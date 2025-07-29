#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Start required services
echo -e "${YELLOW}Starting development services...${NC}"
docker-compose -f ../docker-compose.dev.yml up -d db redis

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements-dev.txt

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
export $(grep -v '^#' ../.env | xargs)
alembic upgrade head

# Start the development server
echo -e "\n${GREEN}Starting development server...${NC}"
echo -e "\nAccess the application at: http://localhost:3000"
echo -e "API Documentation: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop the server"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
