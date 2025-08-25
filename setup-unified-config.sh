#!/bin/bash
# Unified Configuration System for Samoey Copilot Autonomous System
# This script consolidates and simplifies configuration management

set -e

# Configuration
CONFIG_DIR=".autonomous/config"
UNIFIED_CONFIG="$CONFIG_DIR/unified-config.json"
LEGACY_CONFIG=".autonomous-project-config.json"
BACKUP_DIR="$CONFIG_DIR/backups"

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

# Create configuration directory structure
setup_config_structure() {
    log_message "Setting up unified configuration structure..."

    mkdir -p "$CONFIG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$CONFIG_DIR/templates"
    mkdir -p "$CONFIG_DIR/overrides"

    log_message "Configuration structure created successfully"
}

# Backup existing configuration
backup_existing_config() {
    if [ -f "$LEGACY_CONFIG" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="$BACKUP_DIR/legacy-config-backup-$timestamp.json"

        log_message "Backing up existing configuration..."
        cp "$LEGACY_CONFIG" "$backup_file"
        log_message "Configuration backed up to: $backup_file"
    fi
}

# Create unified configuration template
create_unified_config_template() {
    log_message "Creating unified configuration template..."

    cat > "$CONFIG_DIR/templates/unified-config-template.json" << 'EOF'
{
  "meta": {
    "version": "2.0.0",
    "created": "2025-01-01T00:00:00Z",
    "lastModified": "2025-01-01T00:00:00Z",
    "description": "Unified configuration for Samoey Copilot Autonomous System"
  },
  "project": {
    "name": "Samoey Copilot",
    "type": "full-stack",
    "version": "1.0.0",
    "environment": "development",
    "root": "./"
  },
  "directories": {
    "frontend": "frontend/",
    "backend": "app/",
    "config": ".autonomous/config/",
    "logs": ".autonomous/logs/",
    "backups": ".autonomous/backups/",
    "temp": ".autonomous/temp/"
  },
  "build": {
    "enabled": true,
    "autoBuild": true,
    "parallelJobs": 2,
    "timeout": 3600,
    "retryCount": 3,
    "retryDelay": 60,
    "triggers": {
      "fileChanges": true,
      "dependencyChanges": true,
      "schedule": {
        "enabled": false,
        "cron": "0 2 * * *"
      }
    },
    "frontend": {
      "enabled": true,
      "watchPaths": [
        "frontend/src/**/*",
        "frontend/public/**/*",
        "frontend/package.json",
        "frontend/next.config.js",
        "frontend/tailwind.config.ts"
      ],
      "buildCommand": "cd frontend && npm run build",
      "testCommand": "cd frontend && npm run test:ci",
      "lintCommand": "cd frontend && npm run lint",
      "dependencies": ["node", "npm", "next"],
      "packageManager": "npm",
      "environment": "development"
    },
    "backend": {
      "enabled": true,
      "watchPaths": [
        "app/**/*.py",
        "app/requirements.txt",
        "app/main.py",
        "app/models.py"
      ],
      "buildCommand": "cd app && python -m pytest",
      "testCommand": "cd app && python -m pytest --cov=.",
      "lintCommand": "cd app && black . && flake8 .",
      "dependencies": ["python3", "pip", "uvicorn"],
      "packageManager": "pip",
      "environment": "development"
    }
  },
  "resources": {
    "monitoring": {
      "enabled": true,
      "interval": 30,
      "retentionDays": 30
    },
    "thresholds": {
      "cpu": {
        "warning": 75,
        "critical": 90,
        "action": "optimize"
      },
      "memory": {
        "warning": 75,
        "critical": 90,
        "action": "optimize"
      },
      "disk": {
        "warning": 85,
        "critical": 95,
        "action": "cleanup"
      },
      "temperature": {
        "warning": 75,
        "critical": 85,
        "action": "throttle"
      }
    },
    "optimization": {
      "level": "balanced",
      "autoOptimize": true,
      "cleanupInterval": 3600,
      "backupRetention": 7
    }
  },
  "autonomous": {
    "mode": "supervised",
    "decisionMaking": {
      "enabled": true,
      "confidenceThreshold": 0.7,
      "learningRate": 0.1
    },
    "selfHealing": {
      "enabled": true,
      "maxRetries": 3,
      "retryDelay": 60
    },
    "prediction": {
      "enabled": true,
      "modelType": "adaptive",
      "accuracyTarget": 0.8
    }
  },
  "security": {
    "enabled": true,
    "filePermissions": {
      "scripts": "755",
      "configs": "644",
      "sensitive": "600"
    },
    "accessControl": {
      "logAccess": true,
      "configAccess": true,
      "requireAuth": false
    },
    "audit": {
      "enabled": true,
      "logFile": ".autonomous/security/audit.log",
      "events": ["config_change", "system_start", "system_stop", "build_execution"]
    }
  },
  "monitoring": {
    "enabled": true,
    "logging": {
      "level": "INFO",
      "format": "json",
      "rotation": {
        "enabled": true,
        "maxSize": "100MB",
        "maxFiles": 10,
        "compress": true
      }
    },
    "alerts": {
      "enabled": true,
      "channels": ["console", "log"],
      "email": {
        "enabled": false,
        "smtp": {
          "host": "",
          "port": 587,
          "username": "",
          "password": ""
        }
      },
      "webhook": {
        "enabled": false,
        "url": ""
      }
    },
    "health": {
      "enabled": true,
      "checkInterval": 60,
      "endpoints": ["/health", "/metrics"]
    }
  },
  "notifications": {
    "enabled": true,
    "buildSuccess": true,
    "buildFailure": true,
    "securityIssues": true,
    "resourceWarnings": true,
    "systemAlerts": true,
    "methods": {
      "desktop": true,
      "email": false,
      "webhook": false
    }
  },
  "integrations": {
    "docker": {
      "enabled": true,
      "composeFile": "docker-compose.yml"
    },
    "database": {
      "enabled": true,
      "type": "postgresql",
      "migrations": true
    },
    "api": {
      "enabled": true,
      "documentation": true,
      "versioning": true
    },
    "websocket": {
      "enabled": true,
      "port": 8000
    }
  },
  "advanced": {
    "experimental": {
      "enabled": false,
      "features": []
    },
    "performance": {
      "caching": {
        "enabled": true,
        "type": "redis",
        "ttl": 3600
      },
      "compression": {
        "enabled": true,
        "level": 6
      }
    },
    "debug": {
      "enabled": false,
      "verbose": false,
      "profiling": false
    }
  }
}
EOF

    log_message "Unified configuration template created"
}

# Migrate existing configuration
migrate_existing_config() {
    if [ -f "$LEGACY_CONFIG" ]; then
        log_message "Migrating existing configuration..."

        # Read legacy config and extract key values
        local project_name=$(jq -r '.projectName // "Samoey Copilot"' "$LEGACY_CONFIG")
        local project_type=$(jq -r '.projectType // "full-stack"' "$LEGACY_CONFIG")
        local frontend_dir=$(jq -r '.directories.frontend // "frontend/"' "$LEGACY_CONFIG")
        local backend_dir=$(jq -r '.directories.backend // "app/"' "$LEGACY_CONFIG")

        # Extract resource thresholds
        local cpu_threshold=$(jq -r '.resourceManagement.cpuThreshold // 80' "$LEGACY_CONFIG")
        local memory_threshold=$(jq -r '.resourceManagement.memoryThreshold // 85' "$LEGACY_CONFIG")
        local disk_threshold=$(jq -r '.resourceManagement.diskThreshold // 90' "$LEGACY_CONFIG")

        # Extract autonomous settings
        local build_on_change=$(jq -r '.autonomousSettings.buildOnFileChange // true' "$LEGACY_CONFIG")
        local run_tests=$(jq -r '.autonomousSettings.runTestsOnBuild // true' "$LEGACY_CONFIG")
        local security_scan=$(jq -r '.autonomousSettings.securityScanOnBuild // true' "$LEGACY_CONFIG")

        # Create migrated configuration
        jq --arg name "$project_name" \
           --arg type "$project_type" \
           --arg frontend "$frontend_dir" \
           --arg backend "$backend_dir" \
           --argjson cpu "$cpu_threshold" \
           --argjson memory "$memory_threshold" \
           --argjson disk "$disk_threshold" \
           --argjson build_change "$build_on_change" \
           --argjson tests "$run_tests" \
           --argjson security "$security_scan" \
           '.project.name = $name |
            .project.type = $type |
            .directories.frontend = $frontend |
            .directories.backend = $backend |
            .resources.thresholds.cpu.critical = $cpu |
            .resources.thresholds.memory.critical = $memory |
            .resources.thresholds.disk.critical = $disk |
            .build.autoBuild = $build_change |
            .build.triggers.fileChanges = $build_change |
            .autonomous.selfHealing.enabled = $tests |
            .security.enabled = $security |
            .meta.lastModified = "$(date -Iseconds)"' \
           "$CONFIG_DIR/templates/unified-config-template.json" > "$UNIFIED_CONFIG"

        log_message "Configuration migrated successfully"
    else
        log_message "No existing configuration found, creating new unified configuration"
        cp "$CONFIG_DIR/templates/unified-config-template.json" "$UNIFIED_CONFIG"
    fi
}

# Create configuration management script
create_config_manager() {
    log_message "Creating configuration management script..."

    cat > "$CONFIG_DIR/config-manager.sh" << 'EOF'
#!/bin/bash
# Configuration Manager for Samoey Copilot Autonomous System

CONFIG_DIR=".autonomous/config"
UNIFIED_CONFIG="$CONFIG_DIR/unified-config.json"
TEMPLATES_DIR="$CONFIG_DIR/templates"

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

error_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${RED}[$timestamp] ERROR: $1${NC}"
}

# Show configuration
show_config() {
    if [ -f "$UNIFIED_CONFIG" ]; then
        echo "=== Current Unified Configuration ==="
        jq . "$UNIFIED_CONFIG"
        echo "======================================"
    else
        error_message "No unified configuration found"
        exit 1
    fi
}

# Edit configuration
edit_config() {
    if [ -f "$UNIFIED_CONFIG" ]; then
        ${EDITOR:-nano} "$UNIFIED_CONFIG"
        log_message "Configuration updated"
    else
        error_message "No unified configuration found"
        exit 1
    fi
}

# Validate configuration
validate_config() {
    if [ -f "$UNIFIED_CONFIG" ]; then
        if jq empty "$UNIFIED_CONFIG" 2>/dev/null; then
            log_message "Configuration is valid JSON"

            # Check required sections
            local required_sections=("project" "build" "resources" "autonomous" "security")
            for section in "${required_sections[@]}"; do
                if ! jq -e ".${section}" "$UNIFIED_CONFIG" > /dev/null; then
                    error_message "Missing required section: $section"
                    exit 1
                fi
            done

            log_message "All required sections present"
        else
            error_message "Configuration contains invalid JSON"
            exit 1
        fi
    else
        error_message "No unified configuration found"
        exit 1
    fi
}

# Reset configuration to template
reset_config() {
    if [ -f "$TEMPLATES_DIR/unified-config-template.json" ]; then
        cp "$TEMPLATES_DIR/unified-config-template.json" "$UNIFIED_CONFIG"
        log_message "Configuration reset to template"
    else
        error_message "No template found"
        exit 1
    fi
}

# Show help
show_help() {
    echo "Configuration Manager for Samoey Copilot Autonomous System"
    echo ""
    echo "Usage: $0 {show|edit|validate|reset|help}"
    echo ""
    echo "Commands:"
    echo "  show     - Show current configuration"
    echo "  edit     - Edit configuration in default editor"
    echo "  validate - Validate configuration syntax"
    echo "  reset    - Reset configuration to template"
    echo "  help     - Show this help message"
    echo ""
}

# Main execution
main() {
    local action="$1"

    case "$action" in
        "show")
            show_config
            ;;
        "edit")
            edit_config
            ;;
        "validate")
            validate_config
            ;;
        "reset")
            reset_config
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
EOF

    chmod +x "$CONFIG_DIR/config-manager.sh"
    log_message "Configuration management script created"
}

