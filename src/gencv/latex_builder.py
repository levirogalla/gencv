import json
import os
import yaml
from .resumeitems import ResumeExperienceItem
from .utils import TemplateYAML
from pydantic import BaseModel

project_points = [
    "The first point",
    "The second point"
    "The third point"
]

metatext1 = "meta1"
metatext2 = "meta2"
metatext3 = "meta3"

template = "textemplates/jakes_resume"


class ExperiencePlaceHolder(BaseModel):
    placetype: str
    n: int


def fill_item_template(template: TemplateYAML, data: ResumeExperienceItem) -> str:
    bullet_text_kw = "%text%"
    bullets_kw = r"%bullets%"
    metatext1kw = "%metatext1%"
    metatext2kw = "%metatext2%"
    metatext3kw = "%metatext3%"
    metatext4kw = "%metatext4%"
    metatext5kw = "%metatext5%"

    compiled_bullets: list[str] = []
    for bullet in data.bullets:
        compiled_bullet = template.bullet.replace(
            bullet_text_kw, bullet[0].text)
        compiled_bullets.append(compiled_bullet)

    compiled_template = template.template \
        .replace(metatext1kw, data.metatext1) \
        .replace(metatext2kw, data.metatext2) \
        .replace(metatext3kw, data.metatext3) \
        .replace(metatext4kw, data.metatext4) \
        .replace(metatext5kw, data.metatext5) \
        .replace(bullets_kw, "\n".join(compiled_bullets))

    return compiled_template


class TexResumeTemplate:
    def __init__(self, path: str, experiences: list[ResumeExperienceItem] = None) -> None:
        with open(os.path.join(path, "+resume.tex"), "r") as f:
            self.file_template = f.read()

        with open(os.path.join(path, "+resume.yaml"), "r") as f:
            self.item_templates: dict[str, dict] = yaml.safe_load(f)

        self.experiences: list[ResumeExperienceItem] = experiences
        if self.experiences is None:
            self.experiences = []

        self.command_stack = self.create_command_stack()
        self.args: list[tuple[ExperiencePlaceHolder, tuple[int, int]]] = []
        self.compile()

    def create_command_stack(self):
        chars = ""
        stack = []
        for char in self.file_template:
            if char == " ":
                stack.append(chars.strip())
                stack.append(" ")
                chars = ""
            elif char == "\n":
                stack.append(chars.strip())
                stack.append("\n")
                chars = ""
            else:
                chars += char
        # append last word
        stack.append(chars)
        return stack

    def compile(self):
        commands = enumerate(self.command_stack)
        self.command_stack: list
        print(self.command_stack[586:591])
        args = []
        for i, command in commands:
            if command == r"%GENCV":
                arg = ""
                in_arg = False
                arg_start_indx = i
                while True:
                    i, val = next(commands)
                    if val.startswith("{"):
                        in_arg = True
                    if in_arg:
                        print(val)
                        arg += val
                    if val.endswith("}"):
                        in_arg = False
                        break
                arg_end_indx = i + 1
                args.append((ExperiencePlaceHolder(**json.loads(arg.strip())),
                            (arg_start_indx, arg_end_indx)))
        print(args)
        self.args = args

    def fill(self):
        displacement = 0
        filled_latex_stack = self.command_stack.copy()
        for exp_type, template in self.item_templates.items():
            template = TemplateYAML(**template)
            filled_latex_items = []
            for exp in self.experiences:
                if exp.experience_type == exp_type:
                    filled_latex = fill_item_template(template, exp)
                    filled_latex_items.append(filled_latex)

            for arg in self.args:
                if arg[0].placetype == exp_type:

                    filled_latex_stack = filled_latex_stack[:arg[1][0] - displacement] + \
                        filled_latex_items + \
                        filled_latex_stack[arg[1][1] - displacement:]

                    displacement = len(self.command_stack) - \
                        len(filled_latex_stack)
        return filled_latex_stack

    def to_pdf(self):
        ...
