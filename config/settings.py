import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.5-flash"

NCBI_EMAIL = os.getenv("NCBI_EMAIL")
NCBI_API_KEY = os.getenv("NCBI_API_KEY")

DRUG_DB_PATH = Path(os.getenv("DRUG_DB_PATH", "data/drug_db/medex_data.json"))
GUIDELINE_DIR = Path(os.getenv("GUIDELINE_DIR", "data/processed"))
VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE_BACKEND", "chroma")  # chroma | faiss
PERSIST_DIRECTORY = Path(os.getenv("PERSIST_DIRECTORY", "chroma_db"))
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "256"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "32"))

CONDITION_MIN_CONFIDENCE = float(os.getenv("MIN_CONDITION_CONF", "0.8"))
ICD10_MAPPING_PATH = Path(
    os.getenv("ICD10_MAPPING_PATH", "data/mappings/icd10_keywords.json")
)


RETRIEVER_TOP_K = int(os.getenv("RETRIEVER_TOP_K", "5"))
RERANK_CROSS_ENCODER = os.getenv(
    "RERANK_CROSS_ENCODER", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


LLM_MODEL_NAME = os.getenv(
    "LLM_MODEL_NAME", "microsoft/DialoGPT-medium"
)  # or meta-llama/Llama-3-8B-Instruct
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "256"))
REPLY_TEMPERATURE = float(os.getenv("REPLY_TEMPERATURE", "0.3"))
USE_4BIT_QUANT = os.getenv("USE_4BIT_QUANT", "true").lower() == "true"
