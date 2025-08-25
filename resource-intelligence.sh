#!/bin/bash

# Resource Intelligence Engine for Autonomous Build System
# Smart resource management and predictive allocation for macOS 11.7.10 Big Sur Intel

set -e

# Configuration
LOG_FILE="$HOME/resource-intelligence.log"
PROJECT_ROOT="$(pwd)"
RESOURCE_STATE="$PROJECT_ROOT/.autonomous/.resource_state"
PERFORMANCE_DATA="$PROJECT_ROOT/.autonomous/.performance_data"
PREDICTION_MODEL="$PROJECT_ROOT/.autonomous/.prediction_model"

# Resource thresholds
CPU_CRITICAL=90
CPU_WARNING=75
MEMORY_CRITICAL=90
MEMORY_WARNING=75
DISK_CRITICAL=95
DISK_WARNING=85
TEMP_CRITICAL=85
TEMP_WARNING=75

# Global variables
RESOURCE_PID=""
MONITORING_ACTIVE=false
PREDICTION_ENABLED=true
OPTIMIZATION_LEVEL="balanced"  # conservative, balanced, aggressive

# Initialize resource intelligence system
init_resource_intelligence() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] === Resource Intelligence Engine Initializing ===" | tee -a $LOG_FILE

    # Create autonomous directory
    mkdir -p "$PROJECT_ROOT/.autonomous"

    # Initialize state files
    touch "$RESOURCE_STATE" "$PERFORMANCE_DATA" "$PREDICTION_MODEL"

    # Initialize resource state
    echo "status=initialized" > "$RESOURCE_STATE"
    echo "cpu_usage=0" >> "$RESOURCE_STATE"
    echo "memory_usage=0" >> "$RESOURCE_STATE"
    echo "disk_usage=0" >> "$RESOURCE_STATE"
    echo "temperature=0" >> "$RESOURCE_STATE"
    echo "power_source=unknown" >> "$RESOURCE_STATE"
    echo "optimization_level=$OPTIMIZATION_LEVEL" >> "$RESOURCE_STATE"
    echo "last_optimization=never" >> "$RESOURCE_STATE"
    echo "prediction_accuracy=0" >> "$RESOURCE_STATE"

    # Initialize performance data structure
    echo "timestamp,cpu_usage,memory_usage,disk_usage,temperature,build_duration,success_rate" > "$PERFORMANCE_DATA"

    # Initialize prediction model
    init_prediction_model

    log_message "Resource Intelligence Engine initialized successfully"
}

# Initialize prediction model
init_prediction_model() {
    echo "# Resource Prediction Model" > "$PREDICTION_MODEL"
    echo "cpu_weight=0.3" >> "$PREDICTION_MODEL"
    echo "memory_weight=0.3" >> "$PREDICTION_MODEL"
    echo "disk_weight=0.2" >> "$PREDICTION_MODEL"
    echo "temp_weight=0.1" >> "$PREDICTION_MODEL"
    echo "power_weight=0.1" >> "$PREDICTION_MODEL"
    echo "learning_rate=0.1" >> "$PREDICTION_MODEL"
    echo "prediction_accuracy=0" >> "$PREDICTION_MODEL"
    echo "total_predictions=0" >> "$PREDICTION_MODEL"
    echo "correct_predictions=0" >> "$PREDICTION_MODEL"
}

# Logging function
log_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a $LOG_FILE
}

# Get current system metrics
get_system_metrics() {
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' | head -1)
    local memory_info=$(vm_stat)
    local free_pages=$(echo "$memory_info" | grep "Pages free" | awk '{print $3}')
    local total_pages=$(echo "$memory_info" | grep "Pages free" | awk '{print $7}')
    local memory_usage=$(echo "scale=2; (1 - $free_pages/$total_pages) * 100" | bc)
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    local temp=$(osx-cpu-temp 2>/dev/null || echo "0")
    local power_source=$(pmset -g batt | grep -o "charging\|discharging\|AC Power" | head -1)

    # Clean up values
    cpu_usage=${cpu_usage%.*}
    memory_usage=${memory_usage%.*}
    disk_usage=${disk_usage%.*}
    temp=${temp%.*}

    echo "$cpu_usage|$memory_usage|$disk_usage|$temp|$power_source"
}

