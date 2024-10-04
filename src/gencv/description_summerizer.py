import ollama


def gen_resume_query(description: str):
    """Create a textual query from description."""
    prompt = """
    Your job is to summerize the qualification listed in a job description into a text search query.
    An example of a query that you would respond with is: 'Embedded systems engineering, 
    mechanical engineering, knowledge of gradient desent, and comfortable with vs code'.
    Respond with ONLY the query, make sure to include ALL technical and soft requirements, do NOT make up any information you do not have. 
    The job description you are summerizing is written below: \n\n
    """
    stream = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt + description}],
        stream=False,
    )

    return stream["message"]["content"]


def extract_keywords(description: str):
    """Extracts keywords from the description."""
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


def bullet_point_review(bullet: str):
    # this doesnt really work that consitently
    prompt = """
    Your job is to critique resume bullet points based on a list of criteria.
    The things you are judging are:
        1. Does it follow the x, y, z format, that is 'Accomplished [x] as measured by [y] by doing [z]'.
        2. Does it display confidence.
        3. Is it consice but also descriptive enough.
        4. Does it qualify the achievements well if possible.
        5. Does it use good action words.
    When you are giving feed back, DO NOT just re-write the entire bullet point, be specific about what is wrong and how that specific part can be re-worded to fix the issue.
    Your response should follow the format outline in quotes below, where [n], and [text] are variables you are filling out:
    '
    [n/10] x, y, z: [text].
    [n/10] confidence: [text].
    [n/10] consice: [text].
    [n/10] qualifications: [text].
    [n/10] action words: [text].
    Overall feedback: [text].
    '
    Try to keep you feedback short and very too the point.
    The job bullet point you are evaluating is written below: \n\n
    """
    stream = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt + bullet}],
        stream=True,
    )
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)


# bullet_point_review(
#     "Led R&D to optimize requirements analysis in systems engineering project requirements using Sentence Transformers, NLP, LLMs, and K-Means clustering, saving 2+ weeks of manual labour for the requirements management team.")
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