# Create configuration validation script
create_config_validator() {
    log_message "Creating configuration validation script..."

    cat > "$CONFIG_DIR/validate-config.sh" << 'EOF'
#!/bin/bash
# Configuration Validator for Samoey Copilot Autonomous System

CONFIG_DIR=".autonomous/config"
UNIFIED_CONFIG="$CONFIG_DIR/unified-config.json"

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

# Validate JSON syntax
validate_json() {
    if ! jq empty "$UNIFIED_CONFIG" 2>/dev/null; then
        error_message "Invalid JSON syntax"
        return 1
    fi
    return 0
}

# Validate required sections
validate_sections() {
    local required_sections=("project" "build" "resources" "autonomous" "security")
    local missing_sections=()

    for section in "${required_sections[@]}"; do
        if ! jq -e ".${section}" "$UNIFIED_CONFIG" > /dev/null; then
            missing_sections+=("$section")
        fi
    done

    if [ ${#missing_sections[@]} -gt 0 ]; then
        error_message "Missing required sections: ${missing_sections[*]}"
        return 1
    fi
    return 0
}

# Validate resource thresholds
validate_thresholds() {
    local thresholds=("cpu" "memory" "disk" "temperature")
    local issues=()

    for threshold in "${thresholds[@]}"; do
        local warning=$(jq -r ".resources.thresholds.${threshold}.warning // 0" "$UNIFIED_CONFIG")
        local critical=$(jq -r ".resources.thresholds.${threshold}.critical // 0" "$UNIFIED_CONFIG")

        if [ "$warning" -ge "$critical" ]; then
            issues+=("${threshold}: warning ($warning) >= critical ($critical)")
        fi

        if [ "$warning" -le 0 ] || [ "$warning" -gt 100 ]; then
            issues+=("${threshold}: warning threshold out of range (0-100): $warning")
        fi

        if [ "$critical" -le 0 ] || [ "$critical" -gt 100 ]; then
            issues+=("${threshold}: critical threshold out of range (0-100): $critical")
        fi
    done

    if [ ${#issues[@]} -gt 0 ]; then
        error_message "Threshold validation issues:"
        for issue in "${issues[@]}"; do
            error_message "  - $issue"
        done
        return 1
    fi
    return 0
}

# Validate build configuration
validate_build_config() {
    local issues=()

    # Check frontend build command
    local frontend_build=$(jq -r '.build.frontend.buildCommand // ""' "$UNIFIED_CONFIG")
    if [ -z "$frontend_build" ]; then
        issues+=("Frontend build command is empty")
    fi

    # Check backend build command
    local backend_build=$(jq -r '.build.backend.buildCommand // ""' "$UNIFIED_CONFIG")
    if [ -z "$backend_build" ]; then
        issues+=("Backend build command is empty")
    fi

    # Check timeout value
    local timeout=$(jq -r '.build.timeout // 0' "$UNIFIED_CONFIG")
    if [ "$timeout" -le 0 ]; then
        issues+=("Timeout value must be positive: $timeout")
    fi

    # Check retry count
    local retry_count=$(jq -r '.build.retryCount // 0' "$UNIFIED_CONFIG")
    if [ "$retry_count" -lt 0 ]; then
        issues+=("Retry count cannot be negative: $retry_count")
    fi

    if [ ${#issues[@]} -gt 0 ]; then
        error_message "Build configuration issues:"
        for issue in "${issues[@]}"; do
            error_message "  - $issue"
        done
        return 1
    fi
    return 0
}

# Validate directory structure
validate_directories() {
    local issues=()

    # Check frontend directory
    local frontend_dir=$(jq -r '.directories.frontend // ""' "$UNIFIED_CONFIG")
    if [ ! -d "$frontend_dir" ]; then
        issues+=("Frontend directory not found: $frontend_dir")
    fi

    # Check backend directory
    local backend_dir=$(jq -r '.directories.backend // ""' "$UNIFIED_CONFIG")
    if [ ! -d "$backend_dir" ]; then
        issues+=("Backend directory not found: $backend_dir")
    fi

    if [ ${#issues[@]} -gt 0 ]; then
        error_message "Directory validation issues:"
        for issue in "${issues[@]}"; do
            error_message "  - $issue"
        done
        return 1
    fi
    return 0
}

# Main validation function
main() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "=== Configuration Validation ==="
    echo "Time: $timestamp"
    echo ""

    local validation_passed=true

    # Validate JSON syntax
    if ! validate_json; then
        validation_passed=false
    fi

    # Validate required sections
    if ! validate_sections; then
        validation_passed=false
    fi

    # Validate thresholds
    if ! validate_thresholds; then
        validation_passed=false
    fi

    # Validate build configuration
    if ! validate_build_config; then
        validation_passed=false
    fi

    # Validate directory structure
    if ! validate_directories; then
        validation_passed=false
    fi

    echo ""
    if [ "$validation_passed" = true ]; then
        log_message "Configuration validation PASSED"
        exit 0
    else
        error_message "Configuration validation FAILED"
        exit 1
    fi
}

# Run main function
main "$@"
EOF
    chmod +x "$CONFIG_DIR/validate-config.sh"
    log_message "Configuration validation script created"
}

# Create configuration migration script
create_migration_script() {
    log_message "Creating configuration migration script..."

    cat > "$CONFIG_DIR/migrate-config.sh" << 'EOF'
#!/bin/bash
# Configuration Migration Script for Samoey Copilot Autonomous System

CONFIG_DIR=".autonomous/config"
UNIFIED_CONFIG="$CONFIG_DIR/unified-config.json"
LEGACY_CONFIG=".autonomous-project-config.json"
BACKUP_DIR="$CONFIG_DIR/backups"

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

# Backup legacy configuration
backup_legacy_config() {
    if [ -f "$LEGACY_CONFIG" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="$BACKUP_DIR/legacy-config-backup-$timestamp.json"

        log_message "Backing up legacy configuration..."
        cp "$LEGACY_CONFIG" "$backup_file"
        log_message "Legacy configuration backed up to: $backup_file"
        return 0
    else
        warn_message "No legacy configuration found"
        return 1
    fi
}

# Perform migration
perform_migration() {
    if [ ! -f "$LEGACY_CONFIG" ]; then
        warn_message "No legacy configuration to migrate"
        return 0
    fi

    log_message "Starting configuration migration..."

    # Use the migration logic from setup script
    local project_name=$(jq -r '.projectName // "Samoey Copilot"' "$LEGACY_CONFIG")
    local project_type=$(jq -r '.projectType // "full-stack"' "$LEGACY_CONFIG")
    local frontend_dir=$(jq -r '.directories.frontend // "frontend/"' "$LEGACY_CONFIG")
    local backend_dir=$(jq -r '.directories.backend // "app/"' "$LEGACY_CONFIG")

    # Extract resource thresholds
    local cpu_threshold=$(jq -r '.resourceManagement.cpuThreshold // 80' "$LEGACY_CONFIG")
    local memory_threshold=$(jq -r '.resourceManagement.memoryThreshold // 85' "$LEGACY_CONFIG")
    local disk_threshold=$(jq -r '.resourceManagement.diskThreshold // 90' "$LEGACY_CONFIG")

    # Extract autonomous settings
    local build_on_change=$(jq -r '.autonomousSettings.buildOnFileChange // true' "$LEGACY_CONFIG")
    local run_tests=$(jq -r '.autonomousSettings.runTestsOnBuild // true' "$LEGACY_CONFIG")
    local security_scan=$(jq -r '.autonomousSettings.securityScanOnBuild // true' "$LEGACY_CONFIG")

    # Create migrated configuration
    if [ -f "$CONFIG_DIR/templates/unified-config-template.json" ]; then
        jq --arg name "$project_name" \
           --arg type "$project_type" \
           --arg frontend "$frontend_dir" \
           --arg backend "$backend_dir" \
           --argjson cpu "$cpu_threshold" \
           --argjson memory "$memory_threshold" \
           --argjson disk "$disk_threshold" \
           --argjson build_change "$build_on_change" \
           --argjson tests "$run_tests" \
           --argjson security "$security_scan" \
           '.project.name = $name |
            .project.type = $type |
            .directories.frontend = $frontend |
            .directories.backend = $backend |
            .resources.thresholds.cpu.critical = $cpu |
            .resources.thresholds.memory.critical = $memory |
            .resources.thresholds.disk.critical = $disk |
            .build.autoBuild = $build_change |
            .build.triggers.fileChanges = $build_change |
            .autonomous.selfHealing.enabled = $tests |
            .security.enabled = $security |
            .meta.lastModified = "$(date -Iseconds)"' \
           "$CONFIG_DIR/templates/unified-config-template.json" > "$UNIFIED_CONFIG"

        log_message "Configuration migration completed successfully"
        return 0
    else
        error_message "Configuration template not found"
        return 1
    fi
}

# Validate migration
validate_migration() {
    if [ -f "$UNIFIED_CONFIG" ]; then
        log_message "Validating migrated configuration..."
        if "$CONFIG_DIR/validate-config.sh" > /dev/null 2>&1; then
            log_message "Migrated configuration is valid"
            return 0
        else
            error_message "Migrated configuration validation failed"
            return 1
        fi
    else
        error_message "No migrated configuration found"
        return 1
    fi
}

# Show help
show_help() {
    echo "Configuration Migration Script for Samoey Copilot Autonomous System"
    echo ""
    echo "Usage: $0 {migrate|backup|validate|help}"
    echo ""
    echo "Commands:"
    echo "  migrate   - Migrate legacy configuration to unified format"
    echo "  backup    - Backup legacy configuration"
    echo "  validate  - Validate migrated configuration"
    echo "  help      - Show this help message"
    echo ""
}

# Main execution
main() {
    local action="$1"

    case "$action" in
        "migrate")
            backup_legacy_config
            perform_migration
            validate_migration
            ;;
        "backup")
            backup_legacy_config
            ;;
        "validate")
            validate_migration
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
EOF
    chmod +x "$CONFIG_DIR/migrate-config.sh"
    log_message "Configuration migration script created"
}

# Main setup function
main() {
    echo "=== Samoey Copilot Unified Configuration Setup ==="
    echo ""

    setup_config_structure
    backup_existing_config
    create_unified_config_template
    migrate_existing_config
    create_config_manager
    create_config_validator
    create_migration_script

    echo ""
    echo "=== Setup Complete ==="
    echo "Unified configuration system installed successfully!"
    echo ""
    echo "Configuration files created:"
    echo "  - $CONFIG_DIR/unified-config.json"
    echo "  - $CONFIG_DIR/templates/unified-config-template.json"
    echo "  - $CONFIG_DIR/config-manager.sh"
    echo "  - $CONFIG_DIR/validate-config.sh"
    echo "  - $CONFIG_DIR/migrate-config.sh"
    echo ""
    echo "Next steps:"
    echo "  1. Review the unified configuration: $CONFIG_DIR/config-manager.sh show"
    echo "  2. Validate the configuration: $CONFIG_DIR/validate-config.sh"
    echo "  3. Edit if needed: $CONFIG_DIR/config-manager.sh edit"
    echo ""
    echo "=== Configuration Management Commands ==="
    echo "  - Show config: $CONFIG_DIR/config-manager.sh show"
    echo "  - Edit config: $CONFIG_DIR/config-manager.sh edit"
    echo "  - Validate config: $CONFIG_DIR/validate-config.sh"
    echo "  - Migrate config: $CONFIG_DIR/migrate-config.sh migrate"
    echo "============================================="
}

# Run main function
