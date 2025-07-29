#!/bin/bash

# Set the terminal title
echo -n -e "\033]0;Pinnacle Copilot\007"

# Change to the script's directory
cd "$(dirname "$0")"

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status messages
status() {
    echo -e "${GREEN}[*]${NC} $1"
}

error() {
    echo -e "${RED}[!] ERROR:${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[!] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    warning "This script is optimized for macOS. Some features may not work on other operating systems."
fi

# Set window title
echo -n -e "\033]0;Pinnacle Copilot\007"

# Clear the screen
clear

# Print header
echo "╔══════════════════════════════════════════════════════╗"
echo "║             Pinnacle Copilot Launcher                ║"
echo "║         AI-Powered System Monitoring & Assistant     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    warning "Docker is not running. Starting Docker..."
    open -a Docker
    # Wait for Docker to start
    while ! docker info >/dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""
    status "Docker is now running"
fi

# Check if required services are running
check_service() {
    local service=$1
    if ! brew services list | grep -q "$service.*started"; then
        warning "$service is not running. Starting $service..."
        brew services start $service
    fi
}

# Start required services
status "Ensuring required services are running..."
check_service "redis"
check_service "postgresql"
check_service "etcd"

# Stop any existing servers
status "Stopping any existing Pinnacle Copilot servers..."
pkill -f "uvicorn pinnacle_copilot:app" 2>/dev/null || true

# Activate virtual environment
if [ ! -d "venv" ]; then
    status "Creating Python virtual environment..."
    python3 -m venv venv
fi

status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .deps_installed
fi

# Initialize database if needed
if [ ! -f ".db_initialized" ]; then
    status "Initializing database..."
    createdb pinnacle_copilot 2>/dev/null || true
    alembic upgrade head
    touch .db_initialized
fi
if [ ! -d "venv" ]; then
    status "Setting up virtual environment..."
    python3 -m venv venv || {
        error "Failed to create virtual environment"
        exit 1
    }
    source venv/bin/activate
    
    # Install core requirements first
    status "Installing core dependencies..."
    pip install --upgrade pip || {
        error "Failed to upgrade pip"
        exit 1
    }
    
    # Install core requirements one by one with better error handling
    for pkg in $(grep -v '^#' requirements.txt | grep -v '^$' | grep -v '^#' | grep -v 'torch\|transformers\|sentence-transformers\|langchain\|chromadb\|openai'); do
        status "Installing $pkg..."
        pip install "$pkg" || {
            warning "Failed to install $pkg - trying with --break-system-packages"
            pip install --break-system-packages "$pkg" || {
                error "Failed to install $pkg"
                exit 1
            }
        }
    done
    
    # Check if user wants to install AI dependencies
    if [[ -z "$NONINTERACTIVE" ]]; then
        read -p "Do you want to install AI/ML dependencies? (y/N) " -n 1 -r
        echo
    else
        # Non-interactive mode - skip AI dependencies
        REPLY="n"
    fi
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        status "Installing AI/ML dependencies (this may take a while)..."
        
        # Install PyTorch first with CPU-only version
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu || {
            warning "Failed to install PyTorch - trying with --break-system-packages"
            pip install --break-system-packages torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu || {
                warning "Failed to install PyTorch. Some AI features may not work."
            }
        }
        
        # Install remaining AI packages
        for pkg in $(grep -v '^#' requirements.txt | grep -v '^$' | grep -E 'torch|transformers|sentence-transformers|langchain|chromadb|openai'); do
            status "Installing $pkg..."
            pip install "$pkg" || {
                warning "Failed to install $pkg - trying with --break-system-packages"
                pip install --break-system-packages "$pkg" || {
                    warning "Failed to install $pkg. Some features may not work."
                }
            }
        done
    else
        warning "Skipping AI/ML dependencies. The app will run in simple mode."
    fi
else
    source venv/bin/activate
fi

# Update core requirements
status "Checking for updates to core dependencies..."
for pkg in $(grep -v '^#' requirements.txt | grep -v '^$' | grep -v '^#' | grep -v 'torch\|transformers\|sentence-transformers\|langchain\|chromadb\|openai'); do
    pip install -U "$pkg" || pip install --break-system-packages -U "$pkg" || {
        warning "Failed to update $pkg"
    }
done

# Check if AI dependencies are installed
if python -c "import torch, transformers" &>/dev/null; then
    status "Checking for updates to AI/ML dependencies..."
    for pkg in $(grep -v '^#' requirements.txt | grep -v '^$' | grep -v '^#' | grep -E 'torch|transformers|sentence-transformers|langchain|chromadb|openai'); do
        pip install -U "$pkg" || pip install --break-system-packages -U "$pkg" || {
            warning "Failed to update $pkg"
        }
    done
fi

# Create necessary directories
mkdir -p templates static/css static/js

# Create necessary directories
status "Setting up directories..."
mkdir -p data/chat_history data/vectorstore config

# Check if config files exist
if [ ! -f "config/custom_instructions.json" ]; then
    status "Creating default configuration..."
    cat > config/custom_instructions.json <<EOL
{
    "system_prompt": "You are Pinnacle Copilot, an advanced AI assistant.",
    "language": "en",
    "tone": "friendly",
    "knowledge_sources": ["system"]
}
EOL
fi

# Start the server
status "Starting Pinnacle Copilot server..."
uvicorn pinnacle_copilot:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Function to clean up on exit
cleanup() {
    status "Shutting down Pinnacle Copilot..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null
    deactivate 2>/dev/null || true
    echo -e "\n${GREEN}✅ Pinnacle Copilot has been stopped.${NC}"
    exit 0
}

# Set up trap to catch exit signals
trap cleanup EXIT

# Wait for the server to start
status "Waiting for the server to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health >/dev/null; then
        break
    fi
    if [ $i -eq 10 ]; then
        error "Failed to start Pinnacle Copilot server. Check the logs for more information."
    fi
    echo -n "."
    sleep 1
done

echo -e "\n${GREEN}✅ Pinnacle Copilot is now running!${NC}"
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
echo "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Open the browser after a short delay
sleep 2
open "http://localhost:8000"

# Show system status
status "System Status:"

# Show running services
echo -e "\n${BLUE}Running Services:${NC}"
ps -ef | grep -v grep | grep -E "uvicorn|redis|postgres|etcd" | awk '{print $8 " " $9 " " $10 " " $11 " " $12}'

# Show resource usage
echo -e "\n${BLUE}Resource Usage:${NC}"
echo -n "CPU: "
top -l 1 | grep "CPU usage" | awk '{print $3 " user, " $5 " sys, " $7 " idle"}'
echo -n "Memory: "
memory_pressure | grep "System-wide memory free percentage" | awk -F: '{print $2}'

# Keep the script running
wait $SERVER_PID
