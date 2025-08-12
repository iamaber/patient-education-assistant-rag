from pydantic import BaseModel
from typing import List


class PatientGuideline(BaseModel):
    summary: str
    dos: List[str]
    donts: List[str]
    references: List[str]
