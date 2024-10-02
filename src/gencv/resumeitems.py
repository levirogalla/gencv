from typing import Literal, NamedTuple
import uuid
from dataclasses import dataclass, field
import torch
import numpy as np
import logging

from gencv.latex_builder import TexResumeTemplate

from .utils import TextEncoder, load_yaml, calculate_lines


class ResumeBulletItem:
    DEFAULT_ORDER = 0

    def __init__(self, text: str, order_: int, order: int = DEFAULT_ORDER, bold: list[str] = None) -> None:
        self.__text = text
        self.__embedding = None
        self.__dependants: list[ResumeBulletItem] = []
        self.__dependency = None
        self.__parent: ResumeBulletItem = None
        self.order_ = order_
        self.order = self.order = order if order is not None else self.DEFAULT_ORDER
        self.bold = bold
        self.set_text(text)

    def __str__(self) -> str:
        return self.__text

    def __repr__(self) -> str:
        return self.__text

    def set_text(self, text: str) -> "ResumeItem":
        self.__text = text
        self.__embedding = TextEncoder.embed(text)
        return self

    def set_parent(self, parent_bullet_item: "ResumeBulletItem"):
        self.__parent = parent_bullet_item

    def get_parent(self):
        return self.__parent

    @property
    def dependants(self):
        return self.__dependants

    def set_dependency(self, dependency: "ResumeBulletItem"):
        self.__dependency = dependency
        if self not in dependency.dependants:
            raise LookupError(
                "Dependency not added to dependant. Add dependency to dependant first.")

    @property
    def text(self):
        return self.__text

    @property
    def embedding(self):
        return self.__embedding

    def add_dependant(self, dependant):
        dependant.set_parent(self)
        self.__dependants.append(dependant)
        dependant.set_dependency(self)
        return dependant

    @property
    def dependency(self):
        return self.__dependency


@dataclass(frozen=True)
class GroupData:
    min: int
    max: int
    order_: int
    id: uuid.UUID = field(init=False, repr=True, default_factory=uuid.uuid4)


class ResumeExperienceItem:
    DEFAULT_ORDER = 0

    def __init__(self,
                 id: str,
                 experience_type: Literal["job", "project"],
                 max_bullets: int,
                 min_bullets: int,
                 order_: int,
                 bullets: list[tuple[ResumeBulletItem, GroupData]] = None,
                 metatext1="",
                 metatext2="",
                 metatext3="",
                 metatext4="",
                 metatext5="",
                 order: int = DEFAULT_ORDER
                 ) -> None:
        self.order_ = order_
        self.id = id
        self.experience_type = experience_type
        self.__bullets = [] if bullets is None else bullets
        self.embedding = None
        self.metatext1 = metatext1
        self.metatext2 = metatext2
        self.metatext3 = metatext3
        self.metatext4 = metatext4
        self.metatext5 = metatext5
        self.add_bullets(self.__bullets)

        self.max_bullets = max_bullets
        self.min_bullets = min_bullets

        self.order = order if order is not None else self.DEFAULT_ORDER

    def __str__(self) -> str:
        return self.metatext1

    def add_bullets(self, bullets: list[tuple[ResumeBulletItem, GroupData]]):
        self.__bullets = bullets
        self.update_embedding()

    def update_embedding(self):
        if len(self.__bullets) == 0:
            return

        mean = torch.stack(
            [bullet[0].embedding for bullet in self.__bullets], dim=0).mean(dim=0)
        self.embedding = mean
        # self.embedding = TextEncoder.embed(
        #     ", ".join([bullet[0].text for bullet in self.__bullets]))

    @property
    def bullets(self):
        return self.__bullets

    def add_group(self, bullets: list[ResumeBulletItem], group_data: GroupData):
        for bullet in bullets:
            self.__bullets.append((bullet, group_data))
        self.update_embedding()


class PreProcessedBullet(NamedTuple):
    experience: ResumeExperienceItem
    bullet_point: tuple[ResumeBulletItem, GroupData]
    similarity: float


class DataSortingKeys(NamedTuple):
    "NameTuple for sorting bullets into the correct order."
    # first sort the experiences by they're fixed order if given,
    experience_order: int
    # then sort by their similarity
    experience_similarity: float
    # the order that the experience shows up in the data file
    experience_order_: int
    # put all bullets from same experience together if they have the same id and similarity
    experience_id: str
    # then sort the bullets by their fixed order
    bullet_order: int
    # then by the bullets similarity if know order is given,
    bullet_similarity: float
    # then by group
    bullet_group_order_: int
    # then by order in group
    bullet_intergroup_order_: int


class ProcessedData(NamedTuple):
    experience: ResumeExperienceItem
    bullet: ResumeBulletItem
    group: GroupData
    sorting_data: DataSortingKeys


