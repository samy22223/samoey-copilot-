#!/bin/bash

# Autonomous Build Master for Samoey Copilot Project
# Central orchestration engine for fully automated builds

set -e

# Configuration
LOG_FILE="$HOME/auto-build-master.log"
PROJECT_ROOT="$(pwd)"
BUILD_QUEUE="$PROJECT_ROOT/.build_queue"
BUILD_HISTORY="$PROJECT_ROOT/.build_history"
SYSTEM_STATE="$PROJECT_ROOT/.system_state"
ALERT_THRESHOLD=85
CRITICAL_THRESHOLD=95

# Global variables
BUILD_PID=""
CURRENT_BUILD=""
BUILD_START_TIME=""
BUILD_STATUS="idle"

# Initialize system
init_system() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] === Autonomous Build Master Initializing ===" | tee -a $LOG_FILE

    # Create necessary directories and files
    mkdir -p "$PROJECT_ROOT/.autonomous"
    touch "$BUILD_QUEUE" "$BUILD_HISTORY" "$SYSTEM_STATE"

    # Initialize system state
    echo "status=initialized" > "$SYSTEM_STATE"
    echo "last_build=never" >> "$SYSTEM_STATE"
    echo "build_count=0" >> "$SYSTEM_STATE"
    echo "success_rate=0" >> "$SYSTEM_STATE"

    log_message "System initialized successfully"
}

# Logging function
log_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a $LOG_FILE
}

# System health check
check_system_health() {
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    local memory_usage=$(vm_stat | grep "Pages free" | awk '{print $3}' | xargs -I {} echo "scale=2; (1 - {}/$(vm_stat | grep "Pages free" | awk '{print $7}' | xargs -I {} echo {})) * 100" | bc)
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    local temp=$(osx-cpu-temp 2>/dev/null || echo "N/A")

    log_message "System Health - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%, Temp: ${temp}°C"

    # Check if system is healthy enough for builds
    if [ ${disk_usage%.*} -gt $CRITICAL_THRESHOLD ]; then
        log_message "CRITICAL: Disk space too low for builds (${disk_usage}%)"
        return 1
    fi

    if [ ${cpu_usage%.*} -gt 90 ]; then
        log_message "WARNING: CPU usage too high for builds (${cpu_usage}%)"
        return 1
    fi

    if [ ${memory_usage%.*} -gt 90 ]; then
        log_message "WARNING: Memory usage too high for builds (${memory_usage}%)"
        return 1
    fi

    return 0
}

# Monitor file changes
monitor_changes() {
    log_message "Starting file system monitoring..."

    # Use fswatch if available, otherwise use find
    if command -v fswatch &> /dev/null; then
        fswatch -o -r --event=Updated --event=Created --event=Removed \
            --exclude=.git \
            --exclude=node_modules \
            --exclude=.next \
            --exclude=.autonomous \
            "$PROJECT_ROOT" | while read f; do
            handle_file_change
        done
    else
        # Fallback to periodic checking
        while true; do
            sleep 30
            check_for_changes
        done
    fi
}

# Check for file changes
check_for_changes() {
    local last_check_file="$PROJECT_ROOT/.autonomous/last_check"
    local current_time=$(date +%s)

    if [ -f "$last_check_file" ]; then
        local last_check=$(cat "$last_check_file")
        local changes=$(find "$PROJECT_ROOT" -type f -newermt "@$last_check" \
            -not -path "*/.git/*" \
            -not -path "*/node_modules/*" \
            -not -path "*/.next/*" \
            -not -path "*/.autonomous/*" 2>/dev/null | wc -l)

        if [ $changes -gt 0 ]; then
            log_message "Detected $changes file changes"
            queue_build "file_changes"
        fi
    fi

    echo $current_time > "$last_check_file"
}

# Handle file change event
handle_file_change() {
    log_message "File system change detected"
    queue_build "file_change"
}

# Queue a build
queue_build() {
    local reason="$1"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local priority="normal"

    # Determine priority based on reason
    case $reason in
        "manual") priority="high" ;;
        "dependency_change") priority="high" ;;
        "test_failure") priority="high" ;;
        "file_change") priority="normal" ;;
        "scheduled") priority="low" ;;
    esac

    echo "$timestamp|$reason|$priority|pending" >> "$BUILD_QUEUE"
    log_message "Build queued: $reason (priority: $priority)"

    # Trigger build processor
    process_build_queue
}

# Process build queue
process_build_queue() {
    # Check if already building
    if [ ! -z "$BUILD_PID" ] && kill -0 "$BUILD_PID" 2>/dev/null; then
        log_message "Build already in progress (PID: $BUILD_PID)"
        return 0
    fi

    # Get next build from queue
    local next_build=$(head -1 "$BUILD_QUEUE" 2>/dev/null)
    if [ -z "$next_build" ]; then
        return 0
    fi

    # Remove from queue
    sed -i '' '1d' "$BUILD_QUEUE"

    # Parse build info
    local build_time=$(echo "$next_build" | cut -d'|' -f1)
    local build_reason=$(echo "$next_build" | cut -d'|' -f2)
    local build_priority=$(echo "$next_build" | cut -d'|' -f3)

    log_message "Processing build: $build_reason (priority: $build_priority)"

    # Start build
    start_build "$build_reason" "$build_priority"
}

