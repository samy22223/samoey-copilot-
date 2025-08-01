#!/bin/bash

# Pinnacle Copilot Setup for macOS 11.7.10
# This script installs all required dependencies and sets up the development environment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Pinnacle Copilot setup for macOS 11.7.10...${NC}"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}❌ Homebrew is not installed. Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo -e "${GREEN}✓ Homebrew installed successfully${NC}"
else
    echo -e "${GREEN}✓ Homebrew is already installed${NC}"
    # Update Homebrew
    echo -e "${YELLOW}Updating Homebrew...${NC}"
    brew update
    echo -e "${GREEN}✓ Homebrew updated${NC}"
fi

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
brew install python@3.10 git postgresql@14 redis

# Start services
echo -e "${YELLOW}Starting services...${NC}"
brew services start postgresql@14
brew services start redis

# Create and activate virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install development dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
pip install -r requirements-dev.txt

# Install additional packages for macOS 11.7.10
echo -e "${YELLOW}Installing additional packages for macOS 11.7.10...${NC}"
pip install "python-jose[cryptography]" "passlib[bcrypt]" python-multipart

# Set environment variables
echo -e "${YELLOW}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from example${NC}
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}
if [ -f "init_db.py" ]; then
    python -c "from backend.db.session import SessionLocal; from backend.db.init_db import init_db; import asyncio; asyncio.run(init_db(SessionLocal()))"
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo -e "${YELLOW}⚠️  init_db.py not found. Database not initialized.${NC}"
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "To activate the virtual environment, run: ${YELLOW}source venv/bin/activate${NC}"
echo -e "To start the development server, run: ${YELLOW}uvicorn backend.main:app --reload${NC}"
