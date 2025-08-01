#!/bin/bash

# Pinnacle Copilot Development Runner
# This script starts all services in development mode

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display a section header
section() {
    echo -e "\n${BLUE}==> $1${NC}"
}

# Start Docker services
section "Starting Docker services..."
docker-compose up -d

# Wait for PostgreSQL to be ready
section "Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U pinnacle -d pinnacle_copilot > /dev/null 2>&1; do
    sleep 1
done

# Run database migrations
section "Running database migrations..."
cd backend
alembic upgrade head

# Initialize sample data
section "Initializing sample data..."
python init_data.py

# Start the backend server in the background
section "Starting backend server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Move to frontend directory and start the frontend server
section "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Function to clean up on exit
cleanup() {
    echo -e "\n${GREEN}Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    cd ..
    docker-compose down
    exit 0
}

# Set up trap to catch exit signals
trap cleanup INT TERM

# Display URLs
section "Services are running!"
echo -e "${GREEN}Backend API:${NC} http://localhost:8000"
echo -e "${GREEN}API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}PGAdmin:${NC} http://localhost:5050 (email: admin@pinnacle.local, password: admin)"
echo -e "${GREEN}Redis Commander:${NC} http://localhost:8081"
echo -e "\n${BLUE}Press Ctrl+C to stop all services${NC}"

# Keep the script running
wait $BACKEND_PID $FRONTEND_PID
