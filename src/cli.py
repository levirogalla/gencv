from dataclasses import dataclass
import click
from pydantic import BaseModel
from regex import F
import typer
from gencv.resumeitems import ResumeBulletItem, ResumeExperienceItem, select_data, select_experience_bullets, select_experiences, DataSortingKeys, ProcessedData
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
    MAX_LINES = 31
    if not state.verbose:
        progressbar = typer.progressbar(length=7)
    else:
        progressbar = None

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
    processed_data = process_data(bullets)

    update_console_progress(
        "Selecting best bullet points for experiences...", progressbar)
    selected_data = select_data(
        processed_data, resume_template, MAX_LINES, LINE_CHARS_LIM)
    # sort selected data based on order and similarity
    selected_data = sorted(selected_data, key=lambda x: x.sorting_data)

    exp_id_data_map: dict[str, tuple[ResumeExperienceItem,
                                     list[ResumeBulletItem]]] = {}
    for d in selected_data:
        if d.experience.id not in exp_id_data_map:
            exp_id_data_map[d.experience.id] = (d.experience, [])
        exp_id_data_map[d.experience.id][1].append(d.bullet)

    template_data: list[ExperienceData] = []
    for _, (experience, bullets) in exp_id_data_map.items():
        template_bullets = []
        for b in bullets:
            template_bullets.append(BulletData(b.text, b.bold))
        template_experience = ExperienceData(
            id=experience.id,
            experience_type=experience.experience_type,
            bullets=template_bullets,
            metatext1=experience.metatext1,
            metatext2=experience.metatext2,
            metatext3=experience.metatext3,
            metatext4=experience.metatext4,
            metatext5=experience.metatext5
        )
        template_data.append(template_experience)

    # need to make this data interface into the resume template

    update_console_progress("Filling resume template...", progressbar)
    resume = resume_template.fill(template_data)

    update_console_progress("Generating PDF...", progressbar)
    TexResumeTemplate.to_file(
        outdir, template, resume, output_name=outname, proxy_dir=config.proxy_dir, output=output)


if __name__ == "__main__":
    # for debugging
    # import logging
    # logging.basicConfig(level=logging.DEBUG,
    #                     filename="logging.txt", filemode="w")
    # mkres("levi_resume", "just a job for mechanical engineering and electrical")
    app()