class BreaksConstraintError(Exception):
    """Selecting a bullet would break a constraint."""


def process_data(bullets: list[PreProcessedBullet]) -> list[ProcessedData]:
    """Finds how well an experience matches a description using the bullets embedding."""
    #
    exp_bullet_map: dict[str, tuple[list[ResumeBulletItem],
                                    list[GroupData], list[float], ResumeExperienceItem]] = {}
    for experience, (bullet, group), cos_sim in bullets:
        # initialize
        if experience.id not in exp_bullet_map:
            exp_bullet_map[experience.id] = ([], [], [], experience)
        exp_bullet_map[experience.id][0].append(bullet)
        exp_bullet_map[experience.id][1].append(group)
        exp_bullet_map[experience.id][2].append(cos_sim)

    processed_datas: list[ProcessedData] = []

    for _, (exp_bullets, exp_groups, exp_blt_similarities, experience) in exp_bullet_map.items():
        # only calculate the average of first 6 because most resume wont have more than 6 points
        exp_similarity = np.mean(exp_blt_similarities[:5])
        for bullet, group, blt_sim in zip(exp_bullets, exp_groups, exp_blt_similarities):
            sorting_keys = DataSortingKeys(
                # descending
                experience_order=experience.order,
                # ascending order so take inverse
                experience_similarity=1/exp_similarity,
                # order doesn't matter
                experience_id=experience.id,
                # descending order
                experience_order_=experience.order_,
                # descending order
                bullet_order=bullet.order,
                # ascending order so take inverse
                bullet_similarity=1/blt_sim,
                # descending order
                bullet_group_order_=group.order_,
                # descending order
                bullet_intergroup_order_=bullet.order_
            )
            data = ProcessedData(experience, bullet, group, sorting_keys)
            processed_datas.append(data)

    return processed_datas


def compile_yaml(data_file: str):
    compiled_experiences: list[ResumeExperienceItem] = []
    experiences = load_yaml(data_file)

    for exp_i, data in enumerate(experiences):
        resume_experience = ResumeExperienceItem(
            id=data.id,
            order_=exp_i,
            experience_type=data.type,
            metatext1=data.metatext1,
            metatext2=data.metatext2,
            metatext3=data.metatext3,
            metatext4=data.metatext4,
            metatext5=data.metatext5,
            min_bullets=data.min_points,
            max_bullets=data.max_points,
            order=data.order
        )

        for grp_i, bullet_group in enumerate(data.groups):
            group_data = GroupData(
                min=bullet_group.min,
                max=bullet_group.max,
                order_=grp_i,
            )
            bullets = []
            for blt_i, point in enumerate(bullet_group.points):
                bullet_item = ResumeBulletItem(
                    point.text, order_=blt_i, order=point.order, bold=point.bold)
                bullets.append(bullet_item)
                for depenant in point.dependants:
                    depenant_item = ResumeBulletItem(
                        depenant.text, depenant.order, bold=depenant.bold)
                    dependant_bullet = bullet_item.add_dependant(depenant_item)
                    dependant_bullet.order += 1
                    bullets.append(dependant_bullet)

            resume_experience.add_group(bullets, group_data)

        compiled_experiences.append(resume_experience)
    return compiled_experiences


def preprocess_bullets(compiled_experiences: list[ResumeExperienceItem], prompt) -> list[PreProcessedBullet]:
    prompt_embedding = TextEncoder.embed(prompt)
    datas = []
    for exp in compiled_experiences:
        for bullet in exp.bullets:
            datas.append(PreProcessedBullet(
                exp,
                bullet,
                TextEncoder.cosine_similarity(
                    prompt_embedding, bullet[0].embedding),
            ))
    return datas


def experience_similarity(bullets: list[PreProcessedBullet]):
    """Finds how well an experience matches a description using the bullets embedding."""
    exp_map = {}
    for experience, _, cos_sim in bullets:
        if experience in exp_map:
            # only check most similar 6 bullets since in most cases the resume wont have more than 6 bullets
            if len(exp_map[experience]) < 5:
                exp_map[experience].append(cos_sim)
        else:
            exp_map[experience] = [cos_sim]

    experiences: list[tuple[ResumeExperienceItem, float]] = []
    for k, v in exp_map.items():
        experiences.append((k, np.mean(v)))
    return experiences


def select_experiences(experiences: list[ResumeExperienceItem], resume_template: TexResumeTemplate):
    sorted_experiences_counter: dict[str, list[ResumeExperienceItem]] = {}
    sorted_experiences: list[ResumeExperienceItem] = []
    for exp_arg, _ in resume_template.args:
        sorted_experiences_counter[exp_arg.placetype] = 0

    for exp_arg, _ in resume_template.args:
        for exp in experiences:
            if exp.experience_type == exp_arg.placetype and sorted_experiences_counter[exp_arg.placetype] < exp_arg.n:
                sorted_experiences_counter[exp_arg.placetype] += 1
                sorted_experiences.append(exp)

    return sorted_experiences


