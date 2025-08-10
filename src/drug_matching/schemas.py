from pydantic import BaseModel
from typing import Optional
from src.data_ingestion.schemas import DrugEntry


class MatchResult(BaseModel):
    input_drug: str
    matched_drug: Optional[DrugEntry] = None
    confidence: float
