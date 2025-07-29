#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

echo -e "${YELLOW}🚀 Starting Pinnacle Copilot Complete Setup...${NC}"

# 1. Check and install system dependencies
if ! command_exists python3; then
    echo -e "${YELLOW}Installing Python 3...${NC}"
    brew install python
    print_status "Python 3 installed"
fi

if ! command_exists node; then
    echo -e "${YELLOW}Installing Node.js...${NC}"
    brew install node
    print_status "Node.js installed"
fi

if ! command_exists docker; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    brew install --cask docker
    print_status "Docker installed. Please start Docker Desktop and run this script again."
    exit 1
fi

# 2. Create and activate virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
print_status "Virtual environment created and activated"

# 3. Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
print_status "Python dependencies installed"

# 4. Install Node.js dependencies
echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
cd frontend
npm install
cd ..
print_status "Node.js dependencies installed"

# 5. Set up database
echo -e "${YELLOW}Setting up database...${NC}"
python -c "from database import init_db; init_db()"
print_status "Database initialized"

# 6. Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd frontend
npm run build
cd ..
print_status "Frontend built"

# 7. Set up environment variables
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    print_status ".env file created"
fi

# 8. Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d
print_status "Services started"

echo -e "\n${GREEN}✅ Setup completed successfully!${NC}"
echo -e "\nAccess the application at: http://localhost:8000"
echo -e "API Documentation: http://localhost:8000/docs"
echo -e "\nTo stop the application, run: docker-compose down"
