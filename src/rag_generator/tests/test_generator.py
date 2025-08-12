from src.rag_generator.generator import RAGGenerator
from src.condition_extractor.schemas import Condition
from src.guideline_retriever.schemas import RetrievedChunk


def test_generates_output():
    g = RAGGenerator()
    cond = [Condition(name="diabetes", icd10="E11", confidence=0.9)]
    chunks = [
        RetrievedChunk(
            text="Take metformin with meals.", source_file="who.json", score=0.9
        )
    ]
    out = g.generate(cond, chunks)
    assert out.summary
    assert isinstance(out.dos, list)
