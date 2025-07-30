#!/bin/bash

# Pinnacle Copilot macOS Service Manager

# Environment setup
export PINNACLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHON_PATH="${PINNACLE_ROOT}/.venv/bin/python"
export PATH="${PINNACLE_ROOT}/.venv/bin:$PATH"

# Create necessary directories
mkdir -p "${PINNACLE_ROOT}/logs"
mkdir -p "${PINNACLE_ROOT}/data"
mkdir -p "${PINNACLE_ROOT}/uploads"

# Function to check if service is running
check_service() {
    pgrep -f "python main.py" > /dev/null
    return $?
}

# Function to start service
start_service() {
    echo "Starting Pinnacle Copilot..."
    cd "${PINNACLE_ROOT}"
    nohup "${PYTHON_PATH}" main.py > "${PINNACLE_ROOT}/logs/pinnacle.log" 2>&1 &
    sleep 2
    if check_service; then
        echo "Service started successfully"
    else
        echo "Failed to start service"
        exit 1
    fi
}

# Function to stop service
stop_service() {
    echo "Stopping Pinnacle Copilot..."
    pkill -f "python main.py"
    sleep 2
    if ! check_service; then
        echo "Service stopped successfully"
    else
        echo "Failed to stop service"
        exit 1
    fi
}

# Function to restart service
restart_service() {
    stop_service
    start_service
}

# Function to check service status
status_service() {
    if check_service; then
        echo "Pinnacle Copilot is running"
    else
        echo "Pinnacle Copilot is not running"
    fi
}

# Command line interface
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
