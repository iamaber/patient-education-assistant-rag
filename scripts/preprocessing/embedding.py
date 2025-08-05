import json
import os
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import warnings
from config.settings import MODEL_NAME, PROCESSED_DATA_PATH, FAISS_INDEX_PATH

# Try to import GPU version of FAISS first, fallback to CPU version
try:
    import faiss
    print("FAISS library loaded successfully")
    # Check if GPU FAISS is available
    if hasattr(faiss, 'StandardGpuResources'):
        print("GPU FAISS support detected")
    else:
        print("CPU FAISS version detected")
except ImportError:
    print("Error: FAISS library not found. Installing...")
    import subprocess
    import sys
    try:
        # Try GPU version first for RunPod environment
        subprocess.check_call([sys.executable, "-m", "pip", "install", "faiss-gpu"])
        print("GPU FAISS installed successfully")
    except subprocess.CalledProcessError:
        print("GPU FAISS installation failed, installing CPU version...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "faiss-cpu"])
    import faiss

warnings.filterwarnings(
    "ignore", message=".*encoder_attention_mask.*", category=FutureWarning
)

# Check for GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

if device.type == "cuda":
    print(f"GPU: {torch.cuda.get_device_name()}")
    print(f"Total GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    print(f"Available GPU Memory: {torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated() / 1e9:.2f} GB")
    
    # Set CUDA memory allocation strategy for better memory management
    torch.cuda.empty_cache()
    # Enable memory optimization for large models
    if hasattr(torch.backends.cuda, 'matmul'):
        torch.backends.cuda.matmul.allow_tf32 = True
    if hasattr(torch.backends.cudnn, 'allow_tf32'):
        torch.backends.cudnn.allow_tf32 = True

print("Loading BioBERT model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model = model.to(device)  # Move model to GPU if available
print("Model loaded successfully")


def check_gpu_memory():
    """Check GPU memory usage if CUDA is available."""
    if device.type == "cuda":
        allocated = torch.cuda.memory_allocated() / 1e9
        cached = torch.cuda.memory_reserved() / 1e9
        print(f"GPU Memory - Allocated: {allocated:.2f} GB, Cached: {cached:.2f} GB")


def get_document_embeddings(texts):
    """Generate embeddings for a list of texts using BioBERT with GPU acceleration."""
    if isinstance(texts, str):
        texts = [texts]

    embeddings = []
    # Optimize batch size based on GPU memory and RunPod environment
    if device.type == "cuda":
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        if gpu_memory_gb >= 24:  # High-end GPU
            batch_size = 128
        elif gpu_memory_gb >= 16:  # Mid-range GPU
            batch_size = 96
        elif gpu_memory_gb >= 8:   # Entry-level GPU
            batch_size = 64
        else:
            batch_size = 32
    else:
        batch_size = 16  # Conservative for CPU

    print(f"Processing {len(texts)} texts with batch size {batch_size} on {device}")
    
    # Enable mixed precision for faster training on modern GPUs
    if device.type == "cuda":
        scaler = torch.cuda.amp.GradScaler()

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]

        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        )

        # Move inputs to GPU if available
        inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            if device.type == "cuda":
                # Use automatic mixed precision for faster inference
                with torch.cuda.amp.autocast():
                    outputs = model(
                        input_ids=inputs["input_ids"],
                        attention_mask=inputs["attention_mask"],
                    )
            else:
                outputs = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                )

        if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            batch_embeddings = outputs.pooler_output.cpu().numpy()  # Move back to CPU for numpy
        else:
            batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()  # Move back to CPU for numpy

        embeddings.extend(batch_embeddings)

        # Clear GPU cache more aggressively to prevent memory issues
        if device.type == "cuda":
            torch.cuda.empty_cache()

        # Progress indicator with more frequent updates
        if (i // batch_size + 1) % 5 == 0 or i + batch_size >= len(texts):
            progress = min(i + batch_size, len(texts))
            percentage = (progress / len(texts)) * 100
            print(f"Processed {progress}/{len(texts)} texts ({percentage:.1f}%)")
            
            # Show memory usage
            if device.type == "cuda":
                memory_used = torch.cuda.memory_allocated() / 1e9
                print(f"  GPU memory used: {memory_used:.2f} GB")

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
    """Create and save FAISS index with document metadata, using GPU if available."""
    dimension = embeddings.shape[1]
    
    # Create FAISS index
    if device.type == "cuda" and hasattr(faiss, 'StandardGpuResources'):
        # Use GPU FAISS if available
        print("Creating GPU-accelerated FAISS index...")
        try:
            res = faiss.StandardGpuResources()
            cpu_index = faiss.IndexFlatL2(dimension)
            gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            gpu_index.add(embeddings.astype("float32"))
            
            # Copy back to CPU for saving
            cpu_index = faiss.index_gpu_to_cpu(gpu_index)
            index = cpu_index
            print("GPU FAISS index created successfully")
        except Exception as e:
            print(f"GPU FAISS failed, falling back to CPU: {e}")
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype("float32"))
    else:
        # Use CPU FAISS
        print("Creating CPU FAISS index...")
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype("float32"))

    # Ensure directory exists
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    
    # Save index
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"FAISS index saved to: {FAISS_INDEX_PATH}")

    # Save metadata
    metadata_path = FAISS_INDEX_PATH.replace(".faiss", "_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"Metadata saved to: {metadata_path}")


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
        if device.type == "cuda":
            check_gpu_memory()
        
        embeddings = get_document_embeddings(texts)
        print(f"Generated embeddings shape: {embeddings.shape}")

        if device.type == "cuda":
            check_gpu_memory()

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
    finally:
        # Clean up GPU memory
        if device.type == "cuda":
            torch.cuda.empty_cache()
            print("GPU memory cleared")


if __name__ == "__main__":
    generate_embeddings_for_dataset()
