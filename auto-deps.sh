#!/bin/bash

# Auto-Dependency Resolver for Autonomous Build System
# Self-managing dependency installation, updates, and conflict resolution

set -e

# Configuration
LOG_FILE="$HOME/auto-deps.log"
PROJECT_ROOT="$(pwd)"
DEPS_STATE="$PROJECT_ROOT/.autonomous/.deps_state"
DEPS_CACHE="$PROJECT_ROOT/.autonomous/.deps_cache"
SECURITY_SCAN_LOG="$PROJECT_ROOT/.autonomous/.security_scan.log"
VULNERABILITY_DB="$PROJECT_ROOT/.autonomous/.vulnerability_db"

# Global variables
DEPS_PID=""
MONITORING_ACTIVE=false
AUTO_UPDATE=true
SECURITY_SCAN=true
CONFLICT_RESOLUTION=true
ROLLBACK_ENABLED=true

# Initialize dependency management system
init_deps_system() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] === Auto-Dependency Resolver Initializing ===" | tee -a $LOG_FILE

    # Create autonomous directory
    mkdir -p "$PROJECT_ROOT/.autonomous"

    # Initialize state files
    touch "$DEPS_STATE" "$DEPS_CACHE" "$SECURITY_SCAN_LOG" "$VULNERABILITY_DB"

    # Initialize dependency state
    echo "status=initialized" > "$DEPS_STATE"
    echo "last_scan=never" >> "$DEPS_STATE"
    echo "last_update=never" >> "$DEPS_STATE"
    echo "security_issues=0" >> "$DEPS_STATE"
    echo "conflicts_resolved=0" >> "$DEPS_STATE"
    echo "rollbacks_performed=0" >> "$DEPS_STATE"
    echo "packages_managed=0" >> "$DEPS_STATE"

    # Initialize vulnerability database
    echo "# Vulnerability Database" > "$VULNERABILITY_DB"
    echo "last_updated=never" >> "$VULNERABILITY_DB"
    echo "known_vulnerabilities=0" >> "$VULNERABILITY_DB"
    echo "patches_applied=0" >> "$VULNERABILITY_DB"

    log_message "Auto-Dependency Resolver initialized successfully"
}

# Logging function
log_message() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a $LOG_FILE
}

# Detect project type and dependencies
detect_project_type() {
    log_message "Detecting project type and dependencies..."

    local project_type="unknown"
    local dependency_files=()
    local package_managers=()

    # Check for different project types
    if [ -f "package.json" ]; then
        project_type="nodejs"
        dependency_files+=("package.json")
        package_managers+=("npm")
        package_managers+=("yarn")
        package_managers+=("pnpm")
    fi

    if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        project_type="python"
        if [ -f "requirements.txt" ]; then
            dependency_files+=("requirements.txt")
        fi
        if [ -f "setup.py" ]; then
            dependency_files+=("setup.py")
        fi
        if [ -f "pyproject.toml" ]; then
            dependency_files+=("pyproject.toml")
        fi
        package_managers+=("pip")
        package_managers+=("pipenv")
        package_managers+=("poetry")
    fi

    if [ -f "pom.xml" ] || [ -f "build.gradle" ]; then
        project_type="java"
        if [ -f "pom.xml" ]; then
            dependency_files+=("pom.xml")
        fi
        if [ -f "build.gradle" ]; then
            dependency_files+=("build.gradle")
        fi
        package_managers+=("mvn")
        package_managers+=("gradle")
    fi

    if [ -f "Cargo.toml" ]; then
        project_type="rust"
        dependency_files+=("Cargo.toml")
        package_managers+=("cargo")
    fi

    if [ -f "go.mod" ]; then
        project_type="go"
        dependency_files+=("go.mod")
        package_managers+=("go")
    fi

    if [ -f "composer.json" ]; then
        project_type="php"
        dependency_files+=("composer.json")
        package_managers+=("composer")
    fi

    if [ -f "Gemfile" ]; then
        project_type="ruby"
        dependency_files+=("Gemfile")
        package_managers+=("bundle")
    fi

    log_message "Project type detected: $project_type"
    log_message "Dependency files: ${dependency_files[*]}"
    log_message "Available package managers: ${package_managers[*]}"

    echo "$project_type|${dependency_files[*]}|${package_managers[*]}"
}

