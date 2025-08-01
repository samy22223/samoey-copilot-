#!/bin/bash

# Simple Aider setup script
set -e

echo "🚀 Setting up Aider with Python 3.10"
echo "================================"

# Create project directory
PROJECT_DIR="$HOME/CascadeProjects/aider-chat"
echo "📁 Creating project directory at $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create and activate virtual environment with Python 3.10
echo "🐍 Creating Python 3.10 virtual environment"
/usr/local/bin/python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip and install required build tools
echo "🛠️  Installing build tools"
pip install --upgrade pip
pip install wheel setuptools

# Install Aider
echo "🤖 Installing Aider"
pip install aider-chat

# Create a simple README.md
cat > README.md << 'EOL'
# Aider Chat Project

Welcome to your Aider chat project for pair programming with AI!

## Quick Start

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Start Aider:
   ```bash
   aider
   ```

## Usage

- Describe the changes you want to make in natural language
- Aider will help you write and modify code
- All changes will be shown for your approval before being applied
EOL

echo ""
echo "✅ Setup complete!"
echo ""
echo "To get started, run these commands:"
echo "cd '$PROJECT_DIR'"
echo "source venv/bin/activate"
echo "aider"
echo ""
echo "Happy coding! 🚀"
