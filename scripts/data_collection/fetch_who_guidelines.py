import os
import json
import uuid
from scripts.preprocessing.pdf_to_text import process_pdf_to_chunks
from scripts.preprocessing.clean_text import remove_stopwords, lemmatize_text

# define directories
RAW_PDF_DIR = "data/raw/"
PROCESSED_JSON_DIR = "data/processed"

def fetch_who_guidelines():
    if not os.path.exists(RAW_PDF_DIR):
        print(f"ERROR: Directory {RAW_PDF_DIR} does not exist!")
        return
    
    # List all files in directory
    all_files = os.listdir(RAW_PDF_DIR)
    pdf_files = [f for f in all_files if f.endswith(".pdf")]
    
    os.makedirs(PROCESSED_JSON_DIR, exist_ok=True)
    print(f"Created/verified output directory: {os.path.abspath(PROCESSED_JSON_DIR)}")
    
    all_docs = []
    for filename in pdf_files:
        pdf_path = os.path.join(RAW_PDF_DIR, filename)
        try:
            chunks = process_pdf_to_chunks(pdf_path)
            print(f"  Extracted {len(chunks)} chunks from {filename}")
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():  # Only add non-empty chunks
                    # Clean the text
                    cleaned_chunk = remove_stopwords(chunk)
                    cleaned_chunk = lemmatize_text(cleaned_chunk)
                    
                    doc_id = str(uuid.uuid4())
                    all_docs.append({
                        "id": doc_id,
                        "title": filename.replace(".pdf", ""),
                        "body": cleaned_chunk,
                        "source": f"WHO Guidelines: {filename}",
                        "language": "en",
                        "source_type": "Global"
                    })
        except Exception as e:
            print(f"  ERROR processing {filename}: {str(e)}")
            continue
    
    if all_docs:
        output_path = os.path.join(PROCESSED_JSON_DIR, "who_guidelines.json")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_docs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR saving JSON file: {str(e)}")
    else:
        print("No documents to save - no JSON file created")

if __name__ == "__main__":
    fetch_who_guidelines()