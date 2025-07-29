#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Verifying Pinnacle Copilot installation...${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service is running
service_running() {
    if command_exists "docker"; then
        docker ps | grep -q "$1"
    else
        brew services list 2>/dev/null | grep -q "$1.*started"
    fi
}

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))' 2>/dev/null)
if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo -e "${RED}❌ Python 3.8 or higher is required (found $PYTHON_VERSION)${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
fi

# Check Docker
if command_exists "docker"; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    
    # Check if Docker is running
    if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker is running${NC}"
    else
        echo -e "${YELLOW}⚠️ Docker is installed but not running. Starting Docker...${NC}"
        open -a Docker
        sleep 10  # Give Docker time to start
    fi
else
    echo -e "${YELLOW}⚠️ Docker is not installed. Some features may not work properly.${NC}"
fi

# Check required services
SERVICES=("postgresql" "redis" "etcd")
for service in "${SERVICES[@]}"; do
    if service_running "$service"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${YELLOW}⚠️ $service is not running. Attempting to start...${NC}"
        if command_exists "docker"; then
            case $service in
                postgresql)
                    docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:13
                    ;;
                redis)
                    docker run --name redis -p 6379:6379 -d redis
                    ;;
                etcd)
                    docker run --name etcd -p 2379:2379 -p 2380:2380 -d quay.io/coreos/etcd:v3.5.0 /usr/local/bin/etcd --advertise-client-urls http://0.0.0.0:2379 --listen-client-urls http://0.0.0.0:2379
                    ;;
            esac
        else
            brew services start $service
        fi
        sleep 2
        if service_running "$service"; then
            echo -e "${GREEN}✓ $service started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start $service${NC}"
        fi
    fi
done

# Check Python virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Python virtual environment exists${NC}
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check Python packages
    REQUIRED_PACKAGES=("fastapi" "uvicorn" "sqlalchemy" "psycopg2-binary" "etcd3" "langchain" "transformers" "sentence-transformers")
    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        if python3 -c "import $pkg" &>/dev/null; then
            version=$(python3 -c "import $pkg; print(getattr($pkg, '__version__', 'unknown'))" 2>/dev/null || echo "installed")
            echo -e "${GREEN}✓ $pkg $version is installed${NC}"
        else
            echo -e "${YELLOW}⚠️ $pkg is not installed. Installing...${NC}"
            pip install $pkg
        fi
    done
    
    # Deactivate virtual environment
    deactivate
else
    echo -e "${YELLOW}⚠️ Python virtual environment not found. Please run the setup script.${NC}"
fi

# Check if the application can start
echo -e "\n${YELLOW}🚀 Testing application startup...${NC}"

# Start the server in the background
source venv/bin/activate
nohup uvicorn pinnacle_copilot:app --host 0.0.0.0 --port 8000 > /tmp/pinnacle_copilot.log 2>&1 &
SERVER_PID=$!

# Wait for the server to start
sleep 5

# Check if the server is running
if curl -s http://localhost:8000/health >/dev/null; then
    echo -e "${GREEN}✓ Application started successfully!${NC}"
    echo -e "\n${GREEN}✅ Pinnacle Copilot is ready to use!${NC}"
    echo -e "\nAccess the application at: ${GREEN}http://localhost:8000${NC}"
    echo -e "API documentation: ${GREEN}http://localhost:8000/docs${NC}"
    
    # Stop the server
    kill $SERVER_PID
else
    echo -e "${RED}❌ Failed to start the application. Check the logs at /tmp/pinnacle_copilot.log${NC}"
    echo -e "${YELLOW}Last 10 lines of the log:${NC}"
    tail -n 10 /tmp/pinnacle_copilot.log
    exit 1
fi

echo -e "\n${GREEN}✨ Verification complete! ✨${NC}"
