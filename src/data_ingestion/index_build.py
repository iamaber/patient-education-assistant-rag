import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pandas as pd
from config import config


def build_index(parquet_path: Path, index_path: Path, text_col: str = "text"):
    df = pd.read_parquet(parquet_path)
    texts = df[text_col].tolist()

    model = SentenceTransformer(config.embedding_model, device=config.device)
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)  # cosine similarity
    index.add(embeddings.astype("float32"))

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    df.drop(columns=[text_col]).to_parquet(index_path.with_suffix(".meta.parquet"))
    print(f"Indexed {len(texts)} entries at {index_path}")


if __name__ == "__main__":
    build_index(config.drug_parquet, config.drug_index, text_col="indications")
    build_index(config.guidelines_parquet, config.guideline_index, text_col="text")
