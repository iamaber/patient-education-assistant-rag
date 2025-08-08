from config.settings import (
    DRUG_DB_PATH,
    GUIDELINE_DIR,
    VECTOR_STORE_BACKEND,
    PERSIST_DIRECTORY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

settings = {
    "drug_db_path": DRUG_DB_PATH,
    "guideline_dir": GUIDELINE_DIR,
    "vector_store_backend": VECTOR_STORE_BACKEND,
    "persist_directory": PERSIST_DIRECTORY,
    "embedding_model": EMBEDDING_MODEL,
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
}
