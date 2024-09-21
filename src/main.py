# gencv

import math
from typing import NamedTuple
import numpy as np
from regex import R
import yaml
from tqdm import tqdm
# from gencv.utils import ExperienceYAML, TextEncoder
from gencv.resumeitems import GroupData, ProcessedBullet, compile_yaml, preprocess_bullets, experience_similarity
from gencv.latex_builder import TexResumeTemplate, ExperienceData, BulletData
from gencv.resumeitems import ResumeExperienceItem, ResumeBulletItem, sort_experiences, select_experience_bullets, select_experiences

FILE = "src/data.yaml"
LINE_CHARS_LIM = 120
MAX_LINES = 30


resume_template = TexResumeTemplate(
    "/Users/levirogalla/Projects/ai-resume-builder/textemplates/jakes_resume")

data = compile_yaml(FILE)

bullets = preprocess_bullets(
    data, """
AutoCAD software proficiency, Microsoft Office tools experience, chemical process equipment knowledge (pumps, valves, motors, controls), passion for safety, strong work ethic, willingness to learn, regular attendance, adherence to site policies & training requirements.
""")

experiences = experience_similarity(bullets)

experiences = select_experiences(experiences, resume_template=resume_template)

selected_experience_bullets = select_experience_bullets(
    bullets=bullets,
    selected_experiences=experiences,
    max_lines=MAX_LINES,
    line_char_lim=LINE_CHARS_LIM,
)


compiled_resume_items = []
for item, group in selected_experience_bullets.items():

    bullet_datas = []
    for _, bullets in group.items():
        for bullet in bullets:
            bullet_datas.append(BulletData(text=bullet.text))
    # filler group data since it isnt need for the latex builder

    resume_item = ExperienceData(
        id=item.id,
        experience_type=item.experience_type,
        metatext1=item.metatext1,
        metatext2=item.metatext2,
        metatext3=item.metatext3,
        metatext4=item.metatext4,
        metatext5=item.metatext5,
        bullets=bullet_datas
    )

    compiled_resume_items.append(resume_item)


sorted_experiences_order: dict[str, int] = {}
for i, (exp) in enumerate(experiences):
    sorted_experiences_order[exp.id] = i
compiled_resume_items = sorted(
    compiled_resume_items, key=lambda x: sorted_experiences_order[x.id])

resume = resume_template.fill(compiled_resume_items)
resume = "".join(resume)
print(resume)
