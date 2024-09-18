# gencv

import math
from typing import NamedTuple
import numpy as np
import yaml
# from gencv.utils import ExperienceYAML, TextEncoder
from gencv.resumeitems import GroupData, compile_yaml, preprocess_bullets, experience_similarity
from gencv.latex_builder import TexResumeTemplate
from gencv.resumeitems import ResumeExperienceItem, ResumeBulletItem

FILE = "src/data.yaml"
line_chars_lim = 120
max_lines = 30

resume_template = TexResumeTemplate(
    "/Users/levirogalla/Projects/ai-resume-builder/textemplates/jakes_resume")

data = compile_yaml(FILE)

bullets = preprocess_bullets(
    data, """
autocad experience, microsoft office proficiency, knowledge of chemical process equipment, passion for safety, willingness to improve, strong attendance record, compliance with site policies, ability to work independently, presentation skills.
""")

experiences = experience_similarity(bullets)

experiences = sorted(experiences, key=lambda x: x[1], reverse=True)

sorted_experiences: list[ResumeExperienceItem] = {}

for exp_arg, _ in resume_template.args:
    for exp, sim in experiences:
        if exp.experience_type == exp_arg.placetype and len(sorted_experiences) < exp_arg.n:
            sorted_experiences.append(exp)


selected_experiences: dict[ResumeExperienceItem, dict[GroupData, ResumeBulletItem]] = {

}


def calculate_lines(text: str):
    return math.ceil(text / line_chars_lim)


lines = 0
# satisfy min requirement for groups
for exp, bullet, sim in bullets:
    group = exp.groups[bullet[1]]
    if exp not in sorted_experiences:
        continue
    if exp not in selected_experiences:
        selected_experiences[exp] = {}
    if group not in selected_experiences[exp]:
        selected_experiences[exp][group] = []
    if len(selected_experiences[exp][group]) < group.min:
        lines += calculate_lines(bullet[0].text)
        selected_experiences[exp][group].append(bullet)

# satisfy min requirement for experiences
for exp, bullet, sim in bullets:
    group = exp.groups[bullet[1]]
    if exp not in sorted_experiences:
        continue
    if exp not in selected_experiences:
        selected_experiences[exp] = {}
    if group not in selected_experiences[exp]:
        selected_experiences[exp][group] = []
    if sum([len(group) for group in selected_experiences[exp]]) < exp.min_bullets:
        lines += calculate_lines(bullet[0].text)
        selected_experiences[exp][group].append(bullet)

# get additional points above similarity cut off unless lines has been reached
for exp, bullet, sim in bullets:
    group = exp.groups[bullet[1]]
    if exp not in sorted_experiences:
        continue
    if sum([len(group) for group in selected_experiences[exp]]) > exp.max_bullets:
        continue
    if len(selected_experiences[exp][group]) > group.max:
        continue
    if exp not in selected_experiences:
        selected_experiences[exp] = {}
    if group not in selected_experiences[exp]:
        selected_experiences[exp][group] = []
    if lines < max_lines:
        lines += calculate_lines(bullet[0].text)
        selected_experiences[exp][group].append(bullet)


# for p, sim in experiences:
#     print(f"Title: {p.title}, Sim: {sim}")
# print("\n\n")
# bullets = sorted(bullets, key=lambda x: x[2], reverse=True)
# for exp, bullet, sim in bullets:
#     print(f"Title: {bullet[0].text}, Sim: {sim}")


# print(
#     TextEncoder.cosine_similarity(
#         TextEncoder.embed(
#             """
#                 Analyze, design, prototype, develop, test and support - complete software lifecycle in your hands

#             """),
#         TextEncoder.embed(
#             "Experience with Linux, ROS, integrated circuits, PLCs, and communication protocols such as CAN, USB, and HTTP.")

#     )
# )


# for exp in data:
#     sim = TextEncoder.cosine_similarity(exp.embedding, prompt)
#     print(f"Title: {exp.title}, Sim: {sim}")


# for x in exp.bullets:
#     print("    ", x[0].text)

# print("\n\n")


# TexResumeTemplate(
#     "/Users/levirogalla/Projects/ai-resume-builder/textemplates/jakes_resume", experiences=[ResumeExperienceItem(
#         title="the title",
#         experience_type="job",
#         max_bullets=10,
#         min_bullets=3,
#         bullets=[(ResumeBulletItem("test point text, is this working?"), 0)]
#     )]).fill()


def select_point(group,):
