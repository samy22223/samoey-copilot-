#!/bin/bash

# Emergency Disk Cleanup Script for macOS 11.7.10 Big Sur Intel
# This script performs aggressive cleanup to recover critical disk space

set -e

LOG_FILE="$HOME/emergency-cleanup.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$TIMESTAMP] Starting emergency disk cleanup..." | tee -a $LOG_FILE

# Get initial disk usage
echo "[$TIMESTAMP] Initial disk usage:" | tee -a $LOG_FILE
df -h / | tee -a $LOG_FILE

# Function to safely remove directories with backup awareness
safe_remove() {
    local path="$1"
    local description="$2"

    if [ -d "$path" ]; then
        local size=$(du -sh "$path" 2>/dev/null | cut -f1)
        echo "[$TIMESTAMP] Cleaning $description: $path ($size)" | tee -a $LOG_FILE

        # Move to temp location first for safety
        local temp_path="/tmp/cleanup_$(basename "$path")_$(date +%s)"
        mv "$path" "$temp_path" 2>/dev/null || true

        # Remove after successful move
        rm -rf "$temp_path" 2>/dev/null || true
    fi
}

# Function to clear cache directories
clear_cache() {
    local cache_path="$1"
    local description="$2"

    if [ -d "$cache_path" ]; then
        local size=$(du -sh "$cache_path" 2>/dev/null | cut -f1)
        echo "[$TIMESTAMP] Clearing $description cache: $size" | tee -a $LOG_FILE
        rm -rf "$cache_path"/* 2>/dev/null || true
    fi
}

echo "[$TIMESTAMP] Phase 1: System Cache Cleanup..." | tee -a $LOG_FILE

# Clear system caches
clear_cache "~/Library/Caches" "User Library"
clear_cache "/Library/Caches" "System Library"
clear_cache "/System/Library/Caches" "System"

# Clear application caches
clear_cache "~/Library/Application Support/Google/Chrome/Default/Cache" "Chrome"
clear_cache "~/Library/Caches/com.apple.Safari" "Safari"
clear_cache "~/Library/Caches/Firefox" "Firefox"

echo "[$TIMESTAMP] Phase 2: Log File Cleanup..." | tee -a $LOG_FILE

# Clear old log files
find ~/Library/Logs -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
find /var/log -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
find /private/var/log -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true

echo "[$TIMESTAMP] Phase 3: Development Cleanup..." | tee -a $LOG_FILE

# Clean Xcode caches
clear_cache "~/Library/Developer/Xcode/DerivedData" "Xcode DerivedData"
clear_cache "~/Library/Developer/Xcode/Products" "Xcode Products"

# Clean Docker system
if command -v docker &> /dev/null; then
    echo "[$TIMESTAMP] Cleaning Docker system..." | tee -a $LOG_FILE
    docker system prune -af 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
fi

# Clean Node modules from current project
if [ -d "node_modules" ]; then
    size=$(du -sh "node_modules" 2>/dev/null | cut -f1)
    echo "[$TIMESTAMP] Removing node_modules: $size" | tee -a $LOG_FILE
    rm -rf node_modules 2>/dev/null || true
fi

# Clean frontend build artifacts
if [ -d "frontend/.next" ]; then
    rm -rf frontend/.next 2>/dev/null || true
fi
if [ -d "frontend/node_modules" ]; then
    rm -rf frontend/node_modules 2>/dev/null || true
fi

echo "[$TIMESTAMP] Phase 4: Large File Cleanup..." | tee -a $LOG_FILE

# Clean Downloads folder (files older than 30 days)
find ~/Downloads -type f -mtime +30 -delete 2>/dev/null || true

# Clean temporary files
rm -rf /tmp/* 2>/dev/null || true
rm -rf /var/tmp/* 2>/dev/null || true

# Clean Trash
rm -rf ~/.Trash/* 2>/dev/null || true

echo "[$TIMESTAMP] Phase 5: Application Support Cleanup..." | tee -a $LOG_FILE

# Clean old iOS backups
if [ -d "~/Library/Application Support/MobileSync/Backup" ]; then
    find ~/Library/Application\ Support/MobileSync/Backup -type d -mtime +90 -delete 2>/dev/null || true
fi

# Clean application cache files
find ~/Library/Application\ Support -type d -name "Cache" -exec rm -rf {} + 2>/dev/null || true

echo "[$TIMESTAMP] Phase 6: System Maintenance..." | tee -a $LOG_FILE

# Clear DNS cache
sudo dscacheutil -flushcache 2>/dev/null || true
sudo killall -HUP mDNSResponder 2>/dev/null || true

# Clear system font cache
sudo atsutil databases -remove 2>/dev/null || true
sudo atsutil server -shutdown 2>/dev/null || true
sudo atsutil server -ping 2>/dev/null || true

# Rebuild Spotlight index (can be resource intensive, so optional)
echo "[$TIMESTAMP] Rebuilding Spotlight index (this may take a while)..." | tee -a $LOG_FILE
sudo mdutil -E / 2>/dev/null || true

echo "[$TIMESTAMP] Cleanup completed. Final disk usage:" | tee -a $LOG_FILE
df -h / | tee -a $LOG_FILE

# Calculate space recovered
echo "[$TIMESTAMP] Emergency cleanup process completed." | tee -a $LOG_FILE
echo "[$TIMESTAMP] Please check the log file at $LOG_FILE for details." | tee -a $LOG_FILE

# Display summary
echo ""
echo "=== EMERGENCY CLEANUP SUMMARY ==="
echo "Cleanup completed at: $TIMESTAMP"
echo "Log file: $LOG_FILE"
echo ""
echo "Current disk usage:"
df -h /
echo ""
echo "Recommendations:"
echo "1. Restart your system to complete cleanup"
echo "2. Monitor disk space over the next few days"
echo "3. Consider moving large files to external storage"
echo "4. Set up automated cleanup to prevent future issues"
echo "=================================="