# Check if dependencies need installation
check_dependencies_needed() {
    local detection=$(detect_project_type)
    local project_type=$(echo "$detection" | cut -d'|' -f1)
    local dependency_files=$(echo "$detection" | cut -d'|' -f2)
    local package_managers=$(echo "$detection" | cut -d'|' -f3)

    local needs_install=false
    local reasons=()

    case "$project_type" in
        "nodejs")
            if [ ! -d "node_modules" ]; then
                needs_install=true
                reasons+=("node_modules directory missing")
            elif [ "package.json" -nt "node_modules" ]; then
                needs_install=true
                reasons+=("package.json newer than node_modules")
            fi
            ;;
        "python")
            if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
                needs_install=true
                reasons+=("Python virtual environment missing")
            fi
            ;;
        "java")
            if [ ! -d "target" ] && [ ! -d "build" ]; then
                needs_install=true
                reasons+=("Build directory missing")
            fi
            ;;
    esac

    # Check for package lock files
    if [ -f "package-lock.json" ] && [ "package-lock.json" -nt "node_modules" ]; then
        needs_install=true
        reasons+=("package-lock.json newer than node_modules")
    fi

    if [ -f "yarn.lock" ] && [ "yarn.lock" -nt "node_modules" ]; then
        needs_install=true
        reasons+=("yarn.lock newer than node_modules")
    fi

    if [ "$needs_install" = true ]; then
        log_message "Dependencies need installation: ${reasons[*]}"
    else
        log_message "Dependencies are up to date"
    fi

    return $([ "$needs_install" = true ] && echo 0 || echo 1)
}

# Install Node.js dependencies
install_nodejs_deps() {
    log_message "Installing Node.js dependencies..."

    # Check if npm, yarn, or pnpm is available
    local package_manager="npm"
    if command -v yarn &> /dev/null; then
        package_manager="yarn"
    elif command -v pnpm &> /dev/null; then
        package_manager="pnpm"
    fi

    log_message "Using package manager: $package_manager"

    # Install dependencies
    case "$package_manager" in
        "npm")
            if [ -f "package-lock.json" ]; then
                npm ci || { log_message "npm ci failed, trying npm install"; npm install; }
            else
                npm install
            fi
            ;;
        "yarn")
            yarn install --frozen-lockfile || { log_message "yarn install with frozen lockfile failed, trying regular install"; yarn install; }
            ;;
        "pnpm")
            pnpm install || { log_message "pnpm install failed"; exit 1; }
            ;;
    esac

    # Update state
    local packages=$(jq '.dependencies | keys | length' package.json 2>/dev/null || echo "0")
    local dev_packages=$(jq '.devDependencies | keys | length' package.json 2>/dev/null || echo "0")
    local total_packages=$((packages + dev_packages))

    # Update packages managed count
    local current_packages=$(grep "^packages_managed=" "$DEPS_STATE" | cut -d'=' -f2)
    current_packages=$((current_packages + total_packages))
    sed -i '' "s/packages_managed=.*/packages_managed=$current_packages/" "$DEPS_STATE"

    log_message "Node.js dependencies installed successfully ($total_packages packages)"
}

