#!/bin/bash

# Samoey Copilot - Environment Detection Script
# Automatically detects system environment and requirements

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODE="dev"
ENVIRONMENT_FILE="$PROJECT_DIR/automation/environment.json"
LOG_FILE="$PROJECT_DIR/logs/env-detection.log"

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

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
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
Samoey Copilot - Environment Detection Script

USAGE:
    $0 --mode MODE [OPTIONS]

MODES:
    dev         Development environment
    staging     Staging environment
    prod        Production environment

OPTIONS:
    --help, -h          Show this help message

EOF
}

# Detect operating system
detect_os() {
    log_info "Detecting operating system..."
    
    local os_info=""
    local os_name=""
    local os_version=""
    local os_arch=""
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        os_name="linux"
        if [[ -f /etc/os-release ]]; then
            source /etc/os-release
            os_info="$NAME $VERSION"
        elif [[ -f /etc/redhat-release ]]; then
            os_info=$(cat /etc/redhat-release)
        elif [[ -f /etc/debian_version ]]; then
            os_info="Debian $(cat /etc/debian_version)"
        else
            os_info="Linux (Unknown distribution)"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        os_name="macos"
        os_info="macOS $(sw_vers -productVersion)"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        os_name="windows"
        os_info="Windows $(uname -r)"
    else
        os_name="unknown"
        os_info="Unknown OS: $OSTYPE"
    fi
    
    # Detect architecture
    os_arch=$(uname -m)
    
    log_info "OS: $os_info"
    log_info "Architecture: $os_arch"
    
    # Save to environment file
    cat > "$ENVIRONMENT_FILE" << EOF
{
  "os": {
    "name": "$os_name",
    "info": "$os_info",
    "arch": "$os_arch",
    "type": "$OSTYPE"
  },
EOF
}

# Detect system resources
detect_resources() {
    log_info "Detecting system resources..."
    
    local cpu_info=""
    local memory_total=""
    local memory_available=""
    local disk_total=""
    local disk_available=""
    
    # CPU information
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        cpu_info=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
        memory_total=$(free -h | awk 'NR==2{printf "%.1fGB", $2}')
        memory_available=$(free -h | awk 'NR==2{printf "%.1fGB", $7}')
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        cpu_info=$(sysctl -n machdep.cpu.brand_string)
        memory_total=$(system_profiler SPHardwareDataType | grep "Memory:" | awk '{print $2 $3}')
        memory_available=$(vm_stat | perl -ne '/page size of (\d+)/ and $ps=$1; /Pages free:\s+(\d+)/ and printf "%.1fGB", ($1*$ps)/1024/1024/1024')
    fi
    
    # Disk information
    if command -v df &> /dev/null; then
        disk_info=$(df -h "$PROJECT_DIR" | awk 'NR==2{print $2 " total, " $4 " available"}')
        disk_total=$(df -k "$PROJECT_DIR" | awk 'NR==2{print $2}')
        disk_available=$(df -k "$PROJECT_DIR" | awk 'NR==2{print $4}')
    fi
    
    log_info "CPU: $cpu_info"
    log_info "Memory: $memory_total total, $memory_available available"
    log_info "Disk: $disk_info"
    
    # Append to environment file
    cat >> "$ENVIRONMENT_FILE" << EOF
  "resources": {
    "cpu": "$cpu_info",
    "memory": {
      "total": "$memory_total",
      "available": "$memory_available"
    },
    "disk": {
      "total": "$disk_total",
      "available": "$disk_available"
    }
  },
EOF
}

# Detect available commands and tools
detect_commands() {
    log_info "Detecting available commands and tools..."
    
    local commands=()
    local missing_commands=()
    
    # Essential commands
    local essential_commands=("bash" "curl" "wget" "git" "python3" "pip3" "node" "npm" "docker")
    
    # Development tools
    local dev_commands=("make" "gcc" "g++" "cmake" "valgrind")
    
    # Database tools
    local db_commands=("psql" "redis-cli" "mongosh" "mysql")
    
    # Container tools
    local container_commands=("docker-compose" "kubectl" "helm")
    
    # Monitoring tools
    local monitoring_commands=("prometheus" "grafana-server" "nginx")
    
    # Check all commands
    for cmd in "${essential_commands[@]}" "${dev_commands[@]}" "${db_commands[@]}" "${container_commands[@]}" "${monitoring_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            commands+=("$cmd")
            log_debug "Found: $cmd"
        else
            missing_commands+=("$cmd")
            log_debug "Missing: $cmd"
        fi
    done
    
    log_info "Found ${#commands[@]} commands, missing ${#missing_commands[@]} commands"
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_warning "Missing commands: ${missing_commands[*]}"
    fi
    
    # Append to environment file
    cat >> "$ENVIRONMENT_FILE" << EOF
  "commands": {
    "available": [$(printf '"%s",' "${commands[@]}" | sed 's/,$//')],
    "missing": [$(printf '"%s",' "${missing_commands[@]}" | sed 's/,$//')]
  },
EOF
}

# Detect programming languages and versions
detect_languages() {
    log_info "Detecting programming languages and versions..."
    
    local languages=()
    
    # Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        languages+=("{\"name\": \"python\", \"version\": \"$python_version\"}")
        log_info "Python: $python_version"
    fi
    
    # Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        languages+=("{\"name\": \"node\", \"version\": \"$node_version\"}")
        log_info "Node.js: $node_version"
    fi
    
    # npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        languages+=("{\"name\": \"npm\", \"version\": \"$npm_version\"}")
        log_info "npm: $npm_version"
    fi
    
    # Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        languages+=("{\"name\": \"docker\", \"version\": \"$docker_version\"}")
        log_info "Docker: $docker_version"
    fi
    
    # Git
    if command -v git &> /dev/null; then
        local git_version=$(git --version | awk '{print $3}')
        languages+=("{\"name\": \"git\", \"version\": \"$git_version\"}")
        log_info "Git: $git_version"
    fi
    
    # Append to environment file
    cat >> "$ENVIRONMENT_FILE" << EOF
  "languages": [$(printf '%s,' "${languages[@]}" | sed 's/,$//')],
EOF
}

# Detect network connectivity
detect_network() {
    log_info "Detecting network connectivity..."
    
    local network_status="unknown"
    local internet_connectivity="false"
    local dns_resolution="false"
    local ports_status=()
    
    # Check internet connectivity
    if curl -s --connect-timeout 5 https://www.google.com > /dev/null 2>&1; then
        internet_connectivity="true"
        log_success "Internet connectivity: OK"
    else
        log_warning "Internet connectivity: Failed"
    fi
    
    # Check DNS resolution
    if nslookup google.com > /dev/null 2>&1; then
        dns_resolution="true"
        log_success "DNS resolution: OK"
    else
        log_warning "DNS resolution: Failed"
    fi
    
    # Check common ports
    local ports=("22" "80" "443" "3000" "8000" "5432" "6379")
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            ports_status+=("{\"port\": $port, \"status\": \"open\"}")
            log_debug "Port $port: Open"
        else
            ports_status+=("{\"port\": $port, \"status\": \"closed\"}")
            log_debug "Port $port: Closed"
        fi
    done
    
    # Determine overall network status
    if [[ "$internet_connectivity" == "true" && "$dns_resolution" == "true" ]]; then
        network_status="good"
    elif [[ "$internet_connectivity" == "true" || "$dns_resolution" == "true" ]]; then
        network_status="partial"
    else
        network_status="poor"
    fi
    
    log_info "Network status: $network_status"
    
    # Append to environment file
    cat >> "$ENVIRONMENT_FILE" << EOF
  "network": {
    "status": "$network_status",
    "internet": $internet_connectivity,
    "dns": $dns_resolution,
    "ports": [$(printf '%s,' "${ports_status[@]}" | sed 's/,$//')]
  },
EOF
}

# Detect security environment
detect_security() {
    log_info "Detecting security environment..."
    
    local firewall_status="unknown"
    local selinux_status="unknown"
    local user_privileges="unknown"
    
    # Check firewall status
    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "active"; then
            firewall_status="enabled"
            log_info "UFW firewall: Enabled"
        else
            firewall_status="disabled"
            log_info "UFW firewall: Disabled"
        fi
    elif command -v firewall-cmd &> /dev/null; then
        if firewall-cmd --state | grep -q "running"; then
            firewall_status="enabled"
            log_info "Firewalld: Enabled"
        else
            firewall_status="disabled"
            log_info "Firewalld: Disabled"
        fi
    else
        firewall_status="not_available"
        log_info "Firewall: Not available"
    fi
    
    # Check SELinux status
    if [[ -f /etc/selinux/config ]]; then
        if getenforce 2>/dev/null | grep -q "Enforcing"; then
            selinux_status="enforcing"
            log_info "SELinux: Enforcing"
        elif getenforce 2>/dev/null | grep -q "Permissive"; then
            selinux_status="permissive"
            log_info "SELinux: Permissive"
        else
            selinux_status="disabled"
            log_info "SELinux: Disabled"
        fi
    else
        selinux_status="not_available"
        log_info "SELinux: Not available"
    fi
    
    # Check user privileges
    if [[ $EUID -eq 0 ]]; then
        user_privileges="root"
        log_warning "Running as root user"
    else
        user_privileges="normal"
        log_info "Running as normal user"
    fi
    
    # Append to environment file
    cat >> "$ENVIRONMENT_FILE" << EOF
  "security": {
    "firewall": "$firewall_status",
    "selinux": "$selinux_status",
    "user_privileges": "$user_privileges"
  },
EOF
}

# Detect development environment
detect_development() {
    log_info "Detecting development environment..."
    
    local dev_tools=()
    local ide_detected="none"
    local editors=()
    
    # Check for common development tools
    if command -v code &> /dev/null; then
        dev_tools+=("vscode")
        log_info "VS Code detected"
    fi
    
    if command -v vim &> /dev/null; then
        dev_tools+=("vim")
        log_info "Vim detected"
    fi
    
    if command -v emacs &> /dev/null; then
        dev_tools+=("emacs")
        log_info "Emacs detected"
    fi
    
    # Check for IDE processes
    if pgrep -f "Visual Studio Code" > /dev/null; then
        ide_detected="vscode"
    elif pgrep -f "IntelliJ IDEA" > /dev/null; then
        ide_detected="intellij"
    elif pgrep -f "PyCharm" > /dev/null; then
        ide_detected="pycharm"
    fi
    
    # Check for common editors
    if [[ -n "$EDITOR" ]]; then
        editors+=("$EDITOR")
    fi
    
    if [[ -n "$VISUAL" ]]; then
        editors+=("$VISUAL")
    fi
    
    log_info "Development tools: ${dev_tools[*]:-none}"
    log_info "IDE detected: $ide_detected"
    
    # Append to environment file
    cat >> "$ENVIRONMENT_FILE" << EOF
  "development": {
    "tools": [$(printf '"%s",' "${dev_tools[@]}" | sed 's/,$//')],
    "ide": "$ide_detected",
    "editors": [$(printf '"%s",' "${editors[@]}" | sed 's/,$//')]
  },
EOF
}

# Generate recommendations
generate_recommendations() {
    log_info "Generating recommendations..."
    
    local recommendations=()
    
    # Read environment file to get current state
    if [[ -f "$ENVIRONMENT_FILE" ]]; then
        # Check for missing essential commands
        if grep -q '"missing": \[' "$ENVIRONMENT_FILE"; then
            recommendations+=("Install missing essential commands for full functionality")
        fi
        
        # Check network status
        if grep -q '"status": "poor"' "$ENVIRONMENT_FILE"; then
            recommendations+=("Check network connectivity and DNS settings")
        fi
        
        # Check disk space
        local disk_available=$(grep -o '"available": "[^"]*"' "$ENVIRONMENT_FILE" | head -1 | cut -d'"' -f4)
        if [[ "$disk_available" -lt 5242880 ]]; then  # Less than 5GB
            recommendations+=("Free up disk space (less than 5GB available)")
        fi
        
        # Check security
        if grep -q '"firewall": "disabled"' "$ENVIRONMENT_FILE"; then
            recommendations+=("Consider enabling firewall for security")
        fi
    fi
    
    # Mode-specific recommendations
    case "$MODE" in
        "dev")
            recommendations+=("Install development dependencies and tools")
            recommendations+=("Set up local database instances for development")
            ;;
        "staging")
            recommendations+=("Configure staging-specific security settings")
            recommendations+=("Set up monitoring and alerting for staging")
            ;;
        "prod")
            recommendations+=("Ensure all security measures are in place")
            recommendations+=("Set up production monitoring and backup systems")
            ;;
    esac
    
    # Add default recommendations
    recommendations+=("Review environment.json for detailed system information")
    recommendations+=("Follow the generated setup plan for optimal configuration")
    
    log_info "Generated ${#recommendations[@]} recommendations"
    
    # Append to environment file and close it
    cat >> "$ENVIRONMENT_FILE" << EOF
  "recommendations": [$(printf '"%s",' "${recommendations[@]}" | sed 's/,$//')],
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "mode": "$MODE"
}
EOF
}