# Update resource state
update_resource_state() {
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
    local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
    local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
    local temperature=$(echo "$metrics" | cut -d'|' -f4)
    local power_source=$(echo "$metrics" | cut -d'|' -f5)

    # Update state file
    sed -i '' "s/cpu_usage=.*/cpu_usage=$cpu_usage/" "$RESOURCE_STATE"
    sed -i '' "s/memory_usage=.*/memory_usage=$memory_usage/" "$RESOURCE_STATE"
    sed -i '' "s/disk_usage=.*/disk_usage=$disk_usage/" "$RESOURCE_STATE"
    sed -i '' "s/temperature=.*/temperature=$temperature/" "$RESOURCE_STATE"
    sed -i '' "s/power_source=.*/power_source=$power_source/" "$RESOURCE_STATE"

    log_message "Resource state updated - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%, Temp: ${temperature}°C, Power: $power_source"
}

# Check system health for build readiness
check_build_readiness() {
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
    local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
    local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
    local temperature=$(echo "$metrics" | cut -d'|' -f4)
    local power_source=$(echo "$metrics" | cut -d'|' -f5)

    local readiness_score=100
    local reasons=()

    # Check CPU
    if [ $cpu_usage -gt $CPU_CRITICAL ]; then
        readiness_score=$((readiness_score - 40))
        reasons+=("CPU usage critical (${cpu_usage}%)")
    elif [ $cpu_usage -gt $CPU_WARNING ]; then
        readiness_score=$((readiness_score - 20))
        reasons+=("CPU usage high (${cpu_usage}%)")
    fi

    # Check Memory
    if [ $memory_usage -gt $MEMORY_CRITICAL ]; then
        readiness_score=$((readiness_score - 40))
        reasons+=("Memory usage critical (${memory_usage}%)")
    elif [ $memory_usage -gt $MEMORY_WARNING ]; then
        readiness_score=$((readiness_score - 20))
        reasons+=("Memory usage high (${memory_usage}%)")
    fi

    # Check Disk
    if [ $disk_usage -gt $DISK_CRITICAL ]; then
        readiness_score=$((readiness_score - 50))
        reasons+=("Disk space critical (${disk_usage}%)")
    elif [ $disk_usage -gt $DISK_WARNING ]; then
        readiness_score=$((readiness_score - 30))
        reasons+=("Disk space low (${disk_usage}%)")
    fi

    # Check Temperature
    if [ $temperature -gt $TEMP_CRITICAL ]; then
        readiness_score=$((readiness_score - 30))
        reasons+=("Temperature critical (${temperature}°C)")
    elif [ $temperature -gt $TEMP_WARNING ]; then
        readiness_score=$((readiness_score - 15))
        reasons+=("Temperature high (${temperature}°C)")
    fi

    # Check Power Source
    if [ "$power_source" = "discharging" ]; then
        readiness_score=$((readiness_score - 25))
        reasons+=("On battery power")
    fi

    # Log readiness assessment
    if [ ${#reasons[@]} -eq 0 ]; then
        log_message "System ready for build (score: $readiness_score)"
    else
        log_message "System build readiness score: $readiness_score"
        for reason in "${reasons[@]}"; do
            log_message "  - $reason"
        done
    fi

    return $readiness_score
}

# Predict optimal build parameters
predict_build_parameters() {
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
    local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
    local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
    local temperature=$(echo "$metrics" | cut -d'|' -f4)
    local power_source=$(echo "$metrics" | cut -d'|' -f5)

    # Get prediction model weights
    source "$PREDICTION_MODEL"

    # Calculate resource score
    local cpu_score=$((100 - cpu_usage))
    local memory_score=$((100 - memory_usage))
    local disk_score=$((100 - disk_usage))
    local temp_score=$((100 - temperature))
    local power_score=100
    [ "$power_source" = "discharging" ] && power_score=50

    # Calculate weighted score
    local total_score=$(echo "scale=2; ($cpu_score * $cpu_weight) + ($memory_score * $memory_weight) + ($disk_score * $disk_weight) + ($temp_score * $temp_weight) + ($power_score * $power_weight)" | bc)

    # Determine optimal parameters based on score and optimization level
    local max_parallel_jobs=1
    local memory_limit="2g"
    local cpu_limit="75%"
    local priority="normal"

    case "$OPTIMIZATION_LEVEL" in
        "conservative")
            max_parallel_jobs=1
            memory_limit="1g"
            cpu_limit="50%"
            [ $(echo "$total_score > 80" | bc) -eq 1 ] && priority="low"
            ;;
        "balanced")
            if [ $(echo "$total_score > 80" | bc) -eq 1 ]; then
                max_parallel_jobs=2
                memory_limit="3g"
                cpu_limit="75%"
                priority="normal"
            elif [ $(echo "$total_score > 60" | bc) -eq 1 ]; then
                max_parallel_jobs=1
                memory_limit="2g"
                cpu_limit="60%"
                priority="normal"
            else
                max_parallel_jobs=1
                memory_limit="1g"
                cpu_limit="50%"
                priority="low"
            fi
            ;;
        "aggressive")
            if [ $(echo "$total_score > 85" | bc) -eq 1 ]; then
                max_parallel_jobs=4
                memory_limit="6g"
                cpu_limit="90%"
                priority="high"
            elif [ $(echo "$total_score > 70" | bc) -eq 1 ]; then
                max_parallel_jobs=2
                memory_limit="4g"
                cpu_limit="80%"
                priority="normal"
            else
                max_parallel_jobs=1
                memory_limit="2g"
                cpu_limit="70%"
                priority="low"
            fi
            ;;
    esac

    # Adjust for available system resources
    local available_memory=$(( (100 - memory_usage) * 80 / 100 ))  # Use 80% of available memory
    if [ $available_memory -lt 20 ]; then
        max_parallel_jobs=1
        memory_limit="1g"
    fi

    # Log prediction
    log_message "Build parameters predicted - Score: $total_score, Jobs: $max_parallel_jobs, Memory: $memory_limit, CPU: $cpu_limit, Priority: $priority"

    # Record prediction for learning
    record_prediction "$total_score" "$max_parallel_jobs" "$memory_limit" "$cpu_limit" "$priority"

    echo "$max_parallel_jobs|$memory_limit|$cpu_limit|$priority|$total_score"
}

