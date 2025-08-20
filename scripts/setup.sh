#!/bin/bash

# Unified Samoey Copilot Setup Script
# This script sets up the complete development environment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Samoey Copilot setup...${NC}"

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

# Check if Python 3.8+ is installed
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi
print_success "Python $PYTHON_VERSION is installed"

# Check for Node.js and npm (for frontend)
print_status "Checking Node.js and npm..."
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    print_warning "Node.js and npm are not installed. Frontend setup will be skipped."
    SKIP_FRONTEND=true
else
    print_success "Node.js $(node -v) and npm $(npm -v) are installed"
    SKIP_FRONTEND=false
fi

# Check for Docker (optional)
print_status "Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed. Docker services will be skipped."
    SKIP_DOCKER=true
else
    print_success "Docker is installed"
    SKIP_DOCKER=false
fi

# Create and activate virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip
print_success "Pip upgraded"

# Install dependencies based on environment
if [[ "$1" == "--prod" ]]; then
    print_status "Installing production dependencies..."
    pip install -r requirements-prod.txt
    ENV_TYPE="production"
elif [[ "$1" == "--dev" ]]; then
    print_status "Installing development dependencies..."
    pip install -r requirements-dev.txt
    ENV_TYPE="development"
else
    print_status "Installing core dependencies..."
    pip install -r requirements.txt
    ENV_TYPE="development"
fi
print_success "Dependencies installed"

# Install AI/ML dependencies
print_status "Installing AI/ML dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers langchain chromadb
print_success "AI/ML dependencies installed"

# Install spaCy model
print_status "Downloading spaCy model..."
python -m spacy download en_core_web_sm
print_success "spaCy model downloaded"

# Download NLTK data
print_status "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
print_success "NLTK data downloaded"

# Setup frontend if not skipped
if [ "$SKIP_FRONTEND" = false ]; then
    print_status "Setting up frontend..."
    if [ -d "frontend" ]; then
        cd frontend
        npm install
        cd ..
        print_success "Frontend dependencies installed"
    else
        print_warning "Frontend directory not found. Skipping frontend setup."
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env <<EOL
# Samoey Copilot Configuration

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql://samoey:samoey@localhost:5432/samoey_copilot
DATABASE_POOL_SIZE=20

# Security
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# AI Configuration
AI_MODEL=gpt-4
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
OPENAI_API_KEY=your_openai_api_key_here

# Vector Store
VECTOR_STORE_PATH=./data/vector_store

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/samoey_copilot.log

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Environment
ENVIRONMENT=$ENV_TYPE
EOL
    print_success ".env file created"
else
    print_success ".env file already exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data/vectorstore data/uploads temp
print_success "Directories created"

# Initialize database
print_status "Initializing database..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    print_success "Database initialized"
else
    print_warning "Alembic configuration not found. Skipping database initialization."
fi

# Start Docker services if not skipped
if [ "$SKIP_DOCKER" = false ]; then
    print_status "Starting Docker services..."
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        print_success "Docker services started"
    else
        print_warning "Docker Compose file not found. Skipping Docker services."
    fi
fi

# Install pre-commit hooks if in development mode
if [[ "$1" == "--dev" ]]; then
    print_status "Setting up pre-commit hooks..."
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "Pre-commit not installed. Skipping pre-commit hooks."
    fi
fi

# Create startup scripts
print_status "Creating startup scripts..."
cat > start.sh << 'EOF'
#!/bin/bash
# Samoey Copilot Startup Script

echo "🚀 Starting Samoey Copilot..."

# Activate virtual environment
source venv/bin/activate

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF

chmod +x start.sh
print_success "Startup script created"

echo -e "${GREEN}✨ Setup completed successfully! ✨${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Update .env file with your configuration"
echo -e "3. Start the application: ${YELLOW}./start.sh${NC}"
echo
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "4. For frontend: ${YELLOW}cd frontend && npm run dev${NC}"
fi
echo
echo -e "${BLUE}Access points:${NC}"
echo -e "- Application: ${YELLOW}http://localhost:8000${NC}"
echo -e "- API Documentation: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "- Frontend: ${YELLOW}http://localhost:3000${NC}"
echo
echo -e "${GREEN}Happy coding! 🎉${NC}"
