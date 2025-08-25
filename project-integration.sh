#!/bin/bash
# Project Integration Script for Samoey Copilot Autonomous System

set -e

CONFIG_FILE=".autonomous-project-config.json"

show_status() {
    echo "=== Samoey Copilot Project Integration Status ==="
    echo "Current Time: $(date)"
    echo ""

    if [ -f "$CONFIG_FILE" ]; then
        echo "Project Configuration:"
        echo "  Name: $(jq -r '.projectName' "$CONFIG_FILE")"
        echo "  Type: $(jq -r '.projectType' "$CONFIG_FILE')"
        echo "  Frontend: $(jq -r '.directories.frontend' "$CONFIG_FILE')"
        echo "  Backend: $(jq -r '.directories.backend' "$CONFIG_FILE')"
        echo ""
    fi

    echo "Component Status:"
    echo "  Autonomous Launcher: $([ -f "start-autonomous-system.sh" ] && echo "Available" || echo "Missing")"
    echo "  Build Master: $([ -f "auto-build-master.sh" ] && echo "Available" || echo "Missing")"
    echo "  Dependency Manager: $([ -f "auto-deps.sh" ] && echo "Available" || echo "Missing")"
    echo "  Resource Intelligence: $([ -f "resource-intelligence.sh" ] && echo "Available" || echo "Missing")"
    echo "  Space Manager: $([ -f "auto-space-manager.sh" ] && echo "Available" || echo "Missing")"
    echo ""

    echo "Project Structure:"
    echo "  Frontend (package.json): $([ -f "frontend/package.json" ] && echo "Detected" || echo "Missing")"
    echo "  Backend (requirements.txt): $([ -f "app/requirements.txt" ] && echo "Detected" || echo "Missing")"
    echo ""

    echo "Integration Complete"
    echo "=============================================="
}

setup_integration() {
    echo "Setting up project integration..."

    # Create build scripts
    cat > build-frontend.sh << 'SCRIPT_EOF'
#!/bin/bash
cd frontend
echo "Starting frontend build..."
npm run lint && npm run test:ci && npm run build
echo "Frontend build completed"
SCRIPT_EOF

    cat > build-backend.sh << 'SCRIPT_EOF'
#!/bin/bash
cd app
echo "Starting backend build..."
npm run lint && python -m pytest --cov=. && pip install -r requirements.txt
echo "Backend build completed"
SCRIPT_EOF

    chmod +x build-frontend.sh build-backend.sh

    # Create autonomous wrapper
    cat > autonomous-wrapper.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "Starting Autonomous System for Samoey Copilot..."
./start-autonomous-system.sh start
SCRIPT_EOF

    chmod +x autonomous-wrapper.sh

    echo "Project integration setup completed!"
}

case "$1" in
    "setup")
        setup_integration
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Project Integration Script for Samoey Copilot"
        echo ""
        echo "Usage: $0 {setup|status}"
        echo ""
        echo "Commands:"
        echo "  setup  - Set up project integration"
        echo "  status - Show integration status"
        exit 1
        ;;
esac
