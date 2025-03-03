from src.gencv.utils import TextEncoder
import numpy as np


em1 = TextEncoder.embed(
    "embedded systems, chip design, software engineering, software testing, optimization")
em2 = TextEncoder.embed(
    "Led R&D to optimize requirements analysis, saving 2+ weeks of manual labour for the team, by using Sentence Transformers, NLP, LLMs, and K-Means clustering to decompose and sort requirements.")
em3 = TextEncoder.embed("Designed a graph database and API using neo4j and FastAPI to store and manage requirements, tests, interfaces, design documents, and systems, providing streamlined analysis, traceability, and change management capabilities compared to DOORS.")


print(1/TextEncoder.cosine_similarity(em1, em2))
print(1/TextEncoder.cosine_similarity(em1, em3))
