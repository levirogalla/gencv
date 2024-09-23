import ollama


def gen_resume_query(description: str):
    prompt = """
    Your job is to summerize the qualification listed in a job description into a text search query.
    An example of a query that you would respond with is: 'Embedded systems engineering, 
    mechanical engineering, knowledge of gradient desent, and comfortable with vs code'.
    Respond with ONLY the query and make sure to include ALL technical and soft requirements, the job description you are summerizing is written below: \n\n
    """
    stream = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt + description}],
        stream=False,
    )

    return stream["message"]["content"]


def extract_keywords(description: str):
    prompt = """
    Your job is to summerize the requirements listed in a job description into CSV.
    An example of a query that you would respond with is: 'Python, C++, AutoCAD, SolidWorks, Communication'.
    Respond with ONLY the query, make sure to include ALL requirements, and simplify the list with only the most critical words. 
    The job description you are summerizing is written below: \n\n
    """
    stream = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt + description}],
        stream=False,
    )
    keywords = stream["message"]["content"].lower().replace(
        ".", "").split(", ")

    return keywords


# print(gen_resume_query("""
# Required Knowledge, Skills and Abilities
# Basic knowledge of AUTOCAD or comparable program
# Familiarity with all Microsoft Office tools
# Basic understanding of chemical process equipment (pumps, valves, motors, & controls)
# Passion for safety
# Drive to improve
# Willingness to learn
# Expectations
# Prompt and regular attendance
# Comply with all site policy & training requirements
# Satisfactorily perform duties as assigned
# Participation in site Intern events & activities
# Final presentation of Intern activities & learnings
# All positions are subject to background checks, including police checks and medical
# """))
