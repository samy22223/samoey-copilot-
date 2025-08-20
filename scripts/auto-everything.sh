#!/bin/bash

# Samoey Copilot - Complete Automation Script
# One-command setup, deployment, and maintenance
# Usage: ./scripts/auto-everything.sh --mode [dev|staging|prod] [--auto-confirm] [--config FILE]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Animation characters
SPINNER="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PROGRESS_CHARS="▁▂▃▄▅▆▇█"

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODE="dev"
AUTO_CONFIRM=false
CONFIG_FILE=""
LOG_FILE="$PROJECT_DIR/logs/auto-everything.log"
PID_FILE="/tmp/samoey-copilot-auto.pid"
START_TIME=$(date +%s)

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

log_debug() {
    if [[ "$DEBUG" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $*" | tee -a "$LOG_FILE"
    fi
}

# Progress indicator
show_progress() {
    local message="$1"
    local pid=$2
    local delay=0.1
    local temp_file="/tmp/progress_$$.tmp"
    
    echo -ne "${BLUE}$message${NC} "
    
    while kill -0 $pid 2>/dev/null; do
        for char in $PROGRESS_CHARS; do
            echo -ne "\r${BLUE}$message${NC} $char"
            sleep $delay
        done
    done
    
    wait $pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -ne "\r${GREEN}✓ $message${NC}\n"
    else
        echo -ne "\r${RED}✗ $message${NC}\n"
    fi
    
    return $exit_code
}

# Spinner for long operations
show_spinner() {
    local message="$1"
    local pid=$2
    local delay=0.1
    
    echo -ne "${BLUE}$message${NC} "
    
    while kill -0 $pid 2>/dev/null; do
        for char in $SPINNER; do
            echo -ne "\r${BLUE}$message${NC} $char"
            sleep $delay
        done
    done
    
    wait $pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -ne "\r${GREEN}✓ $message${NC}\n"
    else
        echo -ne "\r${RED}✗ $message${NC}\n"
    fi
    
    return $exit_code
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is not recommended for security reasons."
        if ! $AUTO_CONFIRM; then
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_error "Aborted by user"
                exit 1
            fi
        fi
    fi
}

# Check for existing process
check_existing_process() {
    if [ -f "$PID_FILE" ]; then
        local existing_pid=$(cat "$PID_FILE")
        if kill -0 "$existing_pid" 2>/dev/null; then
            log_error "Another automation process is already running (PID: $existing_pid)"
            log_info "If you believe this is incorrect, remove $PID_FILE"
            exit 1
        else
            log_debug "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Create new PID file
    echo $$ > "$PID_FILE"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    if [ -f "$PID_FILE" ] && [ $(cat "$PID_FILE") -eq $$ ]; then
        rm -f "$PID_FILE"
    fi
    
    if [ $exit_code -eq 0 ]; then
        log_success "Automation completed successfully in ${duration}s"
    else
        log_error "Automation failed after ${duration}s"
    fi
    
    exit $exit_code
}

# Trap signals
trap cleanup EXIT INT TERM

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --auto-confirm)
                AUTO_CONFIRM=true
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help
show_help() {
    cat << EOF
Samoey Copilot - Complete Automation Script

USAGE:
    $0 --mode MODE [OPTIONS]

MODES:
    dev         Development setup
    staging     Staging deployment
    prod        Production deployment

OPTIONS:
    --auto-confirm      Skip all confirmation prompts
    --config FILE       Use custom configuration file
    --debug             Enable debug logging
    --help, -h          Show this help message

EXAMPLES:
    $0 --mode dev --auto-confirm
    $0 --mode prod --config ./my-config.json
    $0 --mode staging --debug

EOF
}

# Validate mode
validate_mode() {
    case "$MODE" in
        dev|staging|prod)
            log_info "Target mode: $MODE"
            ;;
        *)
            log_error "Invalid mode: $MODE. Must be dev, staging, or prod"
            exit 1
            ;;
    esac
}

