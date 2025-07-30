#!/bin/bash

# Pinnacle Copilot macOS Installer

# Exit on error
set -e

echo "Installing Pinnacle Copilot for macOS..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="${SCRIPT_DIR}"

# Create Python virtual environment if it doesn't exist
if [ ! -d "${INSTALL_DIR}/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "${INSTALL_DIR}/.venv"
fi

# Activate virtual environment
source "${INSTALL_DIR}/.venv/bin/activate"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up platform directories
echo "Setting up platform directories..."
python3 - <<EOF
from config.mobile import setup_platform_directories
setup_platform_directories()
EOF

# Install macOS service
echo "Installing macOS service..."
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
mkdir -p "${LAUNCH_AGENTS_DIR}"
cp "${INSTALL_DIR}/com.pinnacle.copilot.plist" "${LAUNCH_AGENTS_DIR}/"

# Set correct permissions
chmod 644 "${LAUNCH_AGENTS_DIR}/com.pinnacle.copilot.plist"

# Load the service
echo "Loading service..."
launchctl load "${LAUNCH_AGENTS_DIR}/com.pinnacle.copilot.plist"

# Generate iOS configuration
echo "Generating iOS configuration..."
python3 scripts/generate_ios_config.py

echo "Installation complete!"
echo "Pinnacle Copilot is now installed and running as a service."
echo "Use 'macos_service.sh {start|stop|restart|status}' to manage the service."
