#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Pinnacle Copilot dependency installation...${NC}"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}❌ Homebrew is not installed. Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo -e "${GREEN}✓ Homebrew installed successfully${NC}"
else
    echo -e "${GREEN}✓ Homebrew is already installed${NC}"
    # Update Homebrew
    echo -e "${YELLOW}Updating Homebrew...${NC}"
    brew update
    echo -e "${GREEN}✓ Homebrew updated${NC}"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python 3 is not installed. Installing Python 3...${NC}"
    brew install python@3.9
    echo -e "${GREEN}✓ Python 3 installed successfully${NC}"
else
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
fi

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
brew install git docker docker-compose etcd redis postgresql

# Start services
echo -e "${YELLOW}Starting services...${NC}"
brew services start redis
brew services start postgresql

# Install Python packages
echo -e "${YELLOW}Installing Python packages...${NC}"
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Install AI/ML dependencies
echo -e "${YELLOW}Installing AI/ML dependencies...${NC}"
pip3 install torch torchvision torchaudio
pip3 install transformers sentence-transformers langchain openai tiktoken

# Install spacy model
echo -e "${YELLOW}Downloading spaCy model...${NC}"
python3 -m spacy download en_core_web_sm

# Download NLTK data
echo -e "${YELLOW}Downloading NLTK data...${NC}"
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env <<EOL
# Pinnacle Copilot Configuration

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pinnacle_copilot

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# etcd Configuration
ETCD_HOST=localhost
ETCD_PORT=2379

# Security
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# AI Configuration
AI_MODEL_NAME=gpt-4  # or any other model you want to use
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000

# Vector Store
VECTOR_STORE_PATH=./data/vector_store

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/pinnacle_copilot.log

# CORS (comma-separated list of origins)
CORS_ORIGINS=*
EOL
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create necessary directories
mkdir -p logs data/vector_store

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
createdb pinnacle_copilot 2>/dev/null || true
alembic upgrade head

echo -e "${GREEN}✨ Installation completed successfully! ✨${NC}"
echo -e "To start the application, run: ${YELLOW}uvicorn pinnacle_copilot:app --reload${NC}"
echo -e "Access the application at: ${YELLOW}http://localhost:8000${NC}"
