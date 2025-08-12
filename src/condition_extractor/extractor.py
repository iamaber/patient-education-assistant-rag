import re
from typing import List, Set
from src.data_ingestion.schemas import DrugEntry
from src.condition_extractor.schemas import Condition
from .patterns import ICD10_MAP, FULL_ICD10_MAP


class ConditionExtractor:
    def extract(self, drug: DrugEntry) -> List[Condition]:
        """Return conditions mentioned in indications (enhanced rule-based)."""
        text = (drug.indications or "").lower()
        if not text.strip():
            return []

        results: List[Condition] = []
        matched_conditions: Set[str] = set()

        # Enhanced pattern matching with multiple patterns per condition
        for pattern, conditions in ICD10_MAP.items():
            # Use word boundary matching for better accuracy
            if re.search(rf"\b{re.escape(pattern)}\b", text):
                # Find the corresponding ICD-10 code from FULL_ICD10_MAP
                icd10_code = None
                for category, (
                    cat_conditions,
                    icd10,
                    patterns,
                ) in FULL_ICD10_MAP.items():
                    if pattern in patterns and any(
                        cond in conditions for cond in cat_conditions
                    ):
                        icd10_code = icd10
                        break

                for cond in conditions:
                    if cond not in matched_conditions:
                        matched_conditions.add(cond)
                        results.append(
                            Condition(
                                name=cond,
                                icd10=icd10_code,
                                confidence=1.0,  # rule-based = 100%
                            )
                        )

        # Additional fuzzy matching for common medical terms
        fuzzy_matches = self._fuzzy_match(text)
        for match in fuzzy_matches:
            if match.name not in matched_conditions:
                matched_conditions.add(match.name)
                results.append(match)

        return results

    def _fuzzy_match(self, text: str) -> List[Condition]:
        """Perform fuzzy matching for common medical variations."""
        fuzzy_results = []

        # Common medical term variations
        fuzzy_patterns = {
            "diabetic": ("Type 2 Diabetes Mellitus", "E11", 0.9),
            "hypertensive": ("Essential Hypertension", "I10", 0.9),
            "infected": ("Bacterial Infection", "A49", 0.8),
            "inflammatory": ("Inflammatory Condition", "M79.3", 0.7),
            "cardiac": ("Cardiac Condition", "I25", 0.7),
            "respiratory": ("Respiratory Condition", "J98", 0.7),
        }

        for pattern, (condition, icd10, confidence) in fuzzy_patterns.items():
            if re.search(rf"\b{re.escape(pattern)}\b", text):
                fuzzy_results.append(
                    Condition(
                        name=condition,
                        icd10=icd10,
                        confidence=confidence,
                    )
                )

        return fuzzy_results
