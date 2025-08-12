import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_icd10_map(path: Path) -> Dict[str, Tuple[List[str], str, List[str]]]:
    """Map keywords → (condition names, icd10 code, pattern list)."""
    if not path.exists():
        # fallback mini-map
        return {
            "diabetes": (["Type 2 Diabetes Mellitus"], "E11", ["diabetes", "diabetic"]),
            "hypertension": (
                ["Essential Hypertension"],
                "I10",
                ["hypertension", "high blood pressure"],
            ),
            "infection": (["Bacterial Infection"], "A49", ["infection", "bacterial"]),
        }

    data = json.loads(path.read_text())
    # Transform the loaded data into the expected format
    transformed = {}
    for key, value in data.items():
        transformed[key] = (value["conditions"], value["icd10"], value["patterns"])
    return transformed


# For backward compatibility, create a simple keyword map
def create_pattern_map() -> Dict[str, List[str]]:
    """Create a flattened pattern → conditions mapping for easier searching."""
    full_map = load_icd10_map(
        Path(__file__).parent.parent.parent / "data/mappings/icd10_keywords.json"
    )

    pattern_map = {}
    for category, (conditions, icd10, patterns) in full_map.items():
        for pattern in patterns:
            if pattern not in pattern_map:
                pattern_map[pattern] = []
            pattern_map[pattern].extend(conditions)

    return pattern_map


ICD10_MAP = create_pattern_map()
FULL_ICD10_MAP = load_icd10_map(
    Path(__file__).parent.parent.parent / "data/mappings/icd10_keywords.json"
)
