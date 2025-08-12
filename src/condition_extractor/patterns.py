import json
from pathlib import Path
from typing import Dict, List


def load_icd10_map(path: Path) -> Dict[str, List[str]]:
    """Map keywords → condition names."""
    if not path.exists():
        # fallback mini-map
        return {
            "diabetes": ["Type 2 Diabetes Mellitus"],
            "hypertension": ["Essential Hypertension"],
            "infection": ["Bacterial Infection"],
        }
    return json.loads(path.read_text())


ICD10_MAP = load_icd10_map(
    Path(__file__).parent.parent.parent / "data/mappings/icd10_keywords.json"
)