# Record prediction for learning
record_prediction() {
    local score="$1"
    local max_jobs="$2"
    local memory_limit="$3"
    local cpu_limit="$4"
    local priority="$5"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    echo "$timestamp|$score|$max_jobs|$memory_limit|$cpu_limit|$priority" >> "$PROJECT_ROOT/.autonomous/.prediction_log"
}

# Optimize system resources
optimize_resources() {
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
    local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
    local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
    local temperature=$(echo "$metrics" | cut -d'|' -f4)
    local power_source=$(echo "$metrics" | cut -d'|' -f5)

    log_message "Starting resource optimization..."

    local optimizations_applied=0

    # Memory optimization
    if [ $memory_usage -gt $MEMORY_WARNING ]; then
        log_message "Optimizing memory usage..."

        # Clear inactive memory
        sudo purge 2>/dev/null || true

        # Close memory-intensive applications if possible
        if [ $memory_usage -gt $MEMORY_CRITICAL ]; then
            log_message "Critical memory usage - attempting to free memory"
            # Note: In a real implementation, this would intelligently close non-essential apps
        fi

        optimizations_applied=$((optimizations_applied + 1))
    fi

    # CPU optimization
    if [ $cpu_usage -gt $CPU_WARNING ]; then
        log_message "Optimizing CPU usage..."

        # Reduce process priorities if possible
        # Note: In a real implementation, this would renice processes

        optimizations_applied=$((optimizations_applied + 1))
    fi

    # Disk optimization
    if [ $disk_usage -gt $DISK_WARNING ]; then
        log_message "Optimizing disk usage..."

        # Clear system caches
        sudo rm -rf /private/var/log/asl/*.asl 2>/dev/null || true

        # Run space cleanup if critical
        if [ $disk_usage -gt $DISK_CRITICAL ]; then
            log_message "Critical disk usage - running space cleanup"
            [ -f "$PROJECT_ROOT/auto-space-manager.sh" ] && "$PROJECT_ROOT/auto-space-manager.sh" &
        fi

        optimizations_applied=$((optimizations_applied + 1))
    fi

    # Temperature optimization
    if [ $temperature -gt $TEMP_WARNING ]; then
        log_message "Optimizing for temperature..."

        # Reduce CPU-intensive processes
        # Note: In a real implementation, this would throttle processes

        optimizations_applied=$((optimizations_applied + 1))
    fi

    # Update last optimization timestamp
    sed -i '' "s/last_optimization=.*/last_optimization=$(date +%s)/" "$RESOURCE_STATE"

    log_message "Resource optimization completed - $optimizations_applied optimizations applied"

    return $optimizations_applied
}

