#!/bin/bash

# Samoey Copilot Start Script
# This script starts the Samoey Copilot application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Samoey Copilot...${NC}"

# Function to print status messages
print_status() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run setup first:"
    echo "  ./scripts/setup.sh"
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please run setup first:"
    echo "  ./scripts/setup.sh"
    exit 1
fi

# Check if required services are running
print_status "Checking required services..."

# Check PostgreSQL
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    print_warning "PostgreSQL is not running. Starting with SQLite..."
    export DATABASE_URL="sqlite:///./data/samoey_copilot.db"
else
    print_success "PostgreSQL is running"
fi

# Check Redis
if ! redis-cli ping >/dev/null 2>&1; then
    print_warning "Redis is not running. Some features may be limited."
else
    print_success "Redis is running"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data/vectorstore data/uploads temp
print_success "Directories created"

# Initialize database if needed
print_status "Checking database status..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    print_success "Database initialized"
else
    print_warning "Alembic configuration not found. Skipping database initialization."
fi

# Parse command line arguments
ENVIRONMENT="development"
HOST="0.0.0.0"
PORT="8000"
RELOAD=true
WORKERS=1

while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            ENVIRONMENT="production"
            RELOAD=false
            WORKERS=4
            shift
            ;;
        --dev|--development)
            ENVIRONMENT="development"
            RELOAD=true
            WORKERS=1
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --no-reload)
            RELOAD=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --prod, --production    Start in production mode"
            echo "  --dev, --development    Start in development mode (default)"
            echo "  --host HOST             Host to bind to (default: 0.0.0.0)"
            echo "  --port PORT             Port to bind to (default: 8000)"
            echo "  --workers WORKERS       Number of worker processes (default: 1)"
            echo "  --no-reload            Disable auto-reload"
            echo "  --help, -h             Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Set environment variables
export ENVIRONMENT="$ENVIRONMENT"
export HOST="$HOST"
export PORT="$PORT"

# Start the application
print_status "Starting Samoey Copilot..."
echo "Environment: $ENVIRONMENT"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Reload: $RELOAD"
echo ""

if [[ "$ENVIRONMENT" == "production" ]]; then
    # Production mode with multiple workers
    print_status "Starting in production mode..."
    exec gunicorn app.main:app \
        --bind "$HOST:$PORT" \
        --workers "$WORKERS" \
        --worker-class uvicorn.workers.UvicornWorker \
        --log-level info \
        --access-logfile - \
        --error-logfile -
else
    # Development mode with auto-reload
    print_status "Starting in development mode..."
    exec uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload "$RELOAD" \
        --log-level info
fi
