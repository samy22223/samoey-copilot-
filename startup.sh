#!/bin/bash

# Create necessary directories
echo "Creating required directories..."
mkdir -p data/chat_history data/vectorstore config

# Create default config files if they don't exist
if [ ! -f "config/custom_instructions.json" ]; then
    echo '{
        "system_prompt": "You are Pinnacle Copilot, an advanced AI assistant.",
        "language": "en",
        "tone": "friendly",
        "knowledge_sources": ["system"]
    }' > config/custom_instructions.json
fi

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Set execute permissions on scripts
chmod +x launch.command

# Create desktop shortcut (macOS)
if [ "$(uname)" == "Darwin" ]; then
    echo "Creating desktop shortcut..."
    ln -sf "$(pwd)/launch.command" "$HOME/Desktop/PinnacleCopilot.command"
fi

echo "Setup complete! You can now run './launch.command' to start Pinnacle Copilot."
