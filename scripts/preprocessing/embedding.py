import json
import os
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

# import warnings
from config.settings import MODEL_NAME, PROCESSED_DATA_PATH, FAISS_INDEX_PATH

# warnings.filterwarnings("ignore", message=".*encoder_attention_mask.*", category=FutureWarning)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


def get_document_embeddings(texts):
    inputs = tokenizer(
        texts, padding=True, truncation=True, return_tensors="pt", max_length=512
    )
    with torch.no_grad():
        model_output = model(**inputs)
    embeddings = model_output.last_hidden_state[:, 0, :].numpy()
    return embeddings


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
    # Create and save FAISS index with document metadata.
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  # L2 distance for similarity search
    index.add(embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"FAISS index created and saved to {FAISS_INDEX_PATH}")