def select_data(processed_datas: list[ProcessedData], resume_template: TexResumeTemplate, max_lines, line_char_lim) -> list[ProcessedData]:
    logging.debug(
        f"selecting data {processed_datas}, {resume_template}, {max_lines}, {line_char_lim}")
    selected_datas: list[ProcessedData] = []
    selected_datas_set: set[str] = set()
    experience_bullet_selection_counter = {
        d.experience.id: 0 for d in processed_datas}
    group_bullet_selection_counter = {d.group.id: 0 for d in processed_datas}
    total_lines_counter = 0
    total_experience_type_selection_counter = {
        d[0].placetype: set() for d in resume_template.args}

    # sort only based on similarity
    similarity_sorted_data = sorted(processed_datas, key=lambda x: (
        x.sorting_data.experience_id, 1/x.sorting_data.experience_similarity, 1/x.sorting_data.bullet_similarity))

    logging.debug("Sorted data:")
    for d in similarity_sorted_data if logging.getLogger().getEffectiveLevel() <= logging.DEBUG else []:
        log_processed_data(d)

    def check_experience_type_selections(experience: ResumeExperienceItem):
        "Raises error if the type does not exist in the template or if the max amount of experience for that type has been reached."
        if experience.experience_type not in total_experience_type_selection_counter:
            raise BreaksConstraintError(
                f"{experience.experience_type} not in Latex Template.")
        elif experience.id in total_experience_type_selection_counter[experience.experience_type]:
            # this is fine even if the place type has been reached because we are not adding a new experience
            return
        elif len(total_experience_type_selection_counter[experience.experience_type]) >= resume_template.get_experience_args(experience.experience_type).n:
            raise BreaksConstraintError(
                f"Experience limit for type: {experience.experience_type} has been reached."
            )

    def check_experience_max(experience: ResumeExperienceItem):
        """Raises error if experience bullet max is met."""
        if experience.max_bullets is None:
            return
        if experience_bullet_selection_counter[experience.id] >= experience.max_bullets:
            raise BreaksConstraintError(
                f"{experience.id} experience type max bullets reached.")

    def check_experience_min(experience: ResumeExperienceItem):
        """Raises error if experience bullet min is not met."""
        if experience.min_bullets is None:
            return
        if experience_bullet_selection_counter[experience.id] < experience.min_bullets:
            raise BreaksConstraintError(
                f"{experience.id} experience type min bullets not met.")

    def check_group_max(group: GroupData):
        """Raises error if group bullet max is met."""
        if group.max is None:
            return
        if group_bullet_selection_counter[group.id] >= group.max:
            raise BreaksConstraintError(
                f"{group} max bullets reached.")

    def check_group_min(group: GroupData):
        """Raises error if group bullet min is not met."""
        if group.min is None:
            return
        if group_bullet_selection_counter[group.id] < group.min:
            raise BreaksConstraintError(
                f"{group} min bullets not reached.")

    def check_lines_max():
        """Raises error if max lines is met."""
        if total_lines_counter >= max_lines:
            raise BreaksConstraintError("Max lines is met.")

    def add_data_to_selection(data: ProcessedData):
        nonlocal total_lines_counter
        if data.bullet.dependency is not None:
            add_data_to_selection(ProcessedData(
                data.experience, data.bullet.dependency, data.group, data.sorting_data))
        if data.bullet.text not in selected_datas_set:
            selected_datas.append(data)
            selected_datas_set.add(data.bullet.text)
            total_lines_counter += calculate_lines(
                data.bullet.text, line_char_lim)
            experience_bullet_selection_counter[data.experience.id] += 1
            group_bullet_selection_counter[data.group.id] += 1
            total_experience_type_selection_counter[data.experience.experience_type].add(
                data.experience.id)

    # loop through data in order and make sure conditions are not broken
    # first satisfy min requirement for experiences
    logging.debug("\nSatisfying min requirements for experiences: ")
    for data in similarity_sorted_data:
        log_processed_data(data)
        try:
            # could but max lines in a seperate try except cause this function can just return of max lines raises an error. but not really worth it for the perforance boost.
            check_lines_max()
            check_experience_type_selections(data.experience)
            check_experience_max(data.experience)
            check_group_max(data.group)
        except BreaksConstraintError as e:
            logging.debug(
                f"For the above bullet the following exception occured: {e} \nNOT ADDING BULLET.")
            continue
        try:
            check_experience_min(data.experience)
        except BreaksConstraintError as e:
            logging.debug(
                f"For the above bullet the following exception occured: {e} \nADDING BULLET.")
            add_data_to_selection(data)
            continue
        logging.debug("No exception occured, NOT ADDING BULLET.")

    # second satisfy min requirement for group
    logging.debug("\nSatisfying min requirements for groups: ")
    for data in similarity_sorted_data:
        log_processed_data(data)
        try:
            check_lines_max()
            check_experience_type_selections(data.experience)
            check_experience_max(data.experience)
            check_group_max(data.group)
        except BreaksConstraintError as e:
            logging.debug(
                f"For the above bullet the following exception occured: {e} \nNOT ADDING BULLET.")
            continue
        try:
            check_group_min(data.group)
        except BreaksConstraintError as e:
            logging.debug(
                f"For the above bullet the following exception occured: {e} \nADDING BULLET.")
            add_data_to_selection(data)
            continue
        logging.debug("No exception occured, NOT ADDING BULLET.")

    # last keep adding bullets until a constraint is met (probably max lines)
    logging.debug("\nSatisfying min requirements for experiences: ")
    for data in similarity_sorted_data:
        log_processed_data(data)
        try:
            check_lines_max()
            check_experience_type_selections(data.experience)
            check_experience_max(data.experience)
            check_group_max(data.group)
        except BreaksConstraintError as e:
            logging.debug(
                f"For the above bullet the following exception occured: {e} \nNOT ADDING BULLET.")
            continue
        logging.debug(
            f"ADDING BULLET.")
        add_data_to_selection(data)

    return selected_datas


