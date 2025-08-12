import re
from typing import List
from src.data_ingestion.schemas import DrugEntry
from src.condition_extractor.schemas import Condition
from .patterns import ICD10_MAP


class ConditionExtractor:
    def extract(self, drug: DrugEntry) -> List[Condition]:
        """Return conditions mentioned in indications (rule-based)."""
        text = (drug.indications or "").lower()
        results: List[Condition] = []
        for keyword, conditions in ICD10_MAP.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                for cond in conditions:
                    results.append(
                        Condition(
                            name=cond,
                            icd10=None,  # placeholder
                            confidence=1.0,  # rule-based = 100 %
                        )
                    )
        # Deduplicate by condition name
        seen = set()
        return [c for c in results if not (c.name in seen or seen.add(c.name))]
