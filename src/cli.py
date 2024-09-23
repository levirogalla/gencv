from dataclasses import dataclass
from pydantic import BaseModel
import typer
from gencv.resumeitems import ResumeExperienceItem, ResumeBulletItem, select_experience_bullets, select_experiences
from gencv.latex_builder import TexResumeTemplate, ExperienceData, BulletData
from gencv.resumeitems import GroupData, ProcessedBullet, compile_yaml, preprocess_bullets, experience_similarity
from gencv.description_summerizer import gen_resume_query, extract_keywords
from tqdm import tqdm
import yaml
from regex import R
import numpy as np
from typing import Literal, NamedTuple, Optional
import math
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = typer.Typer()


class Config(BaseModel):
    datafile: Optional[str] = os.path.expanduser("~/.gencv/data.yaml")
    template_dir: Optional[str] = os.path.expanduser("~/.gencv/templates")
    output_dir: Optional[str] = os.path.expanduser("~/Downloads")
    verbose: Optional[bool] = False
    output: Optional[Literal["pdf", "tex", "all"]] = "pdf"
    proxy_dir: Optional[str] = os.path.expanduser("~/.gencv/proxy")


with open(os.path.expanduser("~/.gencvrc"), 'r') as file:
    config_dict = {}
    for line in file:
        # Remove whitespace and newline characters
        line = line.strip()
        # Skip empty lines or comment lines (if any)
        if not line or line.startswith("#"):
            continue
        # Split by '=' to separate the key and value
        key, value = line.split('=', 1)
        # Store in the dictionary
        config_dict[key.strip()] = value.strip()

    config = Config(**config_dict)


@dataclass(frozen=False)
class State:
    verbose: bool = config.verbose


state = State()


@app.callback()
def main(
    verbose: bool = typer.Option(False, help="Enable verbose mode")
):
    """
    Global options for the CLI.
    """
    state.verbose = verbose


def compile_data():
    '''Compile data file to make sure it's formated properly.'''
    ...


def select_projects():
    '''Returns selected projects with selected point for each project to terminal.'''
    ...


@app.command()
def mkres(
        template: str,
        desc: str,
        outdir: str = config.output_dir,
        output: str = "pdf",
        as_query: bool = False,
        datafile: str = config.datafile,
        template_dir: str = config.template_dir):
    '''Generate resume.'''

    # this stuff should be defined on the template
    LINE_CHARS_LIM = 120
    MAX_LINES = 30

    if state.verbose:
        typer.echo("Reading template...")
    resume_template = TexResumeTemplate(os.path.join(template_dir, template))

    if state.verbose:
        typer.echo("Compiling resume data...")
    data = compile_yaml(datafile)

    if state.verbose:
        typer.echo("Generating resume data query from description...")
    query = gen_resume_query(desc) if not as_query else desc
    if state.verbose:
        typer.echo(f"Generated query: '{query}'")

    if state.verbose:
        typer.echo("Querying resume bullet points..")
    bullets = preprocess_bullets(
        data, query)
    if state.verbose:
        typer.echo("Queried the following bullets:")
        for b in sorted(bullets, key=lambda x: x.similarity, reverse=True):
            typer.echo(
                f"    Text: {b.bullet_point[0].text} | Similarity: {b.similarity}")

    if state.verbose:
        typer.echo("Ranking experiences...")
    experiences = experience_similarity(bullets)

    if state.verbose:
        typer.echo("Selecting best experiences...")
    experiences = select_experiences(
        [exp[0] for exp in experiences], resume_template=resume_template)

    if state.verbose:
        typer.echo("Selecting best bullet points for experiences...")
    selected_experience_bullets = select_experience_bullets(
        bullets=bullets,
        selected_experiences=experiences,
        max_lines=MAX_LINES,
        line_char_lim=LINE_CHARS_LIM,
    )

    compiled_resume_items = []
    with typer.progressbar(selected_experience_bullets.items(), label="Preparing resume data") as experiences_iterator:
        for item, group in experiences_iterator:
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

    if state.verbose:
        typer.echo("Organzing resume experiences and bullets...")
    sorted_experiences_order: dict[str, int] = {}
    for i, (exp) in enumerate(experiences):
        sorted_experiences_order[exp.id] = i
    compiled_resume_items = sorted(
        compiled_resume_items, key=lambda x: sorted_experiences_order[x.id])

    if state.verbose:
        typer.echo("Filling resume template...")
    resume = resume_template.fill(compiled_resume_items)

    if state.verbose:
        typer.echo("Generating PDF...")
    TexResumeTemplate.to_file(
        outdir, template, resume, proxy_dir=config.proxy_dir, output=output)


# @app.command()
# def main(name: str, age: int = None, teen: bool = True):
#     """A simple command-line script."""
#     print(f"Hello, {name}!")
#     if age:
#         print(f"You are {age} years old.")
#     print(teen)


if __name__ == "__main__":
    app()
