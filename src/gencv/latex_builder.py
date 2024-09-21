from dataclasses import dataclass
import json
import os
from numpy import fromregex
import yaml
from pylatexenc.latexencode import utf8tolatex
from .utils import TemplateYAML
from pydantic import BaseModel


class ExperiencePlaceHolder(BaseModel):
    placetype: str
    n: int


def fill_item_template(template: TemplateYAML, data: "ExperienceData") -> str:
    bullet_text_kw = r"%text%"
    bullets_kw = r"%bullets%"
    metatext1kw = r"%metatext1%"
    metatext2kw = r"%metatext2%"
    metatext3kw = r"%metatext3%"
    metatext4kw = r"%metatext4%"
    metatext5kw = r"%metatext5%"

    compiled_bullets: list[str] = []
    for bullet in data.bullets:
        compiled_bullet = template.bullet.replace(
            bullet_text_kw, utf8tolatex(bullet.text))
        compiled_bullets.append(compiled_bullet)

    compiled_template = template.template \
        .replace(metatext1kw, utf8tolatex(data.metatext1)) \
        .replace(metatext2kw, utf8tolatex(data.metatext2)) \
        .replace(metatext3kw, utf8tolatex(data.metatext3)) \
        .replace(metatext4kw, utf8tolatex(data.metatext4)) \
        .replace(metatext5kw, utf8tolatex(data.metatext5)) \
        .replace(bullets_kw, "\n".join(compiled_bullets))

    return compiled_template


class TexResumeTemplate:
    def __init__(self, template_folder_path: str) -> None:
        with open(os.path.join(template_folder_path, "+resume.tex"), "r") as f:
            self.file_template = f.read()

        with open(os.path.join(template_folder_path, "+resume.yaml"), "r") as f:
            self.item_templates: dict[str, dict] = yaml.safe_load(f)

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
                arg_end_indx = i + 1
                args.append((ExperiencePlaceHolder(**json.loads(arg.strip())),
                            (arg_start_indx, arg_end_indx)))
        self.args = args

    def fill(self, experiences: list["ExperienceData"]):
        displacement = 0
        filled_latex_stack = self.command_stack.copy()
        for exp_type, template in self.item_templates.items():
            template = TemplateYAML(**template)
            filled_latex_items = []
            for exp in experiences:
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

    @staticmethod
    def to_pdf(self):
        """
        Converts a LaTeX string into a PDF using the terminal LaTeX compiler.

        Parameters:
            file_path (str): Path where the PDF will be saved.
            latex_string (str): The LaTeX content as a string.
            latex_compiler (str): The LaTeX compiler to use (default is "pdflatex").

        Returns:
            None: The PDF is generated at the specified file path.
        """
        # Split the file path into directory and filename
        output_directory, output_filename = os.path.split(file_path)

        # Extract the base name (without extension) to use for .tex and .pdf
        base_name = os.path.splitext(output_filename)[0]

        # Ensure the output directory exists
        if output_directory and not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Create the full path for the .tex file
        tex_file_path = os.path.join(output_directory, base_name + ".tex")

        # Write the LaTeX string to a .tex file
        with open(tex_file_path, 'w') as tex_file:
            tex_file.write(latex_string)

        # Compile the LaTeX file using the specified LaTeX compiler
        try:
            # Call the LaTeX compiler using subprocess
            result = subprocess.run([latex_compiler, tex_file_path],
                                    cwd=output_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if the compilation was successful
            if result.returncode == 0:
                print(f"PDF successfully generated at {file_path}")
            else:
                print(
                    f"Error during PDF generation: {result.stderr.decode('utf-8')}")

        except Exception as e:
            print(f"An error occurred: {e}")


@dataclass(frozen=True)
class BulletData:
    text: str


@dataclass(frozen=True)
class ExperienceData:
    id: str
    experience_type: str
    bullets: list[BulletData]
    metatext1: str
    metatext2: str
    metatext3: str
    metatext4: str
    metatext5: str
