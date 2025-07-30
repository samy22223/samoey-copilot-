#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check component health
check_health() {
    local component=$1
    local port=$2
    local endpoint=$3
    
    if curl -s "http://localhost:${port}${endpoint}" > /dev/null; then
        echo -e "${GREEN}✓ $component is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ $component is not responding${NC}"
        return 1
    fi
}

# Function to restart component
restart_component() {
    local component=$1
    echo -e "${YELLOW}Restarting $component...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.security.yml restart $component
    sleep 5
}

# Function to check logs for security issues
check_security_logs() {
    local time_window=$1
    echo "Checking security logs for the last $time_window..."
    
    # Check application logs
    suspicious=$(docker-compose -f docker-compose.yml -f docker-compose.security.yml logs --since $time_window | grep -iE "attack|threat|suspicious|violation|blocked")
    if [ ! -z "$suspicious" ]; then
        echo -e "${RED}Security Issues Found:${NC}"
        echo "$suspicious"
        
        # Send alert if configured
        if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
            curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"Security Alert: Suspicious activity detected\"}" $SLACK_WEBHOOK_URL
        fi
    else
        echo -e "${GREEN}No immediate security threats detected${NC}"
    fi
}

# Function to perform security audit
perform_security_audit() {
    echo "Performing security audit..."
    
    # Check component status
    components=(
        "security-api:8000:/api/health"
        "prometheus:9090/-/healthy"
        "alertmanager:9093/-/healthy"
        "grafana:3000/api/health"
    )
    
    for comp in "${components[@]}"; do
        IFS=: read -r name port endpoint <<< "$comp"
        check_health "$name" "$port" "$endpoint"
        if [ $? -ne 0 ]; then
            restart_component "$name"
        fi
    done
    
    # Check Redis security
    echo "Checking Redis security..."
    redis_status=$(docker-compose -f docker-compose.yml -f docker-compose.security.yml exec -T redis redis-cli ping)
    if [ "$redis_status" != "PONG" ]; then
        echo -e "${RED}Redis is not responding properly${NC}"
        restart_component "redis"
    fi
    
    # Check security metrics
    echo "Checking security metrics..."
    threat_level=$(curl -s http://localhost:9090/api/v1/query?query=security_threat_level | grep -o '"value":\[[0-9.]*\]' | cut -d'[' -f2 | cut -d']' -f1)
    if (( $(echo "$threat_level > 3" | bc -l) )); then
        echo -e "${RED}High threat level detected: $threat_level${NC}"
        # Trigger enhanced monitoring
        docker-compose -f docker-compose.yml -f docker-compose.security.yml exec security-api python -c "
from backend.core.security_orchestrator import security_orchestrator
import asyncio
asyncio.run(security_orchestrator._adjust_security_level($threat_level))
"
    fi
}

# Function to check and repair file permissions
check_permissions() {
    echo "Checking file permissions..."
    
    # Secure sensitive directories
    directories=(
        "logs/security"
        "config"
        "data/redis"
        ".env"
        ".env.security"
    )
    
    for dir in "${directories[@]}"; do
        if [ -e "$dir" ]; then
            chmod -R 600 "$dir"
            echo -e "${GREEN}✓ Secured $dir${NC}"
        fi
    done
}

# Main monitoring loop
monitor_security() {
    while true; do
        echo "=== Security Monitor Running at $(date) ==="
        
        # Perform security checks
        check_security_logs "5m"
        perform_security_audit
        check_permissions
        
        # Update status
        cat > logs/security/status.txt << EOF
Last Check: $(date)
Threat Level: $threat_level
Security Status: Active
Monitoring: Running
EOF
        
        # Wait before next check
        sleep 300 # 5 minutes
    done
}

# Start monitoring
echo -e "${GREEN}Starting security monitoring...${NC}"
monitor_security
