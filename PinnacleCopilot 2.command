#!/bin/bash
# Pinnacle Copilot Launcher
# This script launches the Pinnacle Copilot application

# Get the directory where this script is located
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the app directory
cd "$APP_DIR"

# Set up environment
export PYTHONPATH="$APP_DIR:$PYTHONPATH"
export PINNACLE_CONFIG_DIR="$HOME/Library/Application Support/PinnacleCopilot"

# Create necessary directories
mkdir -p "$PINNACLE_CONFIG_DIR"
mkdir -p "$HOME/Library/Logs/PinnacleCopilot"

# Set up log file
LOG_FILE="$HOME/Library/Logs/PinnacleCopilot/pinnacle_copilot.log"
echo "Starting Pinnacle Copilot..."
echo "Logs available at: $LOG_FILE"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if requirements are installed
if ! pip show -r requirements.txt &> /dev/null; then
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Start the application
echo "Starting Pinnacle Copilot..."
uvicorn backend.agents.ai_team.dashboard.app:app --host 127.0.0.1 --port 8000 --reload

# Keep the terminal open if there's an error
if [ $? -ne 0 ]; then
    echo "The application encountered an error. Press Enter to close this window..."
    read
fi
