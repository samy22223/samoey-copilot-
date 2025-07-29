#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f ../.env ]; then
    echo -e "${YELLOW}Loading environment variables...${NC}"
    export $(grep -v '^#' ../.env | xargs)
fi

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p ../logs
mkdir -p ../uploads
mkdir -p ../ssl

# Build and start services
echo -e "\n${YELLOW}Building and starting services...${NC}"
docker-compose -f ../docker-compose.prod.yml build
docker-compose -f ../docker-compose.prod.yml up -d

# Wait for services to be ready
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker-compose -f ../docker-compose.prod.yml exec api alembic upgrade head

# Check if services are running
echo -e "\n${YELLOW}Checking services status...${NC}"
docker-compose -f ../docker-compose.prod.yml ps

echo -e "\n${GREEN}Deployment completed successfully!${NC}"
echo -e "\nAccess the application at: ${FRONTEND_URL:-http://localhost:3000}"
echo -e "API Documentation: ${API_URL:-http://localhost:8000}/docs"
echo -e "\nTo view logs, run: docker-compose -f ../docker-compose.prod.yml logs -f"