# Install Python dependencies
install_python_deps() {
    log_message "Installing Python dependencies..."

    # Check if pip, pipenv, or poetry is available
    local package_manager="pip"
    local venv_name="venv"

    if command -v poetry &> /dev/null; then
        package_manager="poetry"
    elif command -v pipenv &> /dev/null; then
        package_manager="pipenv"
        venv_name=".venv"
    fi

    log_message "Using package manager: $package_manager"

    # Create virtual environment if needed
    if [ ! -d "$venv_name" ]; then
        log_message "Creating Python virtual environment..."
        case "$package_manager" in
            "pip")
                python3 -m venv "$venv_name" || { log_message "Failed to create virtual environment"; exit 1; }
                ;;
            "pipenv")
                pipenv install --dev || { log_message "Failed to create virtual environment with pipenv"; exit 1; }
                ;;
            "poetry")
                poetry install || { log_message "Failed to create virtual environment with poetry"; exit 1; }
                ;;
        esac
    fi

    # Install dependencies
    case "$package_manager" in
        "pip")
            source "$venv_name/bin/activate"
            if [ -f "requirements.txt" ]; then
                pip install -r requirements.txt || { log_message "pip install failed"; exit 1; }
            fi
            if [ -f "setup.py" ]; then
                pip install -e . || { log_message "pip install from setup.py failed"; exit 1; }
            fi
            ;;
        "pipenv")
            if [ -f "requirements.txt" ]; then
                pipenv install -r requirements.txt || { log_message "pipenv install failed"; exit 1; }
            fi
            ;;
        "poetry")
            # Poetry handles dependencies automatically
            ;;
    esac

    # Update state
    local packages=0
    if [ -f "requirements.txt" ]; then
        packages=$(wc -l < requirements.txt)
    fi

    local current_packages=$(grep "^packages_managed=" "$DEPS_STATE" | cut -d'=' -f2)
    current_packages=$((current_packages + packages))
    sed -i '' "s/packages_managed=.*/packages_managed=$current_packages/" "$DEPS_STATE"

    log_message "Python dependencies installed successfully ($packages packages)"
}

# Install Java dependencies
install_java_deps() {
    log_message "Installing Java dependencies..."

    if [ -f "pom.xml" ]; then
        # Use Maven
        if command -v mvn &> /dev/null; then
            mvn clean install || { log_message "Maven install failed"; exit 1; }
        else
            log_message "Maven not found, cannot install Java dependencies"
            return 1
        fi
    elif [ -f "build.gradle" ]; then
        # Use Gradle
        if command -v gradle &> /dev/null; then
            gradle build || { log_message "Gradle build failed"; exit 1; }
        else
            log_message "Gradle not found, cannot install Java dependencies"
            return 1
        fi
    else
        log_message "No Java dependency file found"
        return 1
    fi

    log_message "Java dependencies installed successfully"
}

# Install Rust dependencies
install_rust_deps() {
    log_message "Installing Rust dependencies..."

    if [ ! -f "Cargo.toml" ]; then
        log_message "No Cargo.toml found"
        return 1
    fi

    if command -v cargo &> /dev/null; then
        cargo build || { log_message "Cargo build failed"; exit 1; }
    else
        log_message "Cargo not found, cannot install Rust dependencies"
        return 1
    fi

    log_message "Rust dependencies installed successfully"
}

# Install Go dependencies
install_go_deps() {
    log_message "Installing Go dependencies..."

    if [ ! -f "go.mod" ]; then
        log_message "No go.mod found"
        return 1
    fi

    if command -v go &> /dev/null; then
        go mod download || { log_message "go mod download failed"; exit 1; }
        go mod tidy || { log_message "go mod tidy failed"; exit 1; }
    else
        log_message "Go not found, cannot install Go dependencies"
        return 1
    fi

    log_message "Go dependencies installed successfully"
}

# Install PHP dependencies
install_php_deps() {
    log_message "Installing PHP dependencies..."

    if [ ! -f "composer.json" ]; then
        log_message "No composer.json found"
        return 1
    fi

    if command -v composer &> /dev/null; then
        composer install || { log_message "Composer install failed"; exit 1; }
    else
        log_message "Composer not found, cannot install PHP dependencies"
        return 1
    fi

    log_message "PHP dependencies installed successfully"
}

