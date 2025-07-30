#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Pinnacle Copilot Security System...${NC}"

# Function to check if a container is running
check_container() {
    if docker ps | grep -q "$1"; then
        echo -e "${GREEN}✓ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 is not running${NC}"
        return 1
    fi
}

# Function to start a service
start_service() {
    echo -e "${YELLOW}Starting $1...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.security.yml up -d $1
}

# Create required directories
echo "Creating required directories..."
mkdir -p logs/security
mkdir -p monitoring/grafana/dashboards
mkdir -p data/redis
mkdir -p data/prometheus
mkdir -p data/grafana

# Check environment files
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.security...${NC}"
    cp .env.security .env
fi

# Start core security services
echo "Starting security infrastructure..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml up -d redis prometheus grafana alertmanager

# Wait for core services
echo "Waiting for core services to be ready..."
sleep 10

# Check core services
services=("redis" "prometheus" "grafana" "alertmanager")
all_running=true

for service in "${services[@]}"; do
    if ! check_container "pinnacle-copilot_${service}_1"; then
        all_running=false
        echo -e "${RED}Error: $service failed to start${NC}"
        docker logs "pinnacle-copilot_${service}_1"
    fi
done

if [ "$all_running" = false ]; then
    echo -e "${RED}Some core services failed to start. Check the logs above.${NC}"
    exit 1
fi

# Start application with security
echo "Starting application with security features..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml up -d security-api

# Start monitoring components
echo "Starting monitoring components..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml up -d filebeat elastic kibana wazuh

# Initialize security database if needed
echo "Initializing security database..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml exec security-api python -c "
from database import init_db
init_db()
"

# Start fail2ban
echo "Starting fail2ban service..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml up -d fail2ban

# Final checks
echo "Performing final checks..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml ps

# Check application health
echo "Checking application health..."
sleep 5
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Application is healthy${NC}"
else
    echo -e "${RED}✗ Application health check failed${NC}"
fi

# Import Grafana dashboards
echo "Importing Grafana dashboards..."
curl -s -X POST -H "Content-Type: application/json" -d @monitoring/grafana/dashboards/security_overview.json http://admin:admin@localhost:3000/api/dashboards/db

# Start security monitoring
echo "Starting security monitoring..."
docker-compose -f docker-compose.yml -f docker-compose.security.yml logs -f security-api prometheus alertmanager | grep -E "security|threat|attack" &

echo -e "${GREEN}Security system startup complete!${NC}"
echo "Security dashboard: http://localhost:3000/d/security/security-overview"
echo "Alertmanager: http://localhost:9093"
echo "Prometheus: http://localhost:9090"
echo "Kibana: http://localhost:5601"

# Create a status file
cat > logs/security/status.txt << EOF
Security System Status:
Started: $(date)
Environment: $(grep APP_ENV .env | cut -d '=' -f2)
Core Services: Running
Monitoring: Active
Security Level: $(grep SECURITY_THREAT_LEVEL_THRESHOLD .env | cut -d '=' -f2)
EOF

exit 0
