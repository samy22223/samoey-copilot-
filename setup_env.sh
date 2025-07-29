#!/bin/bash

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Initialize database
echo "Initializing database..."
python -c "from backend.db.session import SessionLocal; from backend.db.init_db import init_db; init_db(SessionLocal())"

echo "\nSetup complete! Activate the virtual environment with:"
echo "source venv/bin/activate"
