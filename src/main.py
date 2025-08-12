from fastapi import FastAPI
from src.drug_matching.schemas import MatchResult
from src.drug_matching.matcher import DrugMatcher
from src.condition_extractor.extractor import ConditionExtractor
from src.data_ingestion.schemas import DrugEntry

app = FastAPI(title="RAG-Med DrugMatcher")
matcher = DrugMatcher()


@app.post("/match_drug", response_model=list[MatchResult])
async def match_drug(query: str):
    return matcher.match(query)


extractor = ConditionExtractor()


@app.post("/extract_conditions")
async def extract_conditions(drug: DrugEntry):
    return extractor.extract(drug)
