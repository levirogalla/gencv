from typing import Literal, NamedTuple
from dataclasses import dataclass
import torch
import numpy as np

from .utils import TextEncoder, load_yaml


class ResumeBulletItem:
    def __init__(self, text: str) -> None:
        self.__text = text
        self.__embedding = None
        self.__dependants = []
        self.__parent: ResumeBulletItem = None
        self.set_text(text)

    def set_text(self, text: str) -> "ResumeItem":
        self.__text = text
        self.__embedding = TextEncoder.embed(text)
        return self

    def set_parent(self, parent_bullet_item: "ResumeBulletItem"):
        self.__parent = parent_bullet_item

    def get_parent(self):
        return self.__parent

    @property
    def text(self):
        return self.__text

    @property
    def embedding(self):
        return self.__embedding

    def add_dependant(self, text):
        dependant = ResumeBulletItem(text)
        dependant.set_parent(self)
        self.__dependants.append(dependant)
        return dependant


@dataclass(frozen=True)
class GroupData:
    min: int
    max: int


class ResumeExperienceItem:
    def __init__(self,
                 title: str,
                 experience_type: Literal["job", "project"],
                 max_bullets: int,
                 min_bullets: int,
                 bullet_groups: list[GroupData] = None,
                 bullets: list[tuple[ResumeBulletItem, int]] = None,
                 metatext1="",
                 metatext2="",
                 metatext3="",
                 metatext4="",
                 metatext5="",
                 ) -> None:
        self.title = title
        self.experience_type = experience_type
        self.__bullets = [] if bullets is None else bullets
        self.__bullet_groups = [] if bullet_groups is None else bullet_groups
        self.embedding = None
        self.metatext1 = metatext1
        self.metatext2 = metatext2
        self.metatext3 = metatext3
        self.metatext4 = metatext4
        self.metatext5 = metatext5
        self.add_bullets(self.__bullets, self.__bullet_groups)

        self.max_bullets = max_bullets
        self.min_bullets = min_bullets

    def add_bullets(self, bullets: list[tuple[ResumeBulletItem, int]], groups: list[GroupData]):
        self.__bullets = bullets
        self.__bullet_groups = groups
        self.update_embedding()

    def update_embedding(self):
        if len(self.__bullets) == 0:
            return

        mean = torch.stack(
            [bullet[0].embedding for bullet in self.__bullets], dim=0).mean(dim=0)
        self.embedding = mean
        # self.embedding = TextEncoder.embed(
        #     ", ".join([bullet[0].text for bullet in self.__bullets]))

    @ property
    def bullets(self):
        return self.__bullets

    def add_group(self, bullets: list[ResumeBulletItem], group_data: GroupData):
        index = len(self.__bullet_groups)
        self.__bullet_groups.append(group_data)

        for bullet in bullets:
            self.__bullets.append((bullet, index))

        self.update_embedding()

    # def


def compile_yaml(data_file: str):
    compiled_experiences: list[ResumeExperienceItem] = []
    experiences = load_yaml(data_file)

    for data in experiences:
        resume_experience = ResumeExperienceItem(
            title=data.title,
            experience_type=data.type,
            metatext1=data.metatext1,
            metatext2=data.metatext2,
            metatext3=data.metatext3,
            metatext4=data.metatext4,
            metatext5=data.metatext5,
            min_bullets=data.min_points,
            max_bullets=data.max_points
        )
        # print(data.title)
        for bullet_group in data.groups:
            group_data = GroupData(
                min=bullet_group.min,
                max=bullet_group.max
            )
            bullets = []
            for point in bullet_group.points:
                bullet_item = ResumeBulletItem(point.text)
                bullets.append(bullet_item)

                for depenant in point.dependants:
                    dependant_bullet = bullet_item.add_dependant(depenant)
                    bullets.append(dependant_bullet)
            resume_experience.add_group(bullets, group_data)
        #     for b in bullets:
        #         print("     ", b.text)
        # print("-----")
        # for b in resume_experience.bullets:
        #     print("     ", b[0].text)

        # print("\n")

        compiled_experiences.append(resume_experience)
    return compiled_experiences


class BulletPointRef(NamedTuple):
    experience: ResumeExperienceItem
    bullet_point: tuple[ResumeBulletItem, int]
    similarity: float


def bullet_point_similarity(compiled_experiences: list[ResumeExperienceItem], prompt) -> list[BulletPointRef]:
    prompt_embedding = TextEncoder.embed(prompt)
    datas = []
    for exp in compiled_experiences:
        for bullet in exp.bullets:
            datas.append(BulletPointRef(exp, bullet, TextEncoder.cosine_similarity(
                prompt_embedding, bullet[0].embedding)))
    return datas


def project_similarity(bullets: list[BulletPointRef]):
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


class ResumeFormat1ExperienceItem(ResumeExperienceItem):
    # example of reimplementing to hints to where the metatexts are going
    def __init__(self,
                 title: str,
                 experience_type: Literal['job', 'project'],
                 lsubtext: str,
                 ruppertext: str,
                 rlowertext: str,
                 keywords: list[str],
                 bullets: set[tuple[ResumeBulletItem, dict]] = [],
                 ) -> None:
        ...
        # super().__init__(...)
