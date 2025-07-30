#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Setting up Pinnacle Copilot Security Environment...${NC}"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Docker Desktop for Mac
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker Desktop...${NC}"
    brew install --cask docker
    
    echo -e "${YELLOW}Starting Docker Desktop...${NC}"
    open -a Docker
    
    # Wait for Docker to start
    echo "Waiting for Docker to start..."
    while ! docker info &>/dev/null; do
        sleep 1
    done
fi

# Install docker-compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installing docker-compose...${NC}"
    brew install docker-compose
fi

# Install other dependencies
echo -e "${YELLOW}Installing other dependencies...${NC}"
brew install python@3.11
brew install redis
brew install prometheus
brew install grafana

# Create Python virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Set up configuration
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Setting up environment configuration...${NC}"
    cp .env.security .env
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs/security
mkdir -p monitoring/grafana/dashboards
mkdir -p data/redis
mkdir -p data/prometheus
mkdir -p data/grafana

# Set proper permissions
echo -e "${YELLOW}Setting proper permissions...${NC}"
chmod -R 755 logs monitoring data
chmod 600 .env*

echo -e "${GREEN}Environment setup complete!${NC}"
echo "You can now run ./start_security.sh to start the security system"
