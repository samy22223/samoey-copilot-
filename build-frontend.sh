#!/bin/bash
cd frontend
echo "Starting frontend build..."
npm run lint && npm run test:ci && npm run build
echo "Frontend build completed"
