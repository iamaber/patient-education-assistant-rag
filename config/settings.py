import os
from dotenv import load_dotenv

load_dotenv()

NCBI_EMAIL = os.getenv("NCBI_EMAIL")
NCBI_API_KEY = os.getenv("NCBI_API_KEY")

PROCESSED_DATA_PATH = "./data/processed"
FAISS_INDEX_PATH = "./faiss_index.faiss"
ES_INDEX_NAME = "medical_documents"
MODEL_NAME = "dmis-lab/biobert-base-cased-v1.1"
