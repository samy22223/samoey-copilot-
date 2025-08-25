#!/bin/bash

# Autonomous System Launcher for Samoey Copilot Project
# This script launches and coordinates all automation components for fully autonomous operation

set -e

# Configuration
LOG_FILE="$HOME/autonomous-system-launcher.log"
PROJECT_ROOT="$(pwd)"
MASTER_SCRIPT="$PROJECT_ROOT/autonomous-system-master-final.sh"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local level="$1"
    shift
    local message="$*"

    local color=""
    case "$level" in
        "ERROR") color="$RED" ;;
        "WARN") color="$YELLOW" ;;
        "INFO") color="$GREEN" ;;
        "DEBUG") color="$BLUE" ;;
        *) color="$NC" ;;
    esac

    echo -e "${color}[$timestamp] [$level] $message${NC}" | tee -a "$LOG_FILE"
}

# Show banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                SAMOEY COPILOT AUTONOMOUS SYSTEM              ║"
    echo "║           Fully Autonomous Build & Deployment System          ║"
    echo "║                    for macOS 11.7.10 Big Sur Intel             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Check system requirements
check_requirements() {
    log_message "INFO" "Checking system requirements..."

    local requirements_met=true

    # Check macOS version
    local macos_version=$(sw_vers -productVersion)
    log_message "INFO" "macOS Version: $macos_version"

    # Check required tools
    local required_tools=("bash" "python3" "jq" "bc" "docker" "git" "node" "npm")

    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            log_message "INFO" "✓ $tool is available"
        else
            log_message "WARN" "✗ $tool is not available"
            requirements_met=false
        fi
    done

    # Check available automation scripts
    local automation_scripts=(
        "auto-build-master.sh"
        "auto-deps.sh"
        "auto-space-manager.sh"
        "resource-intelligence.sh"
        "emergency-cleanup.sh"
    )

    log_message "INFO" "Checking automation components..."

    for script in "${automation_scripts[@]}"; do
        if [ -f "$PROJECT_ROOT/$script" ]; then
            chmod +x "$PROJECT_ROOT/$script"
            log_message "INFO" "✓ $script is available"
        else
            log_message "WARN" "✗ $script is missing"
        fi
    done

    if [ "$requirements_met" = true ]; then
        log_message "INFO" "All system requirements met"
        return 0
    else
        log_message "ERROR" "Some system requirements are not met"
        return 1
    fi
}

# Initialize the autonomous system
initialize_system() {
    log_message "INFO" "Initializing autonomous system..."

    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/.autonomous/backups"
    mkdir -p "$PROJECT_ROOT/.autonomous/analytics"
    mkdir -p "$PROJECT_ROOT/.autonomous/ml_models"
    mkdir -p "$PROJECT_ROOT/.autonomous/deployments"
    mkdir -p "$PROJECT_ROOT/.autonomous/logs"

    # Initialize log files
    touch "$LOG_FILE"
    touch "$PROJECT_ROOT/.autonomous/system.log"

    # Set up proper permissions
    chmod 755 "$PROJECT_ROOT/.autonomous"
    chmod -R 755 "$PROJECT_ROOT/.autonomous/"*

    log_message "INFO" "System initialization completed"
}

# Start all automation components
start_components() {
    log_message "INFO" "Starting automation components..."

    local components_started=0

    # Start Resource Intelligence
    if [ -f "$PROJECT_ROOT/resource-intelligence.sh" ]; then
        log_message "INFO" "Starting Resource Intelligence Engine..."
        "$PROJECT_ROOT/resource-intelligence.sh" start &
        components_started=$((components_started + 1))
    fi

    # Start Build Master
    if [ -f "$PROJECT_ROOT/auto-build-master.sh" ]; then
        log_message "INFO" "Starting Build Master..."
        "$PROJECT_ROOT/auto-build-master.sh" start &
        components_started=$((components_started + 1))
    fi

    # Start Dependency Manager
    if [ -f "$PROJECT_ROOT/auto-deps.sh" ]; then
        log_message "INFO" "Starting Dependency Manager..."
        # Note: auto-deps.sh doesn't have a start mode, so we'll run it in monitoring mode
        "$PROJECT_ROOT/auto-deps.sh" status &
        components_started=$((components_started + 1))
    fi

    # Start Space Manager (one-time setup)
    if [ -f "$PROJECT_ROOT/auto-space-manager.sh" ]; then
        log_message "INFO" "Setting up Space Manager..."
        "$PROJECT_ROOT/auto-space-manager.sh" &
        components_started=$((components_started + 1))
    fi

    log_message "INFO" "Started $components_started automation components"

    # Wait a moment for components to initialize
    sleep 5

    # Start the master system
    if [ -f "$MASTER_SCRIPT" ]; then
        log_message "INFO" "Starting Autonomous System Master..."
        "$MASTER_SCRIPT" start &
        MASTER_PID=$!
        log_message "INFO" "Autonomous System Master started with PID: $MASTER_PID"
    else
        log_message "ERROR" "Master script not found: $MASTER_SCRIPT"
        return 1
    fi

    return 0
}

