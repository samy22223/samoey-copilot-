#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Pinnacle Copilot with Docker Compose...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}Docker is not running. Starting Docker...${NC}"
    open -a Docker
    # Wait for Docker to start
    while ! docker info > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo -e "\n${GREEN}✓ Docker is now running${NC}"
fi

# Start the services
docker-compose -f docker-compose.override.yml up -d --build

# Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Check if PostgreSQL is ready
while ! docker-compose -f docker-compose.override.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done

echo -e "\n\n${GREEN}✅ Pinnacle Copilot is now running!${NC}"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                Access Information                    ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║ Dashboard:  http://localhost:8000                    ║"
echo "║ API Docs:   http://localhost:8000/docs               ║"
echo "║ Chat:       http://localhost:8000/chat               ║"
echo "║ PGAdmin:    http://localhost:5050                    ║"
echo "║ Redis UI:   http://localhost:8081                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "${YELLOW}To stop the application, run: docker-compose -f docker-compose.override.yml down${NC}"
echo ""

# Open the dashboard in the default browser
open "http://localhost:8000"
