#!/bin/bash

# Start Xline server in the background
echo "Starting Xline server..."
/Users/samoey/Desktop/Xline/target/release/xline --config /Users/samoey/Desktop/Xline/config.toml > xline.log 2>&1 &
XLINE_PID=$!

echo "Xline server started with PID: $XLINE_PID"

# Function to clean up on exit
cleanup() {
    echo "Shutting down..."
    
    # Kill Xline server
    echo "Shutting down Xline server (PID: $XLINE_PID)"
    kill $XLINE_PID 2>/dev/null
    
    # Kill Pinnacle Copilot if it's running
    if [ -f "pinnacle.pid" ]; then
        PINNACLE_PID=$(cat pinnacle.pid)
        echo "Shutting down Pinnacle Copilot (PID: $PINNACLE_PID)"
        kill $PINNACLE_PID 2>/dev/null
        rm -f pinnacle.pid
    fi
    
    echo "All services stopped."
}

# Set up trap to catch termination signals
trap cleanup EXIT

# Wait a moment for Xline to start
echo "Waiting for Xline to initialize..."
sleep 5

# Start Pinnacle Copilot
echo "Starting Pinnacle Copilot..."
python pinnacle_copilot.py > pinnacle.log 2>&1 &
PINNACLE_PID=$!
echo $PINNACLE_PID > pinnacle.pid

echo "Pinnacle Copilot started with PID: $PINNACLE_PID"
echo "Access the application at: http://localhost:8000"
echo "Press Ctrl+C to stop all services"

# Keep the script running
wait $PINNACLE_PID