# Main execution
main() {
    # Parse arguments
    parse_args "$@"
    
    log_info "Starting environment detection..."
    log_info "Mode: $MODE"
    
    # Execute detection functions
    detect_os
    detect_resources
    detect_commands
    detect_languages
    detect_network
    detect_security
    detect_development
    generate_recommendations
    
    log_success "Environment detection completed successfully!"
    log_info "Environment file saved to: $ENVIRONMENT_FILE"
    
    # Show summary
    echo
    echo -e "${CYAN}Environment Detection Summary:${NC}"
    echo -e "${BLUE}• OS: $(grep -o '"info": "[^"]*"' "$ENVIRONMENT_FILE" | head -1 | cut -d'"' -f4)${NC}"
    echo -e "${BLUE}• Memory: $(grep -o '"total": "[^"]*"' "$ENVIRONMENT_FILE" | head -1 | cut -d'"' -f4)${NC}"
    echo -e "${BLUE}• Network: $(grep -o '"status": "[^"]*"' "$ENVIRONMENT_FILE" | head -1 | cut -d'"' -f4)${NC}"
    echo -e "${BLUE}• Commands found: $(grep -o '"available":\s*\[[^]]*\]' "$ENVIRONMENT_FILE" | grep -o '"[^"]*"' | wc -l | tr -d ' ')${NC}"
    echo -e "${BLUE}• Recommendations: $(grep -o '"recommendations":\s*\[[^]]*\]' "$ENVIRONMENT_FILE" | grep -o '"[^"]*"' | wc -l | tr -d ' ')${NC}"
    echo
}

# Run main function
main "$@"
