# Use a pipeline as a high-level helper
# Load model directly
import math
from typing import Literal, Optional
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch
from pydantic import BaseModel
import yaml


class TextEncoder:
    '''Helper class for making text embeddings.'''

    # tokenizer = AutoTokenizer.from_pretrained(
    #     "sentence-transformers/all-mpnet-base-v2")
    # model = AutoModel.from_pretrained(
    #     "sentence-transformers/all-mpnet-base-v2")

    model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")

    @classmethod
    def embed(cls, text: str) -> torch.Tensor:
        '''Embeds a text.'''
        # inputs = cls.tokenizer(text, return_tensors="pt")
        # # Forward pass through the model to get the hidden states
        # with torch.no_grad():
        #     outputs = cls.model(**inputs)

        # # Get the embeddings from the last hidden state
        # # shape: [batch_size, sequence_length, hidden_size]
        # last_hidden_state = outputs.last_hidden_state.squeeze()
        # # print(embedding, embedding.shape)

        # embedding = torch.mean(last_hidden_state, dim=0)

        # other api
        embedding = torch.tensor(cls.model.encode(
            "Represent this sentence for searching relevant passages: " + text))
        return embedding

    @staticmethod
    def cosine_similarity(vec1: torch.Tensor, vec2: torch.Tensor):
        '''Compares two embeddings.'''
        sim = torch.dot(vec1, vec2) / \
            (torch.norm(vec1) * torch.norm(vec2))
        return sim


class ExperienceYAML(BaseModel):
    class GroupYAML(BaseModel):
        class PointYAML(BaseModel):
            text: str
            dependants: Optional[list[str]] = []

        max: Optional[int] = None
        min: Optional[int] = None
        points: list[PointYAML]

    # just calling it meta texts so it can be extended to other
    # resume formats, this would be like data, company, keywords, etc.
    # and would depend on the template
    id: str
    metatext1: Optional[str] = ""
    metatext2: Optional[str] = ""
    metatext3: Optional[str] = ""
    metatext4: Optional[str] = ""
    metatext5: Optional[str] = ""

    type: str

    min_points: Optional[int] = None
    max_points: Optional[int] = None
    groups: list[GroupYAML] = None
    order: Optional[int] = 0


class TemplateYAML(BaseModel):
    template: str
    bullet: str


def load_yaml(path: str):
    "Load YAML from a file."
    with open(path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    experiences: list[ExperienceYAML] = []
    for exp_id, data in yaml_data.items():
        experiences.append(ExperienceYAML(**data, id=exp_id))
    return experiences


def calculate_lines(text: str, line_chars_lim: int):
    return math.ceil(len(text) / line_chars_lim)
