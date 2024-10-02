from dataclasses import dataclass
import click
from pydantic import BaseModel
import typer
from gencv.resumeitems import select_experience_bullets, select_experiences, DataSortingKeys, ProcessedData
from gencv.latex_builder import TexResumeTemplate, ExperienceData, BulletData
from gencv.resumeitems import compile_yaml, preprocess_bullets, experience_similarity, process_data
from gencv.description_summerizer import gen_resume_query, extract_keywords
from typing import Literal, NamedTuple, Optional
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


def update_console_progress(message: str, progressbar):
    if state.verbose:
        typer.echo(message)
    else:
        progressbar.update(1)


@app.command()
def mkres(
        template: str,
        desc: str,
        outname: str = None,
        outdir: str = config.output_dir,
        output: str = "pdf",
        as_query: bool = False,
        datafile: str = config.datafile,
        template_dir: str = config.template_dir):
    '''Generate resume.'''

    # this stuff should be defined on the template
    LINE_CHARS_LIM = 120
    MAX_LINES = 50
    if not state.verbose:
        progressbar = typer.progressbar(length=11)

    # load template into program
    resume_template = TexResumeTemplate(os.path.join(template_dir, template))

    update_console_progress("Compiling resume data...", progressbar)
    # load yaml file into program as python objects
    data = compile_yaml(datafile)

    update_console_progress(
        "Generating resume data query from description...", progressbar)
    # generate resume query
    query = gen_resume_query(desc) if not as_query else desc
    if state.verbose:
        typer.echo(f"Generated query: '{query}'")

    update_console_progress("Querying resume bullet points..", progressbar)
    bullets = preprocess_bullets(data, query)

    update_console_progress("Ranking experiences...", progressbar)
    experiences = process_data(bullets)
    experiences = sorted(experiences, key=lambda x: x.sorting_data)
    for ex in experiences:
        print()
        print(ex.bullet.text)
        print(ex.sorting_data)
        print("\n\n")
    # experiences = experience_similarity(bullets)

    update_console_progress(
        "Selecting best bullet points for experiences...", progressbar)
    selected_experience_bullets = select_experience_bullets(
        bullets=bullets,
        selected_experiences=experiences,
        max_lines=MAX_LINES,
        line_char_lim=LINE_CHARS_LIM,
    )

    update_console_progress("Preparing to instert resume data...", progressbar)
    compiled_resume_items: list[ExperienceData] = []
    sorted_bullet_dict: dict[str, int] = {}
    for i, bullet in enumerate(bullets):
        sorted_bullet_dict[bullet.bullet_point[0].text] = (
            bullet.bullet_point[0].order, i)

    for item, group in selected_experience_bullets.items():
        bullet_datas: list[BulletData] = []
        for _, bullets in group.items():
            for bullet in bullets:
                bullet_datas.append(BulletData(
                    text=bullet.text, bold=bullet.bold))
        # filler group data since it isnt need for the latex builder
        bullet_datas = sorted(
            bullet_datas, key=lambda x: sorted_bullet_dict[x.text])

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

    update_console_progress(
        "Organzing resume experiences and bullets...", progressbar)
    sorted_experiences_order: dict[str, int] = {}
    for i, (exp) in enumerate(experiences):
        sorted_experiences_order[exp.id] = (exp.order, i)

    compiled_resume_items = sorted(
        compiled_resume_items, key=lambda x: sorted_experiences_order[x.id])

    update_console_progress("Filling resume template...", progressbar)
    resume = resume_template.fill(compiled_resume_items)

    update_console_progress("Generating PDF...", progressbar)
    TexResumeTemplate.to_file(
        outdir, template, resume, output_name=outname, proxy_dir=config.proxy_dir, output=output)


# @app.command()
# def main(name: str, age: int = None, teen: bool = True):
#     """A simple command-line script."""
#     print(f"Hello, {name}!")
#     if age:
#         print(f"You are {age} years old.")
#     print(teen)


if __name__ == "__main__":
    mkres("levi_resume", "software development for systems engineering.")
    app()