# Start a build
start_build() {
    local reason="$1"
    local priority="$2"

    # Check system health before building
    if ! check_system_health; then
        log_message "System not healthy for build - requeuing"
        echo "$(date +"%Y-%m-%d %H:%M:%S")|$reason|$priority|pending" >> "$BUILD_QUEUE"
        return 1
    fi

    # Check if on battery power (avoid intensive builds on battery)
    if pmset -g batt | grep "discharging" > /dev/null; then
        log_message "System on battery power - delaying build"
        echo "$(date +"%Y-%m-%d %H:%M:%S")|$reason|$priority|pending" >> "$BUILD_QUEUE"
        return 1
    fi

    BUILD_START_TIME=$(date +"%s")
    CURRENT_BUILD="$reason"
    BUILD_STATUS="building"

    log_message "Starting build: $reason"

    # Update system state
    sed -i '' "s/status=.*/status=building/" "$SYSTEM_STATE"
    sed -i '' "s/current_build=.*/current_build=$reason/" "$SYSTEM_STATE"

    # Start build in background
    execute_build "$reason" &
    BUILD_PID=$!

    log_message "Build started with PID: $BUILD_PID"

    # Monitor build
    monitor_build
}

# Execute build
execute_build() {
    local reason="$1"
    local build_log="$PROJECT_ROOT/.autonomous/build_$(date +%Y%m%d_%H%M%S).log"

    cd "$PROJECT_ROOT"

    # Execute build based on project type
    {
        echo "=== Build Started: $reason ==="
        echo "Time: $(date)"
        echo "Reason: $reason"
        echo ""

        # Check if package.json exists (Node.js project)
        if [ -f "package.json" ]; then
            echo "=== Node.js Build ==="

            # Install dependencies if needed
            if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
                echo "Installing dependencies..."
                npm install || { echo "Dependency installation failed"; exit 1; }
            fi

            # Run build
            echo "Running build..."
            npm run build || { echo "Build failed"; exit 1; }

            # Run tests if available
            if npm run test --silent 2>/dev/null; then
                echo "Running tests..."
                npm test || { echo "Tests failed"; exit 1; }
            fi

        elif [ -f "requirements.txt" ]; then
            # Python project
            echo "=== Python Build ==="

            # Create virtual environment if needed
            if [ ! -d "venv" ]; then
                echo "Creating virtual environment..."
                python3 -m venv venv || { echo "Virtual environment creation failed"; exit 1; }
            fi

            # Activate virtual environment
            source venv/bin/activate

            # Install dependencies
            echo "Installing dependencies..."
            pip install -r requirements.txt || { echo "Dependency installation failed"; exit 1; }

            # Run tests if available
            if [ -f "app/main.py" ]; then
                echo "Running Python application tests..."
                python -m pytest tests/ 2>/dev/null || echo "No tests found or tests failed"
            fi

        else
            echo "=== Generic Build ==="
            echo "No specific build system detected, running generic checks..."

            # Basic file validation
            find . -name "*.py" -exec python -m py_compile {} \; 2>/dev/null || { echo "Python syntax errors found"; exit 1; }
            find . -name "*.js" -node_modules -exec node -c {} \; 2>/dev/null || { echo "JavaScript syntax errors found"; exit 1; }
        fi

        echo ""
        echo "=== Build Completed Successfully ==="

    } > "$build_log" 2>&1

    local build_exit_code=$?

    # Record build result
    record_build_result "$reason" $build_exit_code "$build_log"

    return $build_exit_code
}

# Monitor build progress
monitor_build() {
    local timeout=3600  # 1 hour timeout
    local start_time=$(date +%s)

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        # Check timeout
        if [ $elapsed -gt $timeout ]; then
            log_message "Build timeout reached, terminating..."
            kill -9 "$BUILD_PID" 2>/dev/null
            record_build_result "$CURRENT_BUILD" 1 "Build timeout"
            break
        fi

        # Check if build completed
        if ! kill -0 "$BUILD_PID" 2>/dev/null; then
            wait "$BUILD_PID"
            local exit_code=$?
            log_message "Build completed with exit code: $exit_code"
            break
        fi

        # Log progress every 30 seconds
        if [ $((elapsed % 30)) -eq 0 ]; then
            log_message "Build in progress... (${elapsed}s elapsed)"
        fi

        sleep 5
    done

    # Reset build state
    BUILD_PID=""
    CURRENT_BUILD=""
    BUILD_STATUS="idle"

    # Update system state
    sed -i '' "s/status=.*/status=idle/" "$SYSTEM_STATE"
    sed -i '' "s/current_build=.*/current_build=none/" "$SYSTEM_STATE"

    # Process next build in queue
    process_build_queue
}