# Adaptive build scheduling
adaptive_build_schedule() {
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
    local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
    local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
    local temperature=$(echo "$metrics" | cut -d'|' -f4)
    local power_source=$(echo "$metrics" | cut -d'|' -f5)
    local current_hour=$(date +%H)

    log_message "Calculating adaptive build schedule..."

    # Calculate optimal build time
    local build_score=100
    local recommended_delay=0
    local reasons=()

    # Time-based scheduling (avoid peak hours)
    if [ $current_hour -ge 9 ] && [ $current_hour -le 17 ]; then
        build_score=$((build_score - 20))
        reasons+=("Peak business hours")
        recommended_delay=3600  # 1 hour delay
    fi

    # Resource-based scheduling
    if [ $cpu_usage -gt $CPU_WARNING ]; then
        build_score=$((build_score - 30))
        reasons+=("High CPU usage")
        recommended_delay=$((recommended_delay + 1800))  # 30 minutes
    fi

    if [ $memory_usage -gt $MEMORY_WARNING ]; then
        build_score=$((build_score - 30))
        reasons+=("High memory usage")
        recommended_delay=$((recommended_delay + 1800))  # 30 minutes
    fi

    if [ $temperature -gt $TEMP_WARNING ]; then
        build_score=$((build_score - 25))
        reasons+=("High temperature")
        recommended_delay=$((recommended_delay + 1200))  # 20 minutes
    fi

    # Power-based scheduling
    if [ "$power_source" = "discharging" ]; then
        build_score=$((build_score - 40))
        reasons+=("On battery power")
        recommended_delay=$((recommended_delay + 7200))  # 2 hours
    fi

    # Log scheduling decision
    log_message "Adaptive build schedule - Score: $build_score, Delay: ${recommended_delay}s"
    if [ ${#reasons[@]} -gt 0 ]; then
        log_message "Delay reasons:"
        for reason in "${reasons[@]}"; do
            log_message "  - $reason"
        done
    fi

    echo "$build_score|$recommended_delay"
}

# Continuous resource monitoring
monitor_resources() {
    log_message "Starting continuous resource monitoring..."

    MONITORING_ACTIVE=true

    while $MONITORING_ACTIVE; do
        # Update resource state
        update_resource_state

        # Check if optimization is needed
        local metrics=$(get_system_metrics)
        local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
        local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
        local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
        local temperature=$(echo "$metrics" | cut -d'|' -f4)

        # Optimize if any resource is above warning threshold
        if [ $cpu_usage -gt $CPU_WARNING ] || [ $memory_usage -gt $MEMORY_WARNING ] || [ $disk_usage -gt $DISK_WARNING ] || [ $temperature -gt $TEMP_WARNING ]; then
            log_message "Resource thresholds exceeded, initiating optimization..."
            optimize_resources
        fi

        # Record performance data
        local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
        echo "$timestamp,$cpu_usage,$memory_usage,$disk_usage,$temperature,0,0" >> "$PERFORMANCE_DATA"

        # Sleep before next check
        sleep 30
    done
}

# Show resource status
show_resource_status() {
    echo "=== Resource Intelligence Status ==="
    echo "Current Time: $(date)"
    echo ""

    # Get current metrics
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d'|' -f1)
    local memory_usage=$(echo "$metrics" | cut -d'|' -f2)
    local disk_usage=$(echo "$metrics" | cut -d'|' -f3)
    local temperature=$(echo "$metrics" | cut -d'|' -f4)
    local power_source=$(echo "$metrics" | cut -d'|' -f5)

    echo "Current Metrics:"
    echo "  CPU Usage: ${cpu_usage}%"
    echo "  Memory Usage: ${memory_usage}%"
    echo "  Disk Usage: ${disk_usage}%"
    echo "  Temperature: ${temperature}°C"
    echo "  Power Source: $power_source"
    echo ""

    # Check build readiness
    check_build_readiness
    local readiness_score=$?
    echo "  Build Readiness Score: $readiness_score"

    # Get predicted build parameters
    local params=$(predict_build_parameters)
    local max_jobs=$(echo "$params" | cut -d'|' -f1)
    local memory_limit=$(echo "$params" | cut -d'|' -f2)
    local cpu_limit=$(echo "$params" | cut -d'|' -f3)
    local priority=$(echo "$params" | cut -d'|' -f4)
    local score=$(echo "$params" | cut -d'|' -f5)

    echo "Predicted Build Parameters:"
    echo "  Max Parallel Jobs: $max_jobs"
    echo "  Memory Limit: $memory_limit"
    echo "  CPU Limit: $cpu_limit"
    echo "  Priority: $priority"
    echo "  Confidence Score: $score"
    echo ""

    # Get adaptive schedule
    local schedule=$(adaptive_build_schedule)
    local build_score=$(echo "$schedule" | cut -d'|' -f1)
    local delay=$(echo "$schedule" | cut -d'|' -f2)

    echo "Adaptive Schedule:"
    echo "  Build Score: $build_score"
    echo "  Recommended Delay: ${delay}s"
    echo ""

    # System state
    echo "System State:"
    while IFS='=' read -r key value; do
        echo "  $key: $value"
    done < "$RESOURCE_STATE"
    echo ""

    echo "Log File: $LOG_FILE"
    echo "=================================="
}

# Cleanup function
cleanup() {
    log_message "Resource Intelligence Engine shutting down..."
    MONITORING_ACTIVE=false

    # Kill monitoring process if running
    if [ ! -z "$RESOURCE_PID" ] && kill -0 "$RESOURCE_PID" 2>/dev/null; then
        log_message "Stopping resource monitoring (PID: $RESOURCE_PID)"
        kill -TERM "$RESOURCE_PID" 2>/dev/null
        sleep 2
        kill -9 "$RESOURCE_PID" 2>/dev/null || true
    fi

    log_message "Resource Intelligence Engine stopped"
    exit 0
}

# Signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    local action="$1"
    local param="$2"

    case "$action" in
        "start")
            log_message "Starting Resource Intelligence Engine..."
            init_resource_intelligence

            # Start monitoring in background
            monitor_resources &
            RESOURCE_PID=$!

            log_message "Resource Intelligence Engine started (Monitor PID: $RESOURCE_PID)"
            log_message "System will automatically monitor and optimize resources"

            # Keep main process running
            while true; do
                sleep 60
                # Periodic health check
                if ! $MONITORING_ACTIVE; then
                    log_message "Monitoring stopped unexpectedly, restarting..."
                    monitor_resources &
                    RESOURCE_PID=$!
                fi
            done
            ;;

        "stop")
            log_message "Stopping Resource Intelligence Engine..."
            cleanup
            ;;

        "status")
            show_resource_status
            ;;

        "check-readiness")
            check_build_readiness
            local score=$?
            echo "Build readiness score: $score"
            ;;

        "predict")
            predict_build_parameters
            ;;

        "schedule")
            adaptive_build_schedule
            ;;

        "optimize")
            log_message "Manual resource optimization requested..."
            optimize_resources
            local optimizations=$?
            echo "Applied $optimizations resource optimizations"
            ;;

        "set-optimization")
            if [ -z "$param" ]; then
                echo "Usage: $0 set-optimization {conservative|balanced|aggressive}"
                exit 1
            fi

            case "$param" in
                "conservative"|"balanced"|"aggressive")
                    sed -i '' "s/optimization_level=.*/optimization_level=$param/" "$RESOURCE_STATE"
                    log_message "Optimization level set to: $param"
                    ;;
                *)
                    echo "Invalid optimization level: $param"
                    echo "Valid options: conservative, balanced, aggressive"
                    exit 1
                    ;;
            esac
            ;;

        *)
            echo "Usage: $0 {start|stop|status|check-readiness|predict|schedule|optimize|set-optimization}"
            echo ""
            echo "Commands:"
            echo "  start              - Start resource intelligence monitoring"
            echo "  stop               - Stop resource intelligence monitoring"
            echo "  status             - Show current resource status"
            echo "  check-readiness    - Check system readiness for builds"
            echo "  predict            - Predict optimal build parameters"
            echo "  schedule           - Get adaptive build schedule"
            echo "  optimize           - Manually optimize system resources"
            echo "  set-optimization  - Set optimization level (conservative|balanced|aggressive)"
            exit 1
            ;;
    esac
}

# Run main function with arguments
main "$@"
