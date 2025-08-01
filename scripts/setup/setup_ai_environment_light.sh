#!/bin/bash

# Lightweight AI Development Environment Setup for macOS
# Installs essential AI/ML tools with minimal dependencies

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create AI directory
AI_DIR="$HOME/AI_Projects_Light"
mkdir -p "$AI_DIR"
cd "$AI_DIR"

# Install Homebrew if needed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Update and install Python
brew update
brew install python@3.10

# Create and activate venv
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install core packages with specific versions to avoid conflicts
pip install numpy==1.24.3 pandas==2.0.3 matplotlib==3.7.2 jupyterlab==4.0.5 scikit-learn==1.3.2

# Install PyTorch with CPU-only version to avoid CUDA issues
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Install TensorFlow with compatible version for macOS
pip install tensorflow-macos==2.9.2 tensorflow-metal==0.5.0

# Install AI/ML packages with specific versions
pip install \
    transformers==4.35.2 \
    langchain==0.1.0 \
    llama-index==0.9.3 \
    autogen==0.2.3 \
    crewai==0.1.2

# Install deployment tools
pip install \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    gradio==4.9.0 \
    streamlit==1.27.2

# Create project structure
mkdir -p "$AI_DIR/ai_agent_project/{src,notebooks,data,models}"

# Create requirements.txt
cat > "$AI_DIR/requirements.txt" << 'EOL'
# Core
numpy==1.24.3
pandas==2.0.3
matplotlib==3.7.2
jupyterlab==4.0.5
scikit-learn==1.3.2

# AI/ML
torch==2.1.0
tensorflow-macos==2.9.2
tensorflow-metal==0.5.0

# NLP/Agents
transformers==4.35.2
langchain==0.1.0
llama-index==0.9.3
autogen==0.2.3
crewai==0.1.2

# Deployment
fastapi==0.104.1
uvicorn==0.24.0
gradio==4.9.0
streamlit==1.27.2
EOL

# Create a simple test script
cat > "$AI_DIR/test_install.py" << 'EOL'
import sys
import platform
import numpy as np
import torch
import tensorflow as tf
from transformers import pipeline

def print_section(title):
    print("\n" + "="*50)
    print(f"{title}")
    print("="*50)

print_section("System Information")
print(f"Python: {sys.version}")
print(f"System: {platform.system()} {platform.release()}")
print(f"Processor: {platform.processor()}")

print_section("PyTorch Test")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Random tensor: {torch.rand(2, 3)}")

print_section("TensorFlow Test")
print(f"TensorFlow version: {tf.__version__}")
print(f"GPU available: {len(tf.config.list_physical_devices('GPU')) > 0}")
print(f"Eager execution: {tf.executing_eagerly()}")

print_section("Hugging Face Test"
try:
    classifier = pipeline('sentiment-analysis')
    result = classifier('I love using AI tools!')
    print(f"Sentiment analysis result: {result}")
except Exception as e:
    print(f"Error with Hugging Face: {e}")

print("\nInstallation test completed successfully!")
EOL

echo -e "${GREEN}Setup complete!${NC}"
echo -e "\nTo get started:"
echo "1. cd $AI_DIR"
echo "2. source venv/bin/activate"
echo "3. python test_install.py"
echo "4. jupyter lab"

echo -e "\nInstalled tools:"
echo "- Python 3.10 with venv"
echo "- PyTorch 2.1.0 (CPU)"
echo "- TensorFlow 2.13.0 (Metal)"
echo "- LangChain, LlamaIndex, AutoGen, CrewAI"
echo "- FastAPI, Gradio, Streamlit"
echo -e "\nProject directory: $AI_DIR"