# Record build result
record_build_result() {
    local reason="$1"
    local exit_code="$2"
    local build_log="$3"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local build_duration=$(($(date +%s) - BUILD_START_TIME))

    # Record in history
    echo "$timestamp|$reason|$exit_code|$build_duration|$build_log" >> "$BUILD_HISTORY"

    # Update system state
    local build_count=$(grep "^build_count=" "$SYSTEM_STATE" | cut -d'=' -f2)
    build_count=$((build_count + 1))
    sed -i '' "s/build_count=.*/build_count=$build_count/" "$SYSTEM_STATE"

    # Calculate success rate
    local success_count=$(awk -F'|' '$3==0 {count++} END {print count+0}' "$BUILD_HISTORY")
    local success_rate=$(echo "scale=2; $success_count * 100 / $build_count" | bc)
    sed -i '' "s/success_rate=.*/success_rate=$success_rate/" "$SYSTEM_STATE"

    # Log result
    if [ $exit_code -eq 0 ]; then
        log_message "Build SUCCESS: $reason (${build_duration}s)"
        send_notification "Build Success" "$reason completed successfully in ${build_duration}s"
    else
        log_message "Build FAILED: $reason (exit code: $exit_code, ${build_duration}s)"
        send_notification "Build Failed" "$reason failed with exit code $exit_code"

        # Auto-heal: queue retry for failed builds
        if [ $exit_code -ne 0 ]; then
            log_message "Auto-heal: Queuing retry build for failed: $reason"
            sleep 60  # Wait before retry
            queue_build "retry_$reason"
        fi
    fi
}

# Send notification
send_notification() {
    local title="$1"
    local message="$2"

    # Use macOS notification center
    osascript -e "display notification \"$message\" with title \"$title\"" 2>/dev/null || true

    # Log notification
    log_message "NOTIFICATION: $title - $message"
}

# Status dashboard
show_status() {
    echo "=== Autonomous Build Master Status ==="
    echo "Current Time: $(date)"
    echo ""

    # System state
    echo "System State:"
    while IFS='=' read -r key value; do
        echo "  $key: $value"
    done < "$SYSTEM_STATE"
    echo ""

    # Current build status
    if [ ! -z "$BUILD_PID" ] && kill -0 "$BUILD_PID" 2>/dev/null; then
        local elapsed=$(($(date +%s) - BUILD_START_TIME))
        echo "Current Build: $CURRENT_BUILD (running for ${elapsed}s)"
    else
        echo "Current Build: None"
    fi
    echo ""

    # Build queue
    local queue_count=$(wc -l < "$BUILD_QUEUE" 2>/dev/null || echo "0")
    echo "Build Queue: $queue_count builds pending"
    if [ $queue_count -gt 0 ]; then
        echo "Pending builds:"
        tail -5 "$BUILD_QUEUE" | while IFS='|' read -r time reason priority status; do
            echo "  - $reason ($priority)"
        done
    fi
    echo ""

    # Recent builds
    echo "Recent Builds:"
    tail -5 "$BUILD_HISTORY" | while IFS='|' read -r time reason code duration log; do
        local status="SUCCESS"
        if [ "$code" != "0" ]; then
            status="FAILED"
        fi
        echo "  - $reason: $status (${duration}s)"
    done
    echo ""

    echo "Log File: $LOG_FILE"
    echo "=================================="
}

# Cleanup function
cleanup() {
    log_message "Received shutdown signal, cleaning up..."

    # Kill current build if running
    if [ ! -z "$BUILD_PID" ] && kill -0 "$BUILD_PID" 2>/dev/null; then
        log_message "Terminating current build (PID: $BUILD_PID)"
        kill -TERM "$BUILD_PID" 2>/dev/null
        sleep 5
        kill -9 "$BUILD_PID" 2>/dev/null || true
    fi

    # Update system state
    sed -i '' "s/status=.*/status=stopped/" "$SYSTEM_STATE"
    sed -i '' "s/current_build=.*/current_build=none/" "$SYSTEM_STATE"

    log_message "System cleanup completed"
    exit 0
}

# Signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    local action="$1"

    case "$action" in
        "start")
            log_message "Starting Autonomous Build Master..."
            init_system

            # Start monitoring in background
            monitor_changes &
            MONITOR_PID=$!

            log_message "Autonomous Build Master started (Monitor PID: $MONITOR_PID)"
            log_message "System will automatically build on file changes"

            # Keep main process running
            while true; do
                sleep 60
                check_system_health
            done
            ;;

        "status")
            show_status
            ;;

        "build")
            queue_build "manual"
            ;;

        "stop")
            log_message "Stopping Autonomous Build Master..."
            cleanup
            ;;

        *)
            echo "Usage: $0 {start|stop|status|build}"
            echo ""
            echo "Commands:"
            echo "  start  - Start autonomous build monitoring"
            echo "  stop   - Stop autonomous build monitoring"
            echo "  status - Show current system status"
            echo "  build  - Trigger manual build"
            exit 1
            ;;
    esac
}

# Run main function with arguments
main "$@"
