from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    text: str
    source_file: str
    page: int | None = None
    score: float
