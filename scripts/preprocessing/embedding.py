import json
import os
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import warnings
from config.settings import MODEL_NAME, PROCESSED_DATA_PATH, FAISS_INDEX_PATH

warnings.filterwarnings(
    "ignore", message=".*encoder_attention_mask.*", category=FutureWarning
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


def get_document_embeddings(texts):
    """Generate embeddings for a list of texts using BioBERT."""
    if isinstance(texts, str):
        texts = [texts]

    embeddings = []
    batch_size = 32

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
            outputs = model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
            )

        if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            batch_embeddings = outputs.pooler_output.numpy()
        else:
            batch_embeddings = outputs.last_hidden_state[:, 0, :].numpy()

        embeddings.extend(batch_embeddings)

    return np.array(embeddings)


def extract_text_for_embedding(document):
    """Extract relevant text content from a document for embedding."""
    if isinstance(document, dict):
        if "title" in document and "abstract" in document:
            return f"{document.get('title', '')} {document.get('abstract', '')}".strip()

        if "title" in document and "body" in document:
            return f"{document.get('title', '')} {document.get('body', '')}".strip()

        if "text" in document:
            return document["text"]

        text_parts = [
            value
            for key, value in document.items()
            if isinstance(value, str)
            and key not in ["id", "pmid", "source", "source_type"]
        ]
        return " ".join(text_parts)

    return str(document) if document else ""


def load_data(directory):
    """Load all JSON documents from the specified directory."""
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
    """Create and save FAISS index with document metadata."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype("float32"))

    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)

    metadata_path = FAISS_INDEX_PATH.replace(".faiss", "_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)


def generate_embeddings_for_dataset():
    """Main function to generate embeddings for the entire dataset."""
    print("Loading all documents...")
    documents = load_data(PROCESSED_DATA_PATH)

    if not documents:
        print("No documents found")
        return

    texts = []
    valid_documents = []

    print("Extracting text content from documents...")
    for doc in documents:
        text = extract_text_for_embedding(doc)
        if text.strip():  # Only include documents with text content
            texts.append(text)
            valid_documents.append(doc)

    print(f"Processing {len(texts)} documents for embedding...")

    if not texts:
        print("No valid text content found in documents.")
        return

    try:
        print("Generating embeddings with BioBERT...")
        embeddings = get_document_embeddings(texts)
        print(f"Generated embeddings shape: {embeddings.shape}")

        print("Creating and saving FAISS index...")
        create_and_save_faiss_index(embeddings, valid_documents)
        print("Embedding generation completed successfully!")
        print(f"FAISS index saved to: {FAISS_INDEX_PATH}")
        print(
            f"Metadata saved to: {FAISS_INDEX_PATH.replace('.faiss', '_metadata.json')}"
        )

    except Exception as e:
        print(f"Error during embedding generation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    generate_embeddings_for_dataset()