def select_experience_bullets(bullets: list[PreProcessedBullet], selected_experiences: list[ResumeExperienceItem], max_lines, line_char_lim):
    lines = 0

    def add_bullet(group: list, bullet: ResumeBulletItem):
        nonlocal lines
        if bullet.dependency is not None:
            add_bullet(group, bullet.dependency)
        if bullet not in group:
            group.append(bullet)
            lines += calculate_lines(bullet.text, line_char_lim)

    selected_experiences_bullets: dict[ResumeExperienceItem,
                                       dict[GroupData, list[ResumeBulletItem]]] = {}
    bullets = sorted(bullets, key=lambda x: x.similarity, reverse=True)
    # satisfy min requirement for groups
    for exp, bullet, _ in bullets:
        group = exp.groups[bullet[1]]
        if exp not in selected_experiences:
            continue
        if exp not in selected_experiences_bullets:
            selected_experiences_bullets[exp] = {}
        if group not in selected_experiences_bullets[exp]:
            selected_experiences_bullets[exp][group] = []
        if lines > max_lines:
            break
        if group.min is None:
            continue
        if len(selected_experiences_bullets[exp][group]) < group.min:
            add_bullet(selected_experiences_bullets[exp][group], bullet[0])
    # satisfy min requirement for experiences
    for exp, bullet, _ in bullets:
        group = exp.groups[bullet[1]]
        if exp not in selected_experiences:
            continue
        if exp not in selected_experiences_bullets:
            selected_experiences_bullets[exp] = {}
        if group not in selected_experiences_bullets[exp]:
            selected_experiences_bullets[exp][group] = []
        if lines > max_lines:
            break
        if exp.min_bullets is None:
            continue
        if sum(
                len(group) for _, group in selected_experiences_bullets[exp].items()) < exp.min_bullets and len(selected_experiences_bullets[exp][group]) < group.max:
            add_bullet(selected_experiences_bullets[exp][group], bullet[0])

    # get additional points above similarity cut off unless lines has been reached
    for exp, bullet, _ in bullets:
        group = exp.groups[bullet[1]]
        if exp not in selected_experiences:
            continue
        if exp not in selected_experiences_bullets:
            selected_experiences_bullets[exp] = {}
        if group not in selected_experiences_bullets[exp]:
            selected_experiences_bullets[exp][group] = []
        if exp.max_bullets is not None:
            if sum(len(group) for _, group in selected_experiences_bullets[exp].items()) >= exp.max_bullets:
                continue
        if len(selected_experiences_bullets[exp][group]) >= group.max:
            continue
        if lines < max_lines:
            add_bullet(selected_experiences_bullets[exp][group], bullet[0])

    return selected_experiences_bullets


def log_processed_data(data: ProcessedData):
    logging.debug("-------------------------------------")
    logging.debug(f"Bullet: {data.bullet.text}")
    logging.debug(f"Group: {data.group}")
    logging.debug(
        f"Experience: {data.experience.metatext1}, max={data.experience.max_bullets}, min={data.experience.min_bullets}")
    logging.debug(f"Sorting data: {data.sorting_data}")
    logging.debug("-------------------------------------")
