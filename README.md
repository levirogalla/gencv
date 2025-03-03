# Resume CLI - Generate Tailored Resumes

## mkres Command

The `mkres` command generates a resume based on a given job description and template.

### Usage

```sh
python main.py mkres <template> <description> [options]
```

The program expects a .gencv directory in ~ (although this is configurable in the .gencvrc which is also expected in ~ but I want to change this to be more XDG compliant). In the .gencv folder can be a list a latex templates and a data.yaml file for the resume data. I have examples of the datafile and latex template in the examples folder. The latex template was based of jakes_resume.

Also make sure the ollama server is running in the background.


### Arguments
- `template` (str): The template file name.
- `desc` (str): Job description or query.

### Options
- `--outname` (str, optional): Output file name.
- `--outdir` (str, optional): Output directory. Default: `~/Downloads`
- `--output` (str, optional): Output format (`pdf`, `tex`, or `all`). Default: `pdf`
- `--as-query` (bool, optional): Treat `desc` as a direct query.
- `--datafile` (str, optional): Path to the resume data YAML file.
- `--template_dir` (str, optional): Directory of LaTeX templates.

### Process Overview
1. **Load Template**: Reads the LaTeX template file.
2. **Compile Data**: Loads structured resume data from a YAML file.
3. **Generate Query**: If `as_query=False`, converts the job description into a query.
4. **Extract Bullet Points**: Filters and ranks resume bullet points based on relevance.
5. **Select Best Experience**: Chooses the most relevant experiences.
6. **Fill Resume Template**: Inserts selected experiences into the template.
7. **Generate Output**: Saves the resume as a PDF or `.tex` file.

### Example
```sh
python main.py mkres my_template "Looking for Python developer with ML experience" --output pdf
```

This generates a `software_engineer.pdf` resume based on the job description.

## YAML Structure Breakdown

### General Elements

- **metatext1**: Placeholder for general metadata (e.g., position, role, etc.).
- **metatext2**: Placeholder for metadata (e.g., company, project name, etc.).
- **metatext3**: Placeholder for date ranges, links, or other context.
- **metatext4**: Placeholder for location, type of work, etc.
- **type**: Defines the type of entry, typically either "job" or "project".
- **order**: Used to control the order of display (lower values appear first).
- **groups**: Contains different groups of accomplishments or responsibilities.

### Groups and Points

Each **group** can have a minimum and maximum number of points associated with it. Points represent specific tasks or accomplishments, with some terms emphasized in bold for clarity.

- **min_points** and **max_points**: These define the range of points that should be listed for this section.
- **points**: Each point contains a **text** field with a description of the accomplishment and a **bold** field for key terms or skills.

---