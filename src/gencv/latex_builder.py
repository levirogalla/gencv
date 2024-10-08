from dataclasses import dataclass
from enum import Flag
import json
import subprocess
import os
from typing import Literal
from numpy import fromregex
import yaml
from pylatexenc.latexencode import utf8tolatex
from .utils import TemplateYAML
from pydantic import BaseModel
import shutil
import datetime


class ExperiencePlaceHolder(BaseModel):
    """Holds config data for the placeholder in the resume for the experience type."""
    placetype: str
    n: int


def fill_item_template(template: TemplateYAML, data: "ExperienceData") -> str:
    """Fills the item templat specified in the YAML file."""
    bullet_text_kw = r"%text%"
    bullets_kw = r"%bullets%"
    metatext1kw = r"%metatext1%"
    metatext2kw = r"%metatext2%"
    metatext3kw = r"%metatext3%"
    metatext4kw = r"%metatext4%"
    metatext5kw = r"%metatext5%"

    compiled_bullets: list[str] = []
    for bullet in data.bullets:
        text = utf8tolatex(bullet.text)
        for bold_kw in bullet.bold:
            ltx_bold_kw = utf8tolatex(bold_kw)
            text = text.replace(utf8tolatex(
                ltx_bold_kw), rf"\textbf{{{ltx_bold_kw}}}")
        compiled_bullet = template.bullet.replace(
            bullet_text_kw, text)
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
    """Class for loading and filling latex templates."""

    def __init__(self, template_folder_path: str) -> None:
        with open(os.path.join(template_folder_path, "+resume.tex"), "r", encoding="utf-8") as f:
            self.file_template = f.read()

        with open(os.path.join(template_folder_path, "+resume.yaml"), "r", encoding="utf-8") as f:
            self.item_templates: dict[str, dict] = yaml.safe_load(f)

        self.command_stack = self.create_command_stack()
        # tuple is start index and end index of where the place holder is in the string
        self.args: list[tuple[ExperiencePlaceHolder, tuple[int, int]]] = []
        self.compile()

    def create_command_stack(self):
        """Parses latex file to create command stack."""
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
        """Compiles latex template file, extracts placeholder arguments."""
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
        """Fills the template with resume data. Returns new command stack."""
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
    def to_file(output_dir, filename, latex: str | list[str],  output_name=None, compiler: Literal["pdflatex"] = "pdflatex", proxy_dir: str = None, output: Literal["pdf", "tex", "all"] = "all"):
        """
        Converts a LaTeX string into a PDF using the terminal LaTeX compiler.

        Parameters:
            file_path (str): Path where the PDF will be saved.
            latex_string (str): The LaTeX content as a string.
            latex_compiler (str): The LaTeX compiler to use (default is "pdflatex").

        Returns:
            None: The PDF is generated at the specified file path.
        """

        # Extract the base name (without extension) to use for .tex and .pdf
        build_dir: str = None
        proxy_dir_exists = True
        if output_name is None:
            output_name = f"{filename}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        # Ensure the output directory exists
        if output == "pdf":
            build_dir = proxy_dir

            if proxy_dir and not os.path.exists(proxy_dir):
                proxy_dir_exists = False
                os.makedirs(proxy_dir)
            if len(os.listdir(proxy_dir)) != 0:
                raise FileExistsError(
                    "Proxy folder is not empty. Files will not be cleaned up.")
        else:
            build_dir = output_dir
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

        # Create the full path for the .tex file
        tex_file_path = os.path.join(build_dir, filename + ".tex")

        # Write the LaTeX string to a .tex file
        if output == "tex":
            with open(tex_file_path, 'w') as tex_file:
                if isinstance(latex, str):
                    tex_file.write(latex)
                else:
                    tex_file.write("".join(latex))
            return

        with open(tex_file_path, 'w') as tex_file:
            if isinstance(latex, str):
                tex_file.write(latex)
            else:
                tex_file.write("".join(latex))

        # Compile the LaTeX file using the specified LaTeX compiler

        # Call the LaTeX compiler using subprocess
        result = subprocess.run([compiler, '-interaction=nonstopmode', '-synctex=1', filename + ".tex"],
                                cwd=build_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check if the compilation was successful
        if result.returncode == 0:
            print(f"PDF successfully generated at {output_dir}.")
        else:
            print(
                f"Error during PDF generation: {result.stderr.decode('utf-8')}")

        if output == "pdf":
            shutil.copy(os.path.join(build_dir, filename + ".pdf"),
                        os.path.join(output_dir, f"{output_name}.pdf"))
            if not proxy_dir_exists:
                shutil.rmtree(proxy_dir)

    def get_experience_args(self, experience_type: str) -> ExperiencePlaceHolder:
        """Get arguments for an experience."""
        for exp, _ in self.args:
            if exp.placetype == experience_type:
                return exp
        raise ValueError(f"{experience_type} not found in template.")


@dataclass(frozen=True)
class BulletData:
    """Required bullet data for latex template."""
    text: str
    bold: list[str] = None


@dataclass(frozen=True)
class ExperienceData:
    """Required experience data for latex template."""
    id: str
    experience_type: str
    bullets: list[BulletData]
    metatext1: str
    metatext2: str
    metatext3: str
    metatext4: str
    metatext5: str
