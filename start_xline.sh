#!/bin/bash

# Start Xline server in the background
/Users/samoey/Desktop/Xline/target/release/xline --config /Users/samoey/Desktop/Xline/config.toml &
XLINE_PID=$!

# Function to clean up on exit
cleanup() {
    echo "Shutting down Xline server..."
    kill $XLINE_PID
    wait $XLINE_PID 2>/dev/null
}

# Set up trap to catch termination signals
trap cleanup EXIT

# Keep the script running
wait $XLINE_PID
