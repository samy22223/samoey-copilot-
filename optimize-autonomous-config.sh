#!/bin/bash
# Autonomous System Configuration Optimizer for Samoey Copilot
# This script optimizes system thresholds and autonomy levels based on project requirements

set -e

CONFIG_FILE=".autonomous-project-config.json"
OPTIMIZED_CONFIG_FILE=".autonomous-project-config-optimized.json"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${GREEN}[$timestamp] INFO: $1${NC}"
}

warn_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${YELLOW}[$timestamp] WARN: $1${NC}"
}

error_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${RED}[$timestamp] ERROR: $1${NC}"
}

# Analyze current system resources
analyze_system_resources() {
    log_message "Analyzing current system resources..."

    # Get current CPU usage
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    log_message "Current CPU usage: ${cpu_usage}%"

    # Get current memory usage
    local memory_info=$(vm_stat | grep -E "(Pages free|Pages active|Pages inactive|Pages wired)")
    local free_pages=$(echo "$memory_info" | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    local active_pages=$(echo "$memory_info" | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
    local inactive_pages=$(echo "$memory_info" | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
    local wired_pages=$(echo "$memory_info" | grep "Pages wired" | awk '{print $3}' | sed 's/\.//')

    local total_pages=$((free_pages + active_pages + inactive_pages + wired_pages))
    local used_pages=$((active_pages + wired_pages))
    local memory_usage=$((used_pages * 100 / total_pages))

    log_message "Current Memory usage: ${memory_usage}%"

    # Get current disk usage
    local disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    log_message "Current Disk usage: ${disk_usage}%"

    # Return analysis results
    echo "${cpu_usage},${memory_usage},${disk_usage}"
}

# Get user preferences for autonomy level
get_autonomy_preference() {
    echo ""
    echo "Please select the preferred autonomy level for the development workflow:"
    echo ""
    echo "1) Limited - Human approval for major actions (safer, more control)"
    echo "2) Supervised - Autonomous with human oversight (balanced approach)"
    echo "3) Full - Complete autonomy (maximum automation)"
    echo ""
    read -p "Enter your choice (1-3): " choice

    case "$choice" in
        1) echo "limited" ;;
        2) echo "supervised" ;;
        3) echo "full" ;;
        *) echo "supervised" ;; # Default to supervised
    esac
}

# Optimize system thresholds based on current usage
optimize_thresholds() {
    local analysis_result=$(analyze_system_resources)
    local current_cpu=$(echo "$analysis_result" | cut -d',' -f1)
    local current_memory=$(echo "$analysis_result" | cut -d',' -f2)
    local current_disk=$(echo "$analysis_result" | cut -d',' -f3)

    log_message "Optimizing thresholds based on current system usage..."

    # Calculate optimized thresholds with safety margins
    local optimized_cpu=$((current_cpu + 25))
    if [ "$optimized_cpu" -gt 95 ]; then
        optimized_cpu=95
    fi

    local optimized_memory=$((current_memory + 20))
    if [ "$optimized_memory" -gt 95 ]; then
        optimized_memory=95
    fi

    local optimized_disk=$((current_disk + 10))
    if [ "$optimized_disk" -gt 95 ]; then
        optimized_disk=95
    fi

    log_message "Recommended thresholds:"
    log_message "  CPU: ${optimized_cpu}% (was 80%)"
    log_message "  Memory: ${optimized_memory}% (was 85%)"
    log_message "  Disk: ${optimized_disk}% (was 90%)"

    echo "${optimized_cpu},${optimized_memory},${optimized_disk}"
}

# Generate optimized configuration
generate_optimized_config() {
    local autonomy_level=$(get_autonomy_preference)
    local thresholds=$(optimize_thresholds)
    local optimized_cpu=$(echo "$thresholds" | cut -d',' -f1)
    local optimized_memory=$(echo "$thresholds" | cut -d',' -f2)
    local optimized_disk=$(echo "$thresholds" | cut -d',' -f3)

    log_message "Generating optimized configuration..."

    # Read original config and create optimized version
    if [ -f "$CONFIG_FILE" ]; then
        jq --arg autonomy_level "$autonomy_level" \
           --argjson cpu_threshold "$optimized_cpu" \
           --argjson memory_threshold "$optimized_memory" \
           --argjson disk_threshold "$optimized_disk" \
           '.autonomousSettings.autonomyLevel = $autonomy_level |
            .resourceManagement.cpuThreshold = $cpu_threshold |
            .resourceManagement.memoryThreshold = $memory_threshold |
            .resourceManagement.diskThreshold = $disk_threshold |
            .resourceManagement.monitoringInterval = 30 |
            .autonomousSettings.optimizeResources = true |
            .autonomousSettings.autoDeploy = false |
            .resourceManagement.cleanupInterval = 7200 |
            .resourceManagement.backupRetentionDays = 14' \
           "$CONFIG_FILE" > "$OPTIMIZED_CONFIG_FILE"

        log_message "Optimized configuration saved to $OPTIMIZED_CONFIG_FILE"

        # Show optimization summary
        echo ""
        echo "=== CONFIGURATION OPTIMIZATION SUMMARY ==="
        echo "Autonomy Level: $autonomy_level"
        echo "CPU Threshold: ${optimized_cpu}%"
        echo "Memory Threshold: ${optimized_memory}%"
        echo "Disk Threshold: ${optimized_disk}%"
        echo "Monitoring Interval: 30 seconds"
        echo "Cleanup Interval: 2 hours"
        echo "Backup Retention: 14 days"
        echo "=========================================="
        echo ""

        # Ask if user wants to apply the optimized configuration
        read -p "Apply optimized configuration? (y/n): " apply_choice
        if [ "$apply_choice" = "y" ] || [ "$apply_choice" = "Y" ]; then
            cp "$OPTIMIZED_CONFIG_FILE" "$CONFIG_FILE"
            log_message "Optimized configuration applied successfully!"
        else
            log_message "Optimized configuration saved but not applied."
        fi
    else
        error_message "Original configuration file not found: $CONFIG_FILE"
        exit 1
    fi
}

# Show help
show_help() {
    echo "Autonomous System Configuration Optimizer"
    echo ""
    echo "Usage: $0 {optimize|help}"
    echo ""
    echo "Commands:"
    echo "  optimize - Optimize autonomous system configuration"
    echo "  help     - Show this help message"
    echo ""
    echo "Features:"
    echo "  - Analyzes current system resource usage"
    echo "  - Optimizes CPU, memory, and disk thresholds"
    echo "  - Configures appropriate autonomy levels"
    echo "  - Adjusts monitoring and cleanup intervals"
    echo "  - Generates optimized configuration file"
    echo ""
}

# Main execution
main() {
    local action="$1"

    case "$action" in
        "optimize")
            echo "=== SAMOEY COPILOT AUTONOMOUS SYSTEM CONFIGURATION OPTIMIZER ==="
            echo ""
            generate_optimized_config
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
