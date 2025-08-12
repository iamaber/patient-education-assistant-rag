import json
import pandas as pd
from pathlib import Path
from typing import List
from schemas import DrugEntry
import config


def load_raw(path: Path) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_drugs(raw: List[dict]) -> pd.DataFrame:
    validated = [DrugEntry(**row).dict() for row in raw]
    df = pd.DataFrame(validated)
    # De-duplicate on (brand, generic, strength)
    df = df.drop_duplicates(subset=["brand_name", "generic_name", "strength"])
    return df


def run():
    raw = load_raw(config.raw_drug)
    df = clean_drugs(raw)
    config.drug_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.drug_parquet, index=False)
    print(f"Saved {len(df)} clean drug entries.")
