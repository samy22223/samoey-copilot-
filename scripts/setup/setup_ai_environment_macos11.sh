#!/bin/bash

# AI Development Environment Setup for macOS 11.7.10
# Installs essential AI/ML tools with proper dependency handling

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create AI directory
AI_DIR="$HOME/AI_Development"
mkdir -p "$AI_DIR"
cd "$AI_DIR"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Install Homebrew if needed
if ! command -v brew &> /dev/null; then
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Update and install system dependencies
print_status "Updating system packages..."
brew update
brew upgrade

# Install Python 3.10 with proper linking
print_status "Installing Python 3.10..."
brew install python@3.10
brew link --force python@3.10

export PATH="/usr/local/opt/python@3.10/bin:$PATH"

# Create and activate venv
print_status "Creating Python virtual environment..."
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install core packages with specific versions
print_status "Installing core packages..."
pip install \
    numpy==1.23.5 \
    pandas==1.5.3 \
    matplotlib==3.6.3 \
    jupyterlab==3.6.3 \
    scikit-learn==1.1.3 \
    ipykernel==6.22.0

# Install PyTorch with CPU support for macOS 11
print_status "Installing PyTorch..."
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu

# Install TensorFlow for macOS 11
print_status "Installing TensorFlow..."
pip install tensorflow-macos==2.9.2 tensorflow-metal==0.5.0

# Install AI/ML packages with compatible versions one by one
print_status "Installing AI/ML packages..."

# Function to install a package with error handling
install_package() {
    local package=$1
    local version=$2
    print_status "Installing $package==$version..."
    if pip install --no-deps "$package==$version"; then
        print_status "Successfully installed $package==$version"
    else
        print_status "Warning: Failed to install $package==$version"
        return 1
    fi
}

# Install core AI/ML packages one by one
print_status "Installing core AI/ML packages..."
install_package "transformers" "4.30.2" || true

# Skip langchain as it may require pyarrow
# install_package "langchain" "0.0.235" || true

# Install additional AI tools
print_status "Installing additional AI tools..."
install_package "autogen" "0.9.5" || true
install_package "crewai" "0.1.2" || true
install_package "openai" "0.27.8" || true
install_package "tiktoken" "0.4.0" || true

# Install deployment tools
print_status "Installing deployment tools..."
pip install \
    fastapi==0.95.2 \
    uvicorn==0.22.0 \
    gradio==3.34.0 \
    streamlit==1.22.0

# Create project structure
print_status "Setting up project structure..."
mkdir -p "$AI_DIR/ai_agent_project/{src,notebooks,data,models}"

# Create requirements.txt
cat > "$AI_DIR/requirements.txt" << 'EOL'
# Core
numpy==1.23.5
pandas==1.5.3
matplotlib==3.6.3
jupyterlab==3.6.3
scikit-learn==1.1.3
ipykernel==6.22.0

# AI/ML
torch==2.0.1
torchvision==0.15.2
torchaudio==2.0.2
tensorflow-macos==2.9.2
tensorflow-metal==0.5.0

# NLP/Agents
transformers==4.30.2
langchain==0.0.235
autogen==0.9.5
crewai==0.1.2
# sentence-transformers==2.2.2  # Requires pyarrow which has build issues
openai==0.27.8
tiktoken==0.4.0

# Deployment
fastapi==0.95.2
uvicorn==0.22.0
gradio==3.34.0
streamlit==1.22.0
EOL

# Create a test script
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

print_section("Hugging Face Test")
try:
    classifier = pipeline('sentiment-analysis')
    result = classifier('I love using AI tools!')
    print(f"Sentiment analysis result: {result}")
except Exception as e:
    print(f"Error with Hugging Face: {e}")

print("\nInstallation test completed successfully!")
EOL

# Create a simple Streamlit demo
cat > "$AI_DIR/ai_demo.py" << 'EOL'
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("AI Development Environment Demo")

st.header("Sample AI Application")
st.write("This is a simple demo showing that your AI environment is working correctly.")

# Interactive plot
st.subheader("Interactive Plot")
x = np.linspace(0, 10, 100)
y = np.sin(x)

fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_title("Sine Wave")
ax.set_xlabel("X")
ax.set_ylabel("sin(X)")
st.pyplot(fig)

# Simple text input
text = st.text_input("Enter some text:")
if text:
    st.write(f"You entered: {text}")
EOL

# Create a Jupyter kernel for the virtual environment
python -m ipykernel install --user --name=ai_env --display-name="Python (AI Env)"

print -e "\n${GREEN}Setup complete!${NC}"
echo -e "\nTo get started:"
echo "1. cd $AI_DIR"
echo "2. source venv/bin/activate"
echo "3. Test the installation: python test_install.py"
echo "4. Launch Jupyter Lab: jupyter lab"
echo "5. Try the Streamlit demo: streamlit run ai_demo.py"

echo -e "\n${BLUE}Installed tools:${NC}"
echo "- Python 3.10 with venv"
echo "- PyTorch 2.0.1 (CPU)"
echo "- TensorFlow 2.10.0 (Metal)"
echo "- LangChain, LlamaIndex, AutoGen, CrewAI"
echo "- FastAPI, Gradio, Streamlit"
echo -e "\n${BLUE}Project directory:${NC} $AI_DIR"
echo -e "${BLUE}Virtual environment:${NC} $AI_DIR/venv"

# Save the activation command to a file
cat > "$AI_DIR/activate_env.sh" << 'EOL'
#!/bin/bash
source "$(dirname "$0")/venv/bin/activate"
"$@"
EOL
chmod +x "$AI_DIR/activate_env.sh"

echo -e "\n${GREEN}Run './activate_env.sh' to activate the environment in new terminal sessions.${NC}"
