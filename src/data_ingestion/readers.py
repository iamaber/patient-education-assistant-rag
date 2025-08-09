import json
from pathlib import Path
from typing import List, Iterable

from schemas import DrugEntry, GuidelineChunk


def load_drug_entries(path: Path) -> List[DrugEntry]:
    """Read medex_data.json and return validated list."""
    with path.open("rt", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        raw = [raw]
    return [DrugEntry(**item) for item in raw]


def iter_guideline_chunks(dir_path: Path) -> Iterable[GuidelineChunk]:
    """
    Stream every JSON file in `processed/*.json`.
    Each file MUST contain a list of dicts with at least:
        {"condition_tag": str, "text": str, ...}
    """
    for file_path in dir_path.glob("*.json"):
        with file_path.open("rt", encoding="utf-8") as fh:
            data = json.load(fh)
        for record in data:
            yield GuidelineChunk(
                condition_tag=record.get("condition_tag", "general"),
                text=record.get("abstract", "") or record.get("text", ""),
                source_file=file_path.name,
                pmid=record.get("pmid"),
                page=record.get("page"),
            )