# Install Ruby dependencies
install_ruby_deps() {
    log_message "Installing Ruby dependencies..."

    if [ ! -f "Gemfile" ]; then
        log_message "No Gemfile found"
        return 1
    fi

    if command -v bundle &> /dev/null; then
        bundle install || { log_message "Bundle install failed"; exit 1; }
    else
        log_message "Bundle not found, cannot install Ruby dependencies"
        return 1
    fi

    log_message "Ruby dependencies installed successfully"
}

# Auto-install dependencies based on project type
auto_install_dependencies() {
    log_message "Starting automatic dependency installation..."

    local detection=$(detect_project_type)
    local project_type=$(echo "$detection" | cut -d'|' -f1)

    case "$project_type" in
        "nodejs")
            install_nodejs_deps
            ;;
        "python")
            install_python_deps
            ;;
        "java")
            install_java_deps
            ;;
        "rust")
            install_rust_deps
            ;;
        "go")
            install_go_deps
            ;;
        "php")
            install_php_deps
            ;;
        "ruby")
            install_ruby_deps
            ;;
        *)
            log_message "Unknown project type, cannot auto-install dependencies"
            return 1
            ;;
    esac

    # Update last update timestamp
    sed -i '' "s/last_update=.*/last_update=$(date +%s)/" "$DEPS_STATE"

    log_message "Automatic dependency installation completed"
}

# Update dependencies
update_dependencies() {
    log_message "Starting dependency update..."

    local detection=$(detect_project_type)
    local project_type=$(echo "$detection" | cut -d'|' -f1)

    case "$project_type" in
        "nodejs")
            if command -v npm &> /dev/null; then
                npm update
            elif command -v yarn &> /dev/null; then
                yarn upgrade
            elif command -v pnpm &> /dev/null; then
                pnpm update
            fi
            ;;
        "python")
            if command -v pip &> /dev/null; then
                if [ -d "venv" ]; then
                    source venv/bin/activate
                fi
                pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U || true
            fi
            ;;
        "java")
            if [ -f "pom.xml" ] && command -v mvn &> /dev/null; then
                mvn versions:use-latest-releases
            fi
            ;;
    esac

    # Update last update timestamp
    sed -i '' "s/last_update=.*/last_update=$(date +%s)/" "$DEPS_STATE"

    log_message "Dependency update completed"
}

# Security scan for vulnerabilities
security_scan() {
    log_message "Starting security vulnerability scan..."

    local vulnerabilities_found=0
    local patches_applied=0

    local detection=$(detect_project_type)
    local project_type=$(echo "$detection" | cut -d'|' -f1)

    case "$project_type" in
        "nodejs")
            if command -v npm &> /dev/null; then
                log_message "Running npm audit..."
                npm audit --json > "$SECURITY_SCAN_LOG" 2>&1 || true

                # Count vulnerabilities
                if [ -f "$SECURITY_SCAN_LOG" ]; then
                    local vuln_count=$(jq '.metadata.vulnerabilities.total // 0' "$SECURITY_SCAN_LOG" 2>/dev/null || echo "0")
                    vulnerabilities_found=$((vulnerabilities_found + vuln_count))

                    # Auto-fix if possible
                    if [ $vuln_count -gt 0 ]; then
                        log_message "Found $vuln_count vulnerabilities, attempting auto-fix..."
                        npm audit fix || true
                        patches_applied=$((patches_applied + 1))
                    fi
                fi
            fi
            ;;
        "python")
            if command -v pip &> /dev/null; then
                log_message "Running pip safety check..."
                if command -v safety &> /dev/null; then
                    safety check --json > "$SECURITY_SCAN_LOG" 2>&1 || true

                    if [ -f "$SECURITY_SCAN_LOG" ]; then
                        local vuln_count=$(jq '. | length' "$SECURITY_SCAN_LOG" 2>/dev/null || echo "0")
                        vulnerabilities_found=$((vulnerabilities_found + vuln_count))
                    fi
                fi
            fi
            ;;
    esac

    # Update vulnerability database
    sed -i '' "s/last_updated=.*/last_updated=$(date +%s)/" "$VULNERABILITY_DB"
    local current_vuln=$(grep "^known_vulnerabilities=" "$VULNERABILITY_DB" | cut -d'=' -f2)
    current_vuln=$((current_vuln + vulnerabilities_found))
    sed -i '' "s/known_vulnerabilities=.*/known_vulnerabilities=$current_vuln/" "$VULNERABILITY_DB"

    local current_patches=$(grep "^patches_applied=" "$VULNERABILITY_DB" | cut -d'=' -f2)
    current_patches=$((current_patches + patches_applied))
    sed -i '' "s/patches_applied=.*/patches_applied=$current_patches/" "$VULNERABILITY_DB"

    # Update security issues count
    local current_issues=$(grep "^security_issues=" "$DEPS_STATE" | cut -d'=' -f2)
    current_issues=$((current_issues + vulnerabilities_found))
    sed -i '' "s/security_issues=.*/security_issues=$current_issues/" "$DEPS_STATE"

    log_message "Security scan completed - $vulnerabilities_found vulnerabilities found, $patches_applied patches applied"
}

