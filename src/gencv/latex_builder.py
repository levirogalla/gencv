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


class TexResumeTemplate:
    def __init__(self, path: str) -> None:
        with open(os.path.join(path, "+resume.tex"), "r") as f:
            self.file_template = f.read()

        with open(os.path.join(path, "+resume.yaml"), "r") as f:
            self.item_templates: dict[str, dict] = yaml.safe_load(f)

        self.experiences: list[ResumeExperienceItem] = []
        self.command_stack = self.create_command_stack()
        self.args = []
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
                        arg += val
                    if val.endswith("}"):
                        in_arg = False
                        break
                arg_end_indx = i
                args.append((ExperiencePlaceHolder(**json.loads(arg.strip())),
                            (arg_start_indx, arg_end_indx)))
        self.args = args

    def fill(self):
        for exp_type, template in self.item_templates.items():
            template = TemplateYAML(**template)
            for exp in self.experiences:
                if exp.experience_type == exp_type:
