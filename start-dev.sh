#!/bin/bash

# Start the development server
echo "Starting Pinnacle Copilot in development mode..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
