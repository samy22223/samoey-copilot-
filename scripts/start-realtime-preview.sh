#!/bin/bash

# Real-time Preview Setup Script for Samoey Copilot
# This script sets up the complete development environment with real-time preview

set -e

echo "🚀 Starting Samoey Copilot Real-Time Preview Setup"
echo "=================================================="

# Check if VSCode is installed
if ! command -v code &> /dev/null; then
    echo "❌ VSCode is not installed. Please install VSCode first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Navigate to project root
cd "$(dirname "$0")/.."
echo "📁 Working directory: $(pwd)"

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ ! -d "frontend/node_modules" ] || [ ! -d "app/venv" ]; then
    echo "📦 Installing dependencies..."
    npm run install:all
else
    echo "✅ Dependencies already installed"
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Cleaning up background processes..."
    if [ ! -z "$LIVE_SERVER_PID" ]; then
        kill $LIVE_SERVER_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Live Server in background
echo "🌐 Starting Live Server on port 3001..."
cd frontend
npx live-server --port=3001 --host=localhost --no-browser --quiet &
LIVE_SERVER_PID=$!
cd ..

# Wait a moment for Live Server to start
sleep 2

# Start frontend development server
echo "🎨 Starting Frontend development server on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

# Start backend development server
echo "🔧 Starting Backend development server on port 8000..."
cd app
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo ""
echo "🎉 Real-Time Preview Environment is Ready!"
echo "========================================="
echo "📱 Frontend: http://localhost:3000"
echo "🌐 Live Preview: http://localhost:3001"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Features:"
echo "   • Real-time browser preview with hot reload"
echo "   • Live server proxy for API integration"
echo "   • WebSocket support for real-time features"
echo "   • Hot reload for both frontend and backend"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo ""

# Wait for all background processes
wait
