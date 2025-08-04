import json
import os
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from config.settings import MODEL_NAME, PROCESSED_DATA_PATH, FAISS_INDEX_PATH

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


def get_document_embeddings(texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = []
    batch_size = 32  # Process in batches to manage memory
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]

        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        )

        with torch.no_grad():
            model_output = model(**inputs)
        batch_embeddings = model_output.last_hidden_state[:, 0, :].numpy()
        embeddings.extend(batch_embeddings)
    return np.array(embeddings)


def load_data(directory):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    documents.extend(data)
                else:
                    documents.append(data)
    return documents


def create_and_save_faiss_index(embeddings, documents):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  # L2 distance for similarity search
    index.add(embeddings.astype("float32"))

    # Save FAISS index
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"FAISS index created and saved to {FAISS_INDEX_PATH}")

    # Save document metadata for retrieval
    metadata_path = FAISS_INDEX_PATH.replace(".faiss", "_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"Document metadata saved to {metadata_path}")
