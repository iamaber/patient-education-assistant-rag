from typing import Optional
from pydantic import BaseModel, Field


class DrugEntry(BaseModel):
    brand_name: str
    generic_name: Optional[str] = None
    indications: Optional[str] = None
    dosage_and_administration: Optional[str] = None
    side_effects: Optional[str] = None
    pregnancy_and_lactation: Optional[str] = None
    precautions_and_warnings: Optional[str] = None
    overdose_effects: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    unit_price: Optional[str] = None


class GuidelineChunk(BaseModel):
    condition_tag: str = Field(..., description="e.g. cancer, hypertension")
    text: str
    source_file: str
    pmid: Optional[str] = None
    page: Optional[int] = None
