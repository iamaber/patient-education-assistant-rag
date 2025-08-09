import re
from typing import List

from .schemas import GuidelineChunk


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_chunks(chunks: List[GuidelineChunk]) -> List[GuidelineChunk]:
    return [
        chunk.copy(update={"text": normalize_whitespace(chunk.text)})
        for chunk in chunks
    ]
