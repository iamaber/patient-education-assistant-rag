from fastapi import FastAPI
from src.drug_matching.schemas import MatchResult
from src.drug_matching.matcher import DrugMatcher

app = FastAPI(title="RAG-Med DrugMatcher")
matcher = DrugMatcher()


@app.post("/match_drug", response_model=list[MatchResult])
async def match_drug(query: str):
    return matcher.match(query)
