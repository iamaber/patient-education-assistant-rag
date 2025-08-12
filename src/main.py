from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.drug_matching.matcher import DrugMatcher
from src.condition_extractor.extractor import ConditionExtractor
from src.guideline_retriever.retriever import GuidelineRetriever
from src.rag_generator.generator import RAGGenerator
from src.guideline_formatter.formatter import to_markdown

app = FastAPI(title="RAG-Med Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
matcher = DrugMatcher()
extractor = ConditionExtractor()
retriever = GuidelineRetriever()
generator = RAGGenerator()


@app.post("/diagnose")
async def diagnose(medicines: list[str]):
    """Step 1: drug → conditions"""
    drugs = [matcher.match(m) for m in medicines]
    flat = [d for sub in drugs for d in sub]
    return {"matched_drugs": [d.dict() for d in flat]}


@app.post("/guidelines")
async def guidelines(conditions: list):
    """Step 2+3+4: conditions → chunks → LLM → formatted"""
    from src.condition_extractor.schemas import Condition as C

    cond_objs = [C(**c) for c in conditions]
    chunks = retriever.retrieve(cond_objs)
    guideline = generator.generate(cond_objs, chunks)
    return {"guideline": guideline.dict(), "markdown": to_markdown(guideline)}