# Validate configuration file
validate_config() {
    if [[ -n "$CONFIG_FILE" && ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        log_warning "Unsupported OS: $OSTYPE"
        OS="unknown"
    fi
    
    log_info "Detected OS: $OS"
    
    # Check required commands
    local required_commands=("curl" "wget" "git" "python3" "node" "npm")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_warning "Missing required commands: ${missing_commands[*]}"
        log_info "Will attempt to install missing dependencies..."
    else
        log_success "All required commands are available"
    fi
    
    # Check disk space (minimum 5GB)
    local available_space=$(df -k "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    local required_space=$((5 * 1024 * 1024)) # 5GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        log_warning "Low disk space: $((available_space / 1024 / 1024))GB available, 5GB recommended"
    else
        log_success "Sufficient disk space available"
    fi
    
    # Check memory (minimum 4GB)
    if [[ "$OS" == "linux" ]]; then
        local total_memory=$(free -m | awk 'NR==2{printf "%.0f", $2}')
        if [[ $total_memory -lt 4096 ]]; then
            log_warning "Low memory: ${total_memory}MB available, 4GB recommended"
        else
            log_success "Sufficient memory available"
        fi
    fi
}

# Run environment detection
run_env_detection() {
    log_info "Running environment detection..."
    
    if [[ ! -f "$PROJECT_DIR/automation/env-detector.sh" ]]; then
        log_error "Environment detection script not found"
        exit 1
    fi
    
    chmod +x "$PROJECT_DIR/automation/env-detector.sh"
    
    # Run environment detection in background
    "$PROJECT_DIR/automation/env-detector.sh" --mode "$MODE" &
    local pid=$!
    
    if show_spinner "Detecting environment..." $pid; then
        log_success "Environment detection completed"
    else
        log_error "Environment detection failed"
        exit 1
    fi
}

# Generate configuration
generate_config() {
    log_info "Generating configuration..."
    
    if [[ -n "$CONFIG_FILE" ]]; then
        log_info "Using custom configuration: $CONFIG_FILE"
        cp "$CONFIG_FILE" "$PROJECT_DIR/automation/current-config.json"
    else
        if [[ ! -f "$PROJECT_DIR/automation/config-generator.py" ]]; then
            log_error "Configuration generator not found"
            exit 1
        fi
        
        # Generate configuration in background
        python3 "$PROJECT_DIR/automation/config-generator.py" --mode "$MODE" &
        local pid=$!
        
        if show_spinner "Generating configuration..." $pid; then
            log_success "Configuration generated successfully"
        else
            log_error "Configuration generation failed"
            exit 1
        fi
    fi
}

# Run setup automation
run_setup() {
    log_info "Running setup automation..."
    
    if [[ ! -f "$PROJECT_DIR/automation/setup-automation.sh" ]]; then
        log_error "Setup automation script not found"
        exit 1
    fi
    
    chmod +x "$PROJECT_DIR/automation/setup-automation.sh"
    
    # Run setup in background
    "$PROJECT_DIR/automation/setup-automation.sh" --mode "$MODE" --auto-confirm $AUTO_CONFIRM &
    local pid=$!
    
    if show_progress "Setting up environment..." $pid; then
        log_success "Setup completed successfully"
    else
        log_error "Setup failed"
        exit 1
    fi
}

# Run deployment automation
run_deployment() {
    log_info "Running deployment automation..."
    
    if [[ ! -f "$PROJECT_DIR/automation/deploy-automation.sh" ]]; then
        log_error "Deployment automation script not found"
        exit 1
    fi
    
    chmod +x "$PROJECT_DIR/automation/deploy-automation.sh"
    
    # Run deployment in background
    "$PROJECT_DIR/automation/deploy-automation.sh" --mode "$MODE" --auto-confirm $AUTO_CONFIRM &
    local pid=$!
    
    if show_progress "Deploying application..." $pid; then
        log_success "Deployment completed successfully"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Run monitoring automation
run_monitoring() {
    log_info "Setting up monitoring..."
    
    if [[ ! -f "$PROJECT_DIR/automation/monitoring-automation.sh" ]]; then
        log_warning "Monitoring automation script not found, skipping..."
        return 0
    fi
    
    chmod +x "$PROJECT_DIR/automation/monitoring-automation.sh"
    
    # Run monitoring setup in background
    "$PROJECT_DIR/automation/monitoring-automation.sh" --mode "$MODE" --auto-confirm $AUTO_CONFIRM &
    local pid=$!
    
    if show_spinner "Setting up monitoring..." $pid; then
        log_success "Monitoring setup completed"
    else
        log_warning "Monitoring setup failed, continuing..."
    fi
}

# Run validation
run_validation() {
    log_info "Running validation..."
    
    if [[ ! -f "$PROJECT_DIR/automation/validation-automation.sh" ]]; then
        log_error "Validation automation script not found"
        exit 1
    fi
    
    chmod +x "$PROJECT_DIR/automation/validation-automation.sh"
    
    # Run validation in background
    "$PROJECT_DIR/automation/validation-automation.sh" --mode "$MODE" &
    local pid=$!
    
    if show_progress "Validating deployment..." $pid; then
        log_success "Validation completed successfully"
    else
        log_error "Validation failed"
        exit 1
    fi
}

# Show completion summary
show_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo
    echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║                Samoey Copilot Automation Complete               ║${NC}"
    echo -e "${MAGENTA}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${MAGENTA}║  Mode:        ${WHITE}$MODE${NC}                                        ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  Duration:    ${WHITE}$duration seconds${NC}                                 ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  Log File:    ${WHITE}$LOG_FILE${NC}                              ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${MAGENTA}║  Access Points:                                                   ║${NC}"
    echo -e "${MAGENTA}║  • Frontend:   ${WHITE}http://localhost:3000${NC}                          ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  • Backend:    ${WHITE}http://localhost:8000${NC}                          ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  • API Docs:   ${WHITE}http://localhost:8000/docs${NC}                      ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  • Monitoring: ${WHITE}http://localhost:3000${NC} (Grafana)              ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${MAGENTA}║  Next Steps:                                                      ║${NC}"
    echo -e "${MAGENTA}║  1. Check application status: ${WHITE}npm run health${NC}                ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  2. View logs: ${WHITE}tail -f $LOG_FILE${NC}                       ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║  3. Access monitoring dashboard                                     ║${NC}"
    echo -e "${MAGENTA}║  4. Test all features and endpoints                                ║${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${GREEN}🎉 Samoey Copilot is ready! 🎉${NC}"
    echo
}

# Main execution
main() {
    # Parse arguments
    parse_args "$@"
    
    # Validate inputs
    validate_mode
    validate_config
    
    # Show banner
    echo -e "${CYAN}"
    cat << 'EOF'
    ____  _       _ _     _                       _       
   |  _ \(_) __ _(_) | __| | ___ __   __ _ _ __ | | ___  
   | | | | |/ _` | | |/ _` |/ / '_ \ / _` | '_ \| |/ _ \ 
   | |_| | | (_| | | | (_|   <| |_) | (_| | | | | | (_) |
   |____/|_|\__, |_|_|\__,_|\_\ .__/ \__,_|_| |_|_|\___/ 
             |___/              |_|                       
EOF
    echo -e "${NC}"
    echo -e "${BLUE}Samoey Copilot - Complete Automation System${NC}"
    echo -e "${BLUE}Mode: $MODE | Auto-confirm: $AUTO_CONFIRM${NC}"
    echo
    
    # Initial checks
    check_root
    check_existing_process
    
    log_info "Starting Samoey Copilot automation..."
    log_info "Project directory: $PROJECT_DIR"
    log_info "Mode: $MODE"
    
    # Execute automation phases
    check_requirements
    run_env_detection
    generate_config
    run_setup
    run_deployment
    run_monitoring
    run_validation
    
    # Show completion summary
    show_summary
    
    log_success "Samoey Copilot automation completed successfully!"
}

# Run main function
main "$@"
