
import time
from torch import device
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

ARTICLE = """ New York (CNN)When Liana Barrientos was 23 years old, she got married in Westchester County, New York.
Qualifications:
1 year of active native Android development
Kotlin programming expertise
Understanding and knowledge of Google's material design and industry best practices
JSON, web-based APIs
Good communicator who can express thoughts both verbally and written
Committed to sustainable development, testing and high-quality code

Nice to have:
Personal development of apps
A passion for UI & UX
Experience working in an agile development environment

"""
device("mps")
st = time.time()
print(summarizer(ARTICLE, max_length=300, min_length=30, do_sample=False))
print(time.time()-st)
