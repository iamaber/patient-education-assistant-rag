from fastapi import FastAPI
from src.drug_matching.matcher import DrugMatcher

app = FastAPI()


@app.post("/match_drug/")
async def match_drug(input_drug: str):
    matcher = DrugMatcher()
    results = matcher.match(input_drug)
    return [r.dict() for r in results]
