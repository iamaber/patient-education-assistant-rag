from typing import List
from rapidfuzz import process, fuzz
from src.data_ingestion.readers import load_drug_entries
from config.settings import DRUG_DB_PATH
from .schemas import MatchResult, DrugEntry


class DrugMatcher:
    def __init__(self) -> None:
        self.drug_db: List[DrugEntry] = load_drug_entries(DRUG_DB_PATH)
        # Pre-compute canonical names for speed
        self._names = [
            (drug.brand_name or "").lower().strip()
            + "|"
            + (drug.generic_name or "").lower().strip()
            for drug in self.drug_db
        ]

    def match(self, query: str, k: int = 5) -> List[MatchResult]:
        query = query.lower().strip()
        matches = process.extract(
            query,
            self._names,
            scorer=fuzz.partial_ratio,
            limit=k,
            score_cutoff=75,  # ≥ 75 % similarity
        )
        return [
            MatchResult(
                input_drug=query,
                matched_drug=self.drug_db[idx],
                confidence=score / 100.0,
            )
            for name, score, idx in matches
        ]
