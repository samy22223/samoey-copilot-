#!/bin/bash

# AI Development Environment Setup for macOS
# Installs free and open-source AI/ML tools

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create AI directory
AI_DIR="$HOME/AI_Projects"
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

# Install core packages
pip install numpy pandas matplotlib jupyterlab scikit-learn

# Install AI frameworks
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install tensorflow tensorflow-macos tensorflow-metal

# Install NLP and agents
pip install transformers langchain llama-index autogen crewai

# Install deployment tools
pip install fastapi uvicorn gradio streamlit

# Create project structure
mkdir -p "$AI_DIR/ai_agent_project/{src,notebooks,data,models}"

# Create requirements.txt
cat > "$AI_DIR/requirements.txt" << 'EOL'
# Core
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0

# AI/ML
torch>=2.0.0
tensorflow>=2.12.0
scikit-learn>=1.2.0

# NLP/Agents
transformers>=4.30.0
langchain>=0.0.200
llama-index>=0.7.0
autogen>=0.2.0
crewai>=0.1.0

# Deployment
fastapi>=0.95.0
gradio>=3.30.0
streamlit>=1.22.0
EOL

echo -e "${GREEN}Setup complete!${NC}"
echo -e "\nTo get started:"
echo "1. cd $AI_DIR"
echo "2. source venv/bin/activate"
echo "3. jupyter lab"

echo -e "\nInstalled tools:"
echo "- Python 3.10 with venv"
echo "- PyTorch & TensorFlow"
echo "- LangChain & LlamaIndex"
echo "- AutoGen & CrewAI"
echo "- FastAPI, Gradio, Streamlit"
echo -e "\nProject directory: $AI_DIR"
