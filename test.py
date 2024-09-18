
from math import ceil
import time
from torch import device
from transformers import pipeline

text = """
    Maintained continuous communication with manufacturing and mechanical engineers on manufacturing processes and part
"""
total = 0
for char in text:
    if char == "\n":
        continue
    total += 1

print(total)
print(ceil(120 / total))