# Resolve dependency conflicts
resolve_conflicts() {
    log_message "Starting dependency conflict resolution..."

    local conflicts_resolved=0

    local detection=$(detect_project_type)
    local project_type=$(echo "$detection" | cut -d'|' -f1)

    case "$project_type" in
        "nodejs")
            # Check for duplicate packages
            if [ -f "package.json" ]; then
                local duplicates=$(jq '.dependencies + .devDependencies | to_entries | group_by(.key) | map(select(length > 1)) | length' package.json 2>/dev/null || echo "0")
                if [ $duplicates -gt 0 ]; then
                    log_message "Found $duplicates duplicate packages, resolving..."
                    # Remove devDependencies that exist in dependencies
                    jq 'def remove_dev_deps(deps): .devDependencies |= with_entries(select(.key as $key | $key | IN(deps | keys[]) | not))); remove_dev_deps(.dependencies)' package.json > package.json.tmp && mv package.json.tmp package.json
                    conflicts_resolved=$((conflicts_resolved + 1))
                fi
            fi
            ;;
        "python")
            # Check for conflicting requirements
            if [ -f "requirements.txt" ]; then
                local conflicts=$(sort requirements.txt | uniq -d | wc -l)
                if [ $conflicts -gt 0 ]; then
                    log_message "Found $conflicts conflicting requirements, resolving..."
                    sort requirements.txt | uniq -u > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt
                    conflicts_resolved=$((conflicts_resolved + 1))
                fi
            fi
            ;;
    esac

    # Update conflicts resolved count
    local current_conflicts=$(grep "^conflicts_resolved=" "$DEPS_STATE" | cut -d'=' -f2)
    current_conflicts=$((current_conflicts + conflicts_resolved))
    sed -i '' "s/conflicts_resolved=.*/conflicts_resolved=$current_conflicts/" "$DEPS_STATE"

    log_message "Dependency conflict resolution completed - $conflicts_resolved conflicts resolved"
}

# Create backup before making changes
create_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="$PROJECT_ROOT/.autonomous/backups"
    mkdir -p "$backup_dir"

    # Backup package files
    for file in package.json package-lock.json yarn.lock requirements.txt setup.py pyproject.toml pom.xml build.gradle Cargo.toml go.mod composer.json Gemfile; do
        if [ -f "$file" ]; then
            cp "$file" "$backup_dir/${file}_${timestamp}"
        fi
    done

    # Backup node_modules if it exists
    if [ -d "node_modules" ]; then
        tar -czf "$backup_dir/node_modules_${timestamp}.tar.gz" node_modules/ 2>/dev/null || true
    fi

    log_message "Backup created at $backup_dir"
}

