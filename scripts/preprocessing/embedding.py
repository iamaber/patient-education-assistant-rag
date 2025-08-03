import json
import os
from transformers import AutoTokenizer, AutoModel
import torch
from config.settings import MODEL_NAME, PROCESSED_DATA_PATH

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
