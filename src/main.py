from fastapi import FastAPI
from src.drug_matching.schemas import MatchResult
from src.drug_matching.matcher import DrugMatcher
from src.condition_extractor.extractor import ConditionExtractor
from src.data_ingestion.schemas import DrugEntry
from src.rag_generator.generator import RAGGenerator
from src.condition_extractor.schemas import Condition
from src.guideline_retriever.retriever import GuidelineRetriever


app = FastAPI(title="RAG-Med DrugMatcher")
matcher = DrugMatcher()


@app.post("/match_drug", response_model=list[MatchResult])
async def match_drug(query: str):
    return matcher.match(query)


extractor = ConditionExtractor()


@app.post("/extract_conditions")
async def extract_conditions(drug: DrugEntry):
    return extractor.extract(drug)


retriever = GuidelineRetriever()
gen = RAGGenerator()


@app.post("/patient_guideline")
async def patient_guideline(conditions: list[Condition]):
    chunks = retriever.retrieve(conditions)
    return gen.generate(conditions, chunks)
