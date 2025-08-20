#!/bin/bash

# Unified Samoey Copilot Deployment Script
# This script handles deployment for various environments

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Samoey Copilot Deployment Script${NC}"

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

# Default values
ENVIRONMENT="staging"
DEPLOY_TYPE="docker"
SKIP_TESTS=false
SKIP_BUILD=false
FORCE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --type|--deploy-type)
            DEPLOY_TYPE="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --env, --environment ENV   Deployment environment (staging, production) [default: staging]"
            echo "  --type, --deploy-type TYPE   Deployment type (docker, kubernetes, manual) [default: docker]"
            echo "  --skip-tests              Skip running tests"
            echo "  --skip-build              Skip build step"
            echo "  --force                   Force deployment without confirmation"
            echo "  --help, -h                Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

# Validate deploy type
if [[ "$DEPLOY_TYPE" != "docker" && "$DEPLOY_TYPE" != "kubernetes" && "$DEPLOY_TYPE" != "manual" ]]; then
    print_error "Invalid deploy type: $DEPLOY_TYPE. Must be 'docker', 'kubernetes', or 'manual'"
    exit 1
fi

# Show deployment plan
echo ""
echo -e "${BLUE}Deployment Plan:${NC}"
echo "Environment: $ENVIRONMENT"
echo "Deploy Type: $DEPLOY_TYPE"
echo "Skip Tests: $SKIP_TESTS"
echo "Skip Build: $SKIP_BUILD"
echo "Force: $FORCE"
echo ""

# Ask for confirmation unless force is enabled
if [[ "$FORCE" != true ]]; then
    read -p "Do you want to continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
fi

# Check if we're in the right directory
if [[ ! -f "package.json" ]]; then
    print_error "Not in the Samoey Copilot root directory"
    exit 1
fi

# Install dependencies if needed
print_status "Checking dependencies..."
if [[ ! -d "node_modules" ]]; then
    print_status "Installing root dependencies..."
    npm install
fi

if [[ ! -d "frontend/node_modules" ]]; then
    print_status "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

if [[ ! -d "venv" ]]; then
    print_status "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    print_success "Dependencies already installed"
fi

# Run tests if not skipped
if [[ "$SKIP_TESTS" != true ]]; then
    print_status "Running tests..."
    
    # Frontend tests
    if [[ -d "frontend" ]]; then
        print_status "Running frontend tests..."
        cd frontend
        if npm run test; then
            print_success "Frontend tests passed"
        else
            print_error "Frontend tests failed"
            exit 1
        fi
        cd ..
    fi
    
    # Backend tests
    print_status "Running backend tests..."
    source venv/bin/activate
    if pytest app/tests/ -v --cov=app; then
        print_success "Backend tests passed"
    else
        print_error "Backend tests failed"
        exit 1
    fi
else
    print_warning "Skipping tests"
fi

# Build if not skipped
if [[ "$SKIP_BUILD" != true ]]; then
    print_status "Building application..."
    
    # Build frontend
    if [[ -d "frontend" ]]; then
        print_status "Building frontend..."
        cd frontend
        if npm run build; then
            print_success "Frontend built successfully"
        else
            print_error "Frontend build failed"
            exit 1
        fi
        cd ..
    fi
    
    # Build backend
    print_status "Building backend..."
    source venv/bin/activate
    if python -m pip install -r requirements-prod.txt; then
        print_success "Backend dependencies installed"
    else
        print_error "Backend dependencies installation failed"
        exit 1
    fi
else
    print_warning "Skipping build"
fi

# Deploy based on type
case $DEPLOY_TYPE in
    "docker")
        print_status "Deploying with Docker..."
        
        # Build Docker image
        print_status "Building Docker image..."
        if docker build -t samoey-copilot:$ENVIRONMENT .; then
            print_success "Docker image built"
        else
            print_error "Docker build failed"
            exit 1
        fi
        
        # Stop existing container if any
        print_status "Stopping existing container..."
        docker stop samoey-copilot-$ENVIRONMENT 2>/dev/null || true
        docker rm samoey-copilot-$ENVIRONMENT 2>/dev/null || true
        
        # Start new container
        print_status "Starting new container..."
        if docker run -d \
            --name samoey-copilot-$ENVIRONMENT \
            --env-file .env \
            -p 8000:8000 \
            -v $(pwd)/data:/app/data \
            -v $(pwd)/logs:/app/logs \
            --restart unless-stopped \
            samoey-copilot:$ENVIRONMENT; then
            print_success "Container started successfully"
        else
            print_error "Container start failed"
            exit 1
        fi
        
        # Health check
        print_status "Performing health check..."
        sleep 10
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Health check passed"
        else
            print_warning "Health check failed - check logs"
        fi
        ;;
        
    "kubernetes")
        print_status "Deploying to Kubernetes..."
        
        # Check kubectl
        if ! command -v kubectl &> /dev/null; then
            print_error "kubectl is not installed"
            exit 1
        fi
        
        # Apply Kubernetes manifests
        print_status "Applying Kubernetes manifests..."
        if kubectl apply -f kubernetes/; then
            print_success "Kubernetes manifests applied"
        else
            print_error "Kubernetes deployment failed"
            exit 1
        fi
        
        # Wait for deployment
        print_status "Waiting for deployment to be ready..."
        if kubectl wait --for=condition=ready pod -l app=samoey-copilot --timeout=300s; then
            print_success "Deployment is ready"
        else
            print_error "Deployment timeout"
            exit 1
        fi
        ;;
        
    "manual")
        print_status "Manual deployment..."
        
        # Stop existing process
        print_status "Stopping existing process..."
        pkill -f "uvicorn app.main:app" 2>/dev/null || true
        
        # Start application
        print_status "Starting application..."
        source venv/bin/activate
        nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 > logs/app.log 2>&1 &
        
        # Health check
        sleep 5
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Application started successfully"
        else
            print_error "Application failed to start"
            exit 1
        fi
        ;;
esac

# Final status
echo ""
echo -e "${GREEN}✨ Deployment completed successfully! ✨${NC}"
echo ""
echo -e "${BLUE}Access points:${NC}"
echo "- Application: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Health Check: http://localhost:8000/health"
echo ""
if [[ "$DEPLOY_TYPE" == "docker" ]]; then
    echo "- View logs: docker logs samoey-copilot-$ENVIRONMENT"
    echo "- Stop container: docker stop samoey-copilot-$ENVIRONMENT"
elif [[ "$DEPLOY_TYPE" == "manual" ]]; then
    echo "- View logs: tail -f logs/app.log"
    echo "- Stop process: pkill -f 'uvicorn app.main:app'"
fi
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"