# Show system status
show_status() {
    echo "=== AUTONOMOUS SYSTEM STATUS ==="
    echo "Current Time: $(date)"
    echo ""

    # Show master system status
    if [ -f "$MASTER_SCRIPT" ]; then
        echo "Master System Status:"
        "$MASTER_SCRIPT" status
        echo ""
    fi

    # Show individual component status
    echo "Individual Component Status:"

    # Resource Intelligence
    if [ -f "$PROJECT_ROOT/resource-intelligence.sh" ]; then
        echo "  Resource Intelligence: $(pgrep -f "resource-intelligence" > /dev/null && echo "Running" || echo "Stopped")"
    fi

    # Build Master
    if [ -f "$PROJECT_ROOT/auto-build-master.sh" ]; then
        echo "  Build Master: $(pgrep -f "auto-build-master" > /dev/null && echo "Running" || echo "Stopped")"
    fi

    # Dependency Manager
    if [ -f "$PROJECT_ROOT/auto-deps.sh" ]; then
        echo "  Dependency Manager: Available"
    fi

    # Space Manager
    if [ -f "$PROJECT_ROOT/auto-space-manager.sh" ]; then
        echo "  Space Manager: Available"
    fi

    echo ""
    echo "Log Files:"
    echo "  System Launcher: $LOG_FILE"
    echo "  Master System: $HOME/autonomous-system-master.log"
    echo "=================================="
}

# Stop all components
stop_components() {
    log_message "INFO" "Stopping autonomous system components..."

    # Stop master system first
    if [ -f "$MASTER_SCRIPT" ]; then
        log_message "INFO" "Stopping Autonomous System Master..."
        "$MASTER_SCRIPT" stop
    fi

    # Stop other components
    if [ -f "$PROJECT_ROOT/resource-intelligence.sh" ]; then
        log_message "INFO" "Stopping Resource Intelligence..."
        "$PROJECT_ROOT/resource-intelligence.sh" stop
    fi

    if [ -f "$PROJECT_ROOT/auto-build-master.sh" ]; then
        log_message "INFO" "Stopping Build Master..."
        "$PROJECT_ROOT/auto-build-master.sh" stop
    fi

    # Kill any remaining processes
    pkill -f "autonomous-system-master" 2>/dev/null || true
    pkill -f "resource-intelligence" 2>/dev/null || true
    pkill -f "auto-build-master" 2>/dev/null || true

    log_message "INFO" "All autonomous system components stopped"
}

# Show help
show_help() {
    echo "Samoey Copilot Autonomous System Launcher"
    echo ""
    echo "Usage: $0 {start|stop|status|restart|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the fully autonomous system"
    echo "  stop     - Stop all autonomous system components"
    echo "  status   - Show current system status"
    echo "  restart  - Restart the autonomous system"
    echo "  help     - Show this help message"
    echo ""
    echo "Features:"
    echo "  - Fully autonomous build and deployment system"
    echo "  - AI/ML-powered decision making"
    echo "  - Self-healing and recovery capabilities"
    echo "  - Predictive resource optimization"
    echo "  - Intelligent build scheduling"
    echo "  - Automated deployment management"
    echo "  - Continuous learning and adaptation"
    echo ""
    echo "Requirements:"
    echo "  - macOS 11.7.10 Big Sur Intel or later"
    echo "  - bash, python3, jq, bc, docker, git, node, npm"
    echo ""
    echo "Components:"
    echo "  - Autonomous System Master (orchestrator)"
    echo "  - Resource Intelligence Engine"
    echo "  - Build Master"
    echo "  - Dependency Manager"
    echo "  - Space Manager"
    echo "  - Emergency Cleanup System"
    echo ""
}

# Main execution
main() {
    local action="$1"

    case "$action" in
        "start")
            show_banner
            check_requirements || exit 1
            initialize_system
            start_components || exit 1
            log_message "INFO" "Samoey Copilot Autonomous System started successfully!"
            echo ""
            echo "The system is now running in fully autonomous mode."
            echo "Use '$0 status' to check system status."
            echo "Use '$0 stop' to shut down the system."
            ;;
        "stop")
            log_message "INFO" "Stopping Samoey Copilot Autonomous System..."
            stop_components
            log_message "INFO" "Samoey Copilot Autonomous System stopped successfully!"
            ;;
        "status")
            show_status
            ;;
        "restart")
            log_message "INFO" "Restarting Samoey Copilot Autonomous System..."
            stop_components
            sleep 3
            check_requirements || exit 1
            initialize_system
            start_components || exit 1
            log_message "INFO" "Samoey Copilot Autonomous System restarted successfully!"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "Invalid command: $action"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
