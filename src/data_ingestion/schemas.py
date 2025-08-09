from typing import Optional
from pydantic import BaseModel, Field


class DrugEntry(BaseModel):
    brand_name: str
    generic_name: str
    indications: str
    dosage_and_administration: Optional[str] = None
    side_effects: str
    pregnancy_and_lactation: Optional[str] = None
    precautions_and_warnings: str
    overdose_effects: str
    dosage_form: Optional[str]
    strength: Optional[str]
    unit_price: Optional[str]


class GuidelineChunk(BaseModel):
    condition_tag: str = Field(..., description="e.g. cancer, hypertension")
    text: str
    source_file: str
    pmid: Optional[str] = None
    page: Optional[int] = None
