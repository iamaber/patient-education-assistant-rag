import difflib
from typing import List
from .schemas import MatchResult
from config.settings import DRUG_DB_PATH
from src.data_ingestion.readers import load_drug_entries


class DrugMatcher:
    def __init__(self) -> None:
        self.drug_db = load_drug_entries(DRUG_DB_PATH)

    def match(self, input_drug: str) -> List[MatchResult]:
        results = []
        for drug in self.drug_db:
            confidence = self._calculate_confidence(
                input_drug, drug.brand_name or drug.generic_name
            )
            if confidence > 0.6:  # Threshold
                results.append(
                    MatchResult(
                        input_drug=input_drug, matched_drug=drug, confidence=confidence
                    )
                )
        return results

    @staticmethod
    def _calculate_confidence(input_drug: str, drug_name: str) -> float:
        return difflib.SequenceMatcher(
            None, input_drug.lower(), drug_name.lower()
        ).ratio()


# Example usage
if __name__ == "__main__":
    matcher = DrugMatcher()
    results = matcher.match("Aceclora Tablet")
    for result in results:
        print(result.json())
