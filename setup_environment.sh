#!/bin/bash

# Pinnacle Copilot Environment Setup Script
# This script sets up the development environment for Pinnacle Copilot

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Pinnacle Copilot Environment Setup...${NC}
"

# Check for Python 3.8+
echo -e "${YELLOW}🔍 Checking Python version...${NC}
if ! command -v python3 &> /dev/null; then
    echo "Python 3.8+ is required. Please install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi
echo -e "✓ Python $PYTHON_VERSION is installed\n"

# Check for Node.js and npm
echo -e "${YELLOW}🔍 Checking Node.js and npm...${NC}
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "Node.js and npm are required. Please install them first."
    exit 1
fi
echo -e "✓ Node.js $(node -v) and npm $(npm -v) are installed\n"

# Check for Docker
echo -e "${YELLOW}🔍 Checking Docker...${NC}
if ! command -v docker &> /dev/null; then
    echo "Docker is required. Please install it first."
    exit 1
fi
echo -e "✓ Docker is installed\n"

# Create and activate virtual environment
echo -e "${YELLOW}🛠️  Setting up Python virtual environment...${NC}
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "✓ Virtual environment created\n"
else
    echo -e "✓ Virtual environment already exists\n"
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
echo -e "\n✓ Python dependencies installed\n"

# Install frontend dependencies
echo -e "${YELLOW}🌐 Installing frontend dependencies...${NC}
cd frontend
npm install
cd ..
echo -e "\n✓ Frontend dependencies installed\n"

# Set up environment variables
echo -e "${YELLOW}⚙️  Setting up environment variables...${NC}
if [ ! -f ".env" ]; then
    cat > .env <<EOL
# Pinnacle Copilot Environment Variables

# Backend
DEBUG=True
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pinnacle
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_AI_MODEL=gpt-4
AI_TEMPERATURE=0.7

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Security
CORS_ORIGINS=["http://localhost:3000"]
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60
EOL
    echo -e "✓ Created .env file. Please update the values as needed.\n"
else
    echo -e "✓ .env file already exists\n"
fi

# Initialize database
echo -e "${YELLOW}💾 Initializing database...${NC}
cd backend
alembic upgrade head
cd ..
echo -e "\n✓ Database initialized\n"

# Start Docker services
echo -e "${YELLOW}🐳 Starting Docker services...${NC}
docker-compose up -d
echo -e "\n✓ Docker services started\n"

echo -e "${GREEN}✨ Setup complete!${NC}"
echo -e "\nTo start the development servers, run:"
echo -e "1. Backend: ${YELLOW}cd backend && uvicorn main:app --reload${NC}"
echo -e "2. Frontend: ${YELLOW}cd frontend && npm run dev${NC}"
echo -e "\nAccess the application at ${YELLOW}http://localhost:3000${NC}"
echo -e "API documentation: ${YELLOW}http://localhost:8000/docs${NC}"
