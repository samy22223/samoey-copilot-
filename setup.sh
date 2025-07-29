#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Pinnacle Copilot setup...${NC}"

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python 3 is required but not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"

# Create and activate virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install development dependencies if requested
if [[ "$1" == "--dev" ]]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    pip install -r requirements-dev.txt
fi

# Install spacy model
echo -e "${YELLOW}Downloading spaCy model...${NC}"
python -m spacy download en_core_web_sm

# Download NLTK data
echo -e "${YELLOW}Downloading NLTK data...${NC}"
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

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
DATABASE_URL=sqlite:///./pinnacle_copilot.db

# Security
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
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
alembic upgrade head

# Install pre-commit hooks if in development mode
if [[ "$1" == "--dev" ]]; then
    echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
    pre-commit install
fi

echo -e "${GREEN}✨ Setup completed successfully! ✨${NC}"
echo -e "To activate the virtual environment, run: ${YELLOW}source venv/bin/activate${NC}"
echo -e "To start the application, run: ${YELLOW}uvicorn pinnacle_copilot:app --reload${NC}"
