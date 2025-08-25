#!/bin/bash

# Automated Space Management Script for macOS 11.7.10 Big Sur Intel
# This script provides automated disk space management and monitoring

set -e

LOG_FILE="$HOME/auto-space-manager.log"
ALERT_THRESHOLD=85
CRITICAL_THRESHOLD=95
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Function to get current disk usage percentage
get_disk_usage() {
    df -h / | tail -1 | awk '{print $5}' | sed 's/%//'
}

# Function to log messages
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a $LOG_FILE
}

# Function to send notification
send_notification() {
    local title="$1"
    local message="$2"

    # Use macOS notification center
    osascript -e "display notification \"$message\" with title \"$title\""

    # Also log it
    log_message "NOTIFICATION: $title - $message"
}

# Function to cleanup caches
cleanup_caches() {
    log_message "Starting cache cleanup..."

    # Clear user caches
    if [ -d "$HOME/Library/Caches" ]; then
        local size_before=$(du -sh "$HOME/Library/Caches" 2>/dev/null | cut -f1)
        rm -rf "$HOME/Library/Caches/"* 2>/dev/null || true
        log_message "Cleared user caches (was: $size_before)"
    fi

    # Clear browser caches
    if [ -d "$HOME/Library/Application Support/Google/Chrome/Default/Cache" ]; then
        rm -rf "$HOME/Library/Application Support/Google/Chrome/Default/Cache/"* 2>/dev/null || true
        log_message "Cleared Chrome cache"
    fi

    if [ -d "$HOME/Library/Caches/com.apple.Safari" ]; then
        rm -rf "$HOME/Library/Caches/com.apple.Safari/"* 2>/dev/null || true
        log_message "Cleared Safari cache"
    fi

    # Clear Docker if available
    if command -v docker &> /dev/null; then
        docker system prune -f 2>/dev/null || true
        log_message "Cleaned Docker system"
    fi
}

# Function to cleanup logs
cleanup_logs() {
    log_message "Starting log cleanup..."

    # Clear old log files
    find "$HOME/Library/Logs" -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
    log_message "Cleared logs older than 7 days"
}

# Function to cleanup downloads
cleanup_downloads() {
    log_message "Starting downloads cleanup..."

    # Clear downloads older than 30 days
    local old_files=$(find "$HOME/Downloads" -type f -mtime +30 2>/dev/null | wc -l)
    find "$HOME/Downloads" -type f -mtime +30 -delete 2>/dev/null || true
    log_message "Removed $old_files old files from Downloads"
}

# Function to cleanup temporary files
cleanup_temp() {
    log_message "Starting temporary files cleanup..."

    # Clear temporary files
    rm -rf /tmp/* 2>/dev/null || true
    rm -rf /var/tmp/* 2>/dev/null || true

    # Clear trash
    rm -rf "$HOME/.Trash/"* 2>/dev/null || true

    log_message "Cleared temporary files and trash"
}

# Function to cleanup development files
cleanup_dev() {
    log_message "Starting development files cleanup..."

    # Clean node_modules in current directory if exists
    if [ -d "node_modules" ]; then
        local size=$(du -sh "node_modules" 2>/dev/null | cut -f1)
        rm -rf node_modules 2>/dev/null || true
        log_message "Removed node_modules (was: $size)"
    fi

    # Clean frontend build artifacts
    if [ -d "frontend/.next" ]; then
        rm -rf frontend/.next 2>/dev/null || true
        log_message "Cleared frontend build artifacts"
    fi

    if [ -d "frontend/node_modules" ]; then
        rm -rf frontend/node_modules 2>/dev/null || true
        log_message "Cleared frontend node_modules"
    fi
}

# Function to find large files
find_large_files() {
    log_message "Scanning for large files (>100MB)..."

    echo "Large files (>100MB):" >> "$HOME/large-files-report.txt"
    find "$HOME" -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr >> "$HOME/large-files-report.txt"

    local large_count=$(find "$HOME" -type f -size +100M 2>/dev/null | wc -l)
    log_message "Found $large_count large files. Report saved to $HOME/large-files-report.txt"

    if [ $large_count -gt 0 ]; then
        send_notification "Large Files Found" "Found $large_count files >100MB. Check $HOME/large-files-report.txt"
    fi
}

# Function to check disk health
check_disk_health() {
    log_message "Checking disk health..."

    # Check disk for errors
    if command -v diskutil &> /dev/null; then
        diskutil verifyVolume / >> "$HOME/disk-health-report.txt" 2>&1 || true
        log_message "Disk health check completed. Report saved to $HOME/disk-health-report.txt"
    fi
}

# Main cleanup function
perform_cleanup() {
    local usage=$1
    log_message "Current disk usage: ${usage}%"

    if [ $usage -gt $CRITICAL_THRESHOLD ]; then
        log_message "CRITICAL: Disk usage above ${CRITICAL_THRESHOLD}% - Performing aggressive cleanup"
        send_notification "Critical Disk Space" "Disk usage at ${usage}%. Performing emergency cleanup."

        cleanup_caches
        cleanup_logs
        cleanup_downloads
        cleanup_temp
        cleanup_dev

    elif [ $usage -gt $ALERT_THRESHOLD ]; then
        log_message "WARNING: Disk usage above ${ALERT_THRESHOLD}% - Performing standard cleanup"
        send_notification "Low Disk Space" "Disk usage at ${usage}%. Performing cleanup."

        cleanup_caches
        cleanup_logs
        cleanup_temp

    else
        log_message "Disk usage normal (${usage}%) - Performing light maintenance"
        cleanup_logs
        cleanup_temp
    fi
}

# Main execution
log_message "=== Automated Space Management Started ==="

# Get current disk usage
CURRENT_USAGE=$(get_disk_usage)
log_message "Initial disk usage: ${CURRENT_USAGE}%"

# Perform cleanup based on usage
perform_cleanup $CURRENT_USAGE

# Get final disk usage
FINAL_USAGE=$(get_disk_usage)
log_message "Final disk usage: ${FINAL_USAGE}%"

# Calculate space recovered
SPACE_RECOVERED=$((CURRENT_USAGE - FINAL_USAGE))
if [ $SPACE_RECOVERED -gt 0 ]; then
    log_message "Space recovered: ${SPACE_RECOVERED}%"
    send_notification "Space Cleanup Complete" "Recovered ${SPACE_RECOVERED}% disk space. Current usage: ${FINAL_USAGE}%"
fi

# Perform additional maintenance tasks
find_large_files
check_disk_health

# Display summary
echo ""
echo "=== SPACE MANAGEMENT SUMMARY ==="
echo "Completed at: $TIMESTAMP"
echo "Initial usage: ${CURRENT_USAGE}%"
echo "Final usage: ${FINAL_USAGE}%"
if [ $SPACE_RECOVERED -gt 0 ]; then
    echo "Space recovered: ${SPACE_RECOVERED}%"
fi
echo "Log file: $LOG_FILE"
echo "Large files report: $HOME/large-files-report.txt"
echo "Disk health report: $HOME/disk-health-report.txt"
echo "=================================="

log_message "=== Automated Space Management Completed ==="

# Setup cron job for daily execution
setup_cron_job() {
    log_message "Setting up daily cron job..."

    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "auto-space-manager.sh"; then
        # Add daily execution at 2 AM
        (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/auto-space-manager.sh") | crontab -
        log_message "Daily cron job scheduled for 2:00 AM"
    else
        log_message "Cron job already exists"
    fi
}

# Setup cron job
setup_cron_job

log_message "Automated space management setup completed."
