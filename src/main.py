# gencv

import math
from typing import NamedTuple
import numpy as np
import yaml
from utils.utils import ExperienceYAML, TextEncoder
from utils.resumeitems import compile_yaml, bullet_point_similarity, project_similarity

FILE = "src/data.yaml"

data = compile_yaml(FILE)


bullets = bullet_point_similarity(
    data, """
autocad experience, microsoft office proficiency, knowledge of chemical process equipment, passion for safety, willingness to improve, strong attendance record, compliance with site policies, ability to work independently, presentation skills.
""")
projects = project_similarity(bullets)
projects = sorted(projects, key=lambda x: x[1], reverse=True)
for p, sim in projects:
    print(f"Title: {p.title}, Sim: {sim}")
print("\n\n")
bullets = sorted(bullets, key=lambda x: x[2], reverse=True)
for exp, bullet, sim in bullets:
    print(f"Title: {bullet[0].text}, Sim: {sim}")


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
