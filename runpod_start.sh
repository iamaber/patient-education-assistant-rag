#!/bin/bash

# RunPod PyTorch 2.8.0 Template Setup Script
# For Patient Education Assistant RAG
# Template: runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

echo "🏥 Patient Education Assistant RAG - RunPod PyTorch Setup"
echo "========================================================="
echo "📦 Using RunPod PyTorch 2.8.0 Template"
echo ""

# Set environment variables
export PYTHONPATH="/workspace:$PYTHONPATH"
export DEBIAN_FRONTEND=noninteractive

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting setup process..."

# Navigate to workspace (RunPod template uses /workspace)
cd /workspace

# Clone the repository if it doesn't exist
if [ ! -d "patient-education-assistant-rag" ]; then
    log "Cloning repository..."
    git clone https://github.com/iamaber/patient-education-assistant-rag.git
    cd patient-education-assistant-rag
else
    log "Repository already exists, updating..."
    cd patient-education-assistant-rag
    git pull origin main
fi

# Install Python dependencies (PyTorch already installed in template)
log "Installing additional Python dependencies..."
if [ -f "requirements.txt" ]; then
    # Install without PyTorch since it's already in the template
    grep -v "torch" requirements.txt > temp_requirements.txt
    pip install -r temp_requirements.txt
    rm temp_requirements.txt
else
    log "Warning: requirements.txt not found"
fi

# Install additional packages that might not be in requirements
log "Installing core packages..."
pip install faiss-cpu sentence-transformers transformers fastapi gradio uvicorn beautifulsoup4 elasticsearch pandas numpy requests

# Install additional packages that might not be in requirements
log "Installing core packages..."
pip install faiss-cpu sentence-transformers transformers fastapi gradio uvicorn beautifulsoup4 elasticsearch pandas numpy requests

# Download spaCy model
log "Downloading spaCy model..."
python -m spacy download en_core_web_sm || log "Warning: Failed to download spaCy model"

# Create necessary directories
log "Creating necessary directories..."
mkdir -p data/processed data/raw faiss_indices logs

# Set permissions for Python scripts
chmod +x scripts/preprocessing/*.py 2>/dev/null || true
chmod +x scripts/data_collection/*.py 2>/dev/null || true

# Display system information
log "System Information:"
log "  Python version: $(python --version)"
log "  PyTorch version: $(python -c 'import torch; print(torch.__version__)')"
log "  CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')"
log "  GPU count: $(python -c 'import torch; print(torch.cuda.device_count() if torch.cuda.is_available() else 0)')"

# Check if data exists
if [ ! -d "data/processed" ] || [ -z "$(ls -A data/processed 2>/dev/null)" ]; then
    log "No processed data found. You can run data collection scripts:"
    log "  python scripts/data_collection/fetch_pubmed.py"
    log "  python scripts/data_collection/scrap_medex.py" 
    log "  python scripts/preprocessing/embedding.py"
fi

log ""
log "🏥 Patient Education Assistant RAG - Ready for Development"
log "=========================================================="
log ""
log "� RunPod PyTorch 2.8.0 Template Active"
log "�📊 Main web application not yet implemented"
log ""
log "🔧 Available data processing scripts:"
log "  python scripts/preprocessing/embedding.py          # Generate embeddings"
log "  python scripts/data_collection/fetch_pubmed.py     # Fetch PubMed data"
log "  python scripts/data_collection/scrap_medex.py      # Scrape Medex data"
log "  python main.py                                      # Show available commands"
log ""
log "💻 To run scripts:"
log "  cd /workspace/patient-education-assistant-rag"
log "  python scripts/preprocessing/embedding.py"
log ""
log "📂 Data directories:"
log "  /workspace/patient-education-assistant-rag/data/processed/"
log "  /workspace/patient-education-assistant-rag/faiss_indices/"
log ""
log "🖥️  GPU Info:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits | while read line; do
        log "  GPU: $line"
    done
else
    log "  nvidia-smi not available"
fi
log ""
log "✅ Setup complete! Container ready for development."
log "   Use the terminal to run your scripts interactively."

# Keep container running for interactive development
tail -f /dev/null
