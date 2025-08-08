import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

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
