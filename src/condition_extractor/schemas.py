from __future__ import annotations
from pydantic import BaseModel


class Condition(BaseModel):
    name: str
    icd10: str | None = None
    confidence: float
