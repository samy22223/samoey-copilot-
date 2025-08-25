#!/bin/bash
cd app
echo "Starting backend build..."
npm run lint && python -m pytest --cov=. && pip install -r requirements.txt
echo "Backend build completed"