# Rollback to previous state
rollback() {
    log_message "Starting dependency rollback..."

    local backup_dir="$PROJECT_ROOT/.autonomous/backups"
    if [ ! -d "$backup_dir" ]; then
        log_message "No backups found, cannot rollback"
        return 1
    fi

    # Find most recent backup
    local latest_backup=$(ls -t "$backup_dir" | head -1 | cut -d'_' -f1)
    if [ -z "$latest_backup" ]; then
        log_message "No valid backup found, cannot rollback"
        return 1
    fi

    log_message "Rolling back to backup: $latest_backup"

    # Restore package files
    for file in package.json package-lock.json yarn.lock requirements.txt setup.py pyproject.toml pom.xml build.gradle Cargo.toml go.mod composer.json Gemfile; do
        local backup_file="$backup_dir/${file}_${latest_backup}"
        if [ -f "$backup_file" ]; then
            cp "$backup_file" "$file"
            log_message "Restored $file"
        fi
    done

    # Restore node_modules if backup exists
    local node_modules_backup="$backup_dir/node_modules_${latest_backup}.tar.gz"
    if [ -f "$node_modules_backup" ]; then
        rm -rf node_modules/
        tar -xzf "$node_modules_backup"
        log_message "Restored node_modules"
    fi

    # Update rollback count
    local current_rollbacks=$(grep "^rollbacks_performed=" "$DEPS_STATE" | cut -d'=' -f2)
    current_rollbacks=$((current_rollbacks + 1))
    sed -i '' "s/rollbacks_performed=.*/rollbacks_performed=$current_rollbacks/" "$DEPS_STATE"

    log_message "Dependency rollback completed"
}

# Show dependency status
show_deps_status() {
    echo "=== Auto-Dependency Resolver Status ==="
    echo "Current Time: $(date)"
    echo ""

    # Get project type
    local detection=$(detect_project_type)
    local project_type=$(echo "$detection" | cut -d'|' -f1)
    local dependency_files=$(echo "$detection" | cut -d'|' -f2)
    local package_managers=$(echo "$detection" | cut -d'|' -f3)

    echo "Project Type: $project_type"
    echo "Dependency Files: $dependency_files"
    echo "Available Package Managers: $package_managers"
    echo ""

    # Show state information
    if [ -f "$DEPS_STATE" ]; then
        echo "System State:"
        cat "$DEPS_STATE" | while read line; do
            echo "  $line"
        done
    fi

    echo ""
    echo "Security Status:"
    if [ -f "$VULNERABILITY_DB" ]; then
        cat "$VULNERABILITY_DB" | while read line; do
            echo "  $line"
        done
    fi

    echo ""
    echo "=================================="
}

# Main execution function
main() {
    local action="$1"

    case "$action" in
        "install")
            init_deps_system
            auto_install_dependencies
            ;;
        "update")
            init_deps_system
            update_dependencies
            ;;
        "security-scan")
            init_deps_system
            security_scan
            ;;
        "resolve-conflicts")
            init_deps_system
            resolve_conflicts
            ;;
        "backup")
            create_backup
            ;;
        "rollback")
            rollback
            ;;
        "status")
            show_deps_status
            ;;
        *)
            echo "Auto-Dependency Resolver for Samoey Copilot Project"
            echo ""
            echo "Usage: $0 {install|update|security-scan|resolve-conflicts|backup|rollback|status}"
            echo ""
            echo "Commands:"
            echo "  install            - Install dependencies for detected project type"
            echo "  update             - Update all dependencies"
            echo "  security-scan      - Run security vulnerability scan"
            echo "  resolve-conflicts  - Resolve dependency conflicts"
            echo "  backup             - Create backup of dependency files"
            echo "  rollback           - Rollback to previous backup"
            echo "  status             - Show current dependency status"
            echo ""
            echo "Features:"
            echo "  - Multi-language support (Node.js, Python, Java, Rust, Go, PHP, Ruby)"
            echo "  - Automatic project type detection"
            echo "  - Security vulnerability scanning"
            echo "  - Conflict resolution"
            echo "  - Backup and rollback capabilities"
            echo "  - Comprehensive status reporting"
            exit 1
            ;;
    esac
}

# Run main function with arguments
main "$@"
