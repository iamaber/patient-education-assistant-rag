import json
import os
from sentence_transformers import SentenceTransformer
import warnings
from config.settings import MODEL_NAME, PROCESSED_DATA_PATH, FAISS_INDEX_PATH

try:
    import faiss

    # Check if GPU version is available
    if hasattr(faiss, "StandardGpuResources"):
        print("Using faiss-gpu")
    else:
        print("Using faiss-cpu")
except ImportError:
    raise

warnings.filterwarnings("ignore")

model = SentenceTransformer(MODEL_NAME)


def get_document_embeddings(texts):
    if isinstance(texts, str):
        texts = [texts]

    # Use sentence-transformers for simpler embedding generation
    return model.encode(texts, batch_size=32, show_progress_bar=False)


def extract_text_for_embedding(document):
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
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype("float32"))

    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)

    faiss.write_index(index, FAISS_INDEX_PATH)

    metadata_path = FAISS_INDEX_PATH.replace(".faiss", "_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)


def generate_embeddings_for_dataset():
    documents = load_data(PROCESSED_DATA_PATH)

    if not documents:
        return

    texts = []
    valid_documents = []

    for doc in documents:
        text = extract_text_for_embedding(doc)
        if text.strip():
            texts.append(text)
            valid_documents.append(doc)

    if not texts:
        return

    try:
        embeddings = get_document_embeddings(texts)
        create_and_save_faiss_index(embeddings, valid_documents)
    except Exception as e:
        print(f"Error during embedding generation: {e}")


if __name__ == "__main__":
    generate_embeddings_for_dataset()
