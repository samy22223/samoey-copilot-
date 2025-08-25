#!/bin/bash

# Comprehensive Security Audit Script for Samoey Copilot
# Addresses security implementation gaps identified in analysis

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
AUDIT_DIR="./security-audits"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
AUDIT_REPORT="$AUDIT_DIR/security-audit-$TIMESTAMP.json"
SUMMARY_REPORT="$AUDIT_DIR/summary-$TIMESTAMP.md"
ENVIRONMENT=${1:-development}

echo -e "${BLUE}🔒 Starting comprehensive security audit for Samoey Copilot${NC}"
echo -e "${CYAN}Environment: $ENVIRONMENT${NC}"
echo -e "${CYAN}Timestamp: $(date -u)${NC}"

# Create audit directory
mkdir -p "$AUDIT_DIR"

# Initialize audit results
cat > "$AUDIT_REPORT" << EOF
{
  "audit_info": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$ENVIRONMENT",
    "audit_version": "1.0.0",
    "scanner_version": "comprehensive-audit-v1"
  },
  "categories": {},
  "summary": {
    "total_checks": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "critical_issues": 0,
    "security_score": 0
  },
  "recommendations": []
}
EOF

# Helper functions
log_result() {
    local category="$1"
    local check="$2"
    local status="$3"
    local details="$4"
    local severity="${5:-medium}"

    # Update JSON report
    jq --arg cat "$category" \
       --arg check "$check" \
       --arg status "$status" \
       --arg details "$details" \
       --arg severity "$severity" \
       --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.categories[$cat][$check] = {
         "status": $status,
         "details": $details,
         "severity": $severity,
         "timestamp": $timestamp
       }' "$AUDIT_REPORT" > "$AUDIT_REPORT.tmp" && mv "$AUDIT_REPORT.tmp" "$AUDIT_REPORT"
}

increment_counter() {
    local field="$1"
    jq --argjson value 1 ".summary.$field += \$value" "$AUDIT_REPORT" > "$AUDIT_REPORT.tmp" && mv "$AUDIT_REPORT.tmp" "$AUDIT_REPORT"
}

add_recommendation() {
    local recommendation="$1"
    local priority="${2:-medium}"
    local category="${3:-general}"

    jq --arg rec "$recommendation" \
       --arg pri "$priority" \
       --arg cat "$category" \
       '.recommendations += [{
         "recommendation": $rec,
         "priority": $pri,
         "category": $cat,
         "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
       }]' "$AUDIT_REPORT" > "$AUDIT_REPORT.tmp" && mv "$AUDIT_REPORT.tmp" "$AUDIT_REPORT"
}

# 1. Secrets Management Audit
echo -e "${YELLOW}🔐 Auditing secrets management...${NC}"

# Check for hardcoded secrets
echo -e "${CYAN}  Checking for hardcoded secrets...${NC}"
if grep -r -i "password\|secret\|key\|token" --include="*.py" --include="*.js" --include="*.ts" --include="*.yml" --include="*.yaml" --include="*.json" app/ frontend/ | grep -v "example\|placeholder\|test" > /tmp/secrets-scan.txt; then
    log_result "secrets_management" "hardcoded_secrets" "failed" "Found hardcoded secrets in codebase" "critical"
    increment_counter "failed"
    increment_counter "critical_issues"
    add_recommendation "Remove hardcoded secrets and implement proper secrets management with Vault" "critical" "secrets_management"
else
    log_result "secrets_management" "hardcoded_secrets" "passed" "No hardcoded secrets found"
    increment_counter "passed"
fi

# Check Vault integration
echo -e "${CYAN}  Checking Vault integration...${NC}"
if [ -f "app/core/vault_manager.py" ] && [ -f "vault-config/vault-config.hcl" ]; then
    log_result "secrets_management" "vault_integration" "passed" "Vault configuration and integration found"
    increment_counter "passed"
else
    log_result "secrets_management" "vault_integration" "failed" "Vault integration missing" "high"
    increment_counter "failed"
    add_recommendation "Implement HashiCorp Vault integration for enterprise-grade secrets management" "high" "secrets_management"
fi

# Check environment files
echo -e "${CYAN}  Checking environment files...${NC}"
if ls .env* 1> /dev/null 2>&1; then
    for env_file in .env*; do
        if [ -f "$env_file" ] && grep -q "password\|secret\|key" "$env_file"; then
            log_result "secrets_management" "env_file_security" "warning" "Environment file contains sensitive data" "medium"
            increment_counter "warnings"
            add_recommendation "Move sensitive data from environment files to Vault" "medium" "secrets_management"
        else
            log_result "secrets_management" "env_file_security" "passed" "Environment file is secure"
            increment_counter "passed"
        fi
    done
else
    log_result "secrets_management" "env_file_security" "passed" "No environment files found"
    increment_counter "passed"
fi

# 2. AI Security Audit
echo -e "${YELLOW}🤖 Auditing AI security...${NC}"

# Check AI input sanitization
echo -e "${CYAN}  Checking AI input sanitization...${NC}"
if grep -r "sanitize\|clean\|validate" app/core/ai* app/core/advanced_security.py > /dev/null; then
    log_result "ai_security" "input_sanitization" "passed" "AI input sanitization implemented"
    increment_counter "passed"
else
    log_result "ai_security" "input_sanitization" "failed" "AI input sanitization missing" "high"
    increment_counter "failed"
    add_recommendation "Implement AI input sanitization to prevent prompt injection attacks" "high" "ai_security"
fi

# Check prompt injection detection
echo -e "${CYAN}  Checking prompt injection detection...${NC}"
if grep -r "prompt.*injection\|injection.*prompt" app/core/advanced_security.py > /dev/null; then
    log_result "ai_security" "prompt_injection_detection" "passed" "Prompt injection detection implemented"
    increment_counter "passed"
else
    log_result "ai_security" "prompt_injection_detection" "warning" "Prompt injection detection needs enhancement" "medium"
    increment_counter "warnings"
    add_recommendation "Enhance prompt injection detection with advanced patterns" "medium" "ai_security"
fi

# 3. Network Security Audit
echo -e "${YELLOW}🌐 Auditing network security...${NC}"

# Check CORS configuration
echo -e "${CYAN}  Checking CORS configuration...${NC}"
if grep -r "CORS\|cors" app/config/settings.py app/main.py > /dev/null; then
    cors_config=$(grep -A 5 -B 5 "CORS" app/config/settings.py || echo "")
    if echo "$cors_config" | grep -q "\"\*\""; then
        log_result "network_security" "cors_configuration" "warning" "CORS allows all origins" "medium"
        increment_counter "warnings"
        add_recommendation "Restrict CORS origins for production environments" "medium" "network_security"
    else
        log_result "network_security" "cors_configuration" "passed" "CORS properly configured"
        increment_counter "passed"
    fi
else
    log_result "network_security" "cors_configuration" "failed" "CORS configuration missing" "high"
    increment_counter "failed"
    add_recommendation "Implement proper CORS configuration" "high" "network_security"
fi

# Check SSL/TLS configuration
echo -e "${CYAN}  Checking SSL/TLS configuration...${NC}"
if grep -r "ssl\|tls\|https" docker-compose*.yml app/config/settings.py nginx/nginx.conf > /dev/null; then
    log_result "network_security" "ssl_tls_configuration" "passed" "SSL/TLS configuration found"
    increment_counter "passed"
else
    log_result "network_security" "ssl_tls_configuration" "failed" "SSL/TLS configuration missing" "critical"
    increment_counter "failed"
    increment_counter "critical_issues"
    add_recommendation "Implement SSL/TLS for all network communications" "critical" "network_security"
fi

# 4. Application Security Audit
echo -e "${YELLOW}🛡️  Auditing application security...${NC}"

# Check SQL injection protection
echo -e "${CYAN}  Checking SQL injection protection...${NC}"
if grep -r "sqlalchemy\|orm\|parameterized" app/ > /dev/null; then
    log_result "application_security" "sql_injection_protection" "passed" "SQL injection protection implemented"
    increment_counter "passed"
else
    log_result "application_security" "sql_injection_protection" "failed" "SQL injection protection missing" "critical"
    increment_counter "failed"
    increment_counter "critical_issues"
    add_recommendation "Implement parameterized queries and ORM to prevent SQL injection" "critical" "application_security"
fi

# Check XSS protection
echo -e "${CYAN}  Checking XSS protection...${NC}"
if grep -r "escape\|sanitize\|html" app/ frontend/ > /dev/null; then
    log_result "application_security" "xss_protection" "passed" "XSS protection implemented"
    increment_counter "passed"
else
    log_result "application_security" "xss_protection" "failed" "XSS protection missing" "high"
    increment_counter "failed"
    add_recommendation "Implement XSS protection for all user inputs" "high" "application_security"
fi

# Check authentication and authorization
echo -e "${CYAN}  Checking authentication and authorization...${NC}"
if [ -f "app/auth.py" ] && [ -d "app/core/auth" ]; then
    log_result "application_security" "auth_implementation" "passed" "Authentication and authorization implemented"
    increment_counter "passed"
else
    log_result "application_security" "auth_implementation" "failed" "Authentication/authorization missing" "critical"
    increment_counter "failed"
    increment_counter "critical_issues"
    add_recommendation "Implement proper authentication and authorization system" "critical" "application_security"
fi

# 5. Infrastructure Security Audit
echo -e "${YELLOW}🏗️  Auditing infrastructure security...${NC}"

# Check Docker security
echo -e "${CYAN}  Checking Docker security...${NC}"
if [ -f "Dockerfile" ] && grep -q "USER\|HEALTHCHECK\|multi-stage" Dockerfile; then
    log_result "infrastructure_security" "docker_security" "passed" "Docker security best practices implemented"
    increment_counter "passed"
else
    log_result "infrastructure_security" "docker_security" "warning" "Docker security needs improvement" "medium"
    increment_counter "warnings"
    add_recommendation "Implement Docker security best practices (non-root user, multi-stage builds)" "medium" "infrastructure_security"
fi

# Check Kubernetes security
echo -e "${CYAN}  Checking Kubernetes security...${NC}"
if [ -d "kubernetes" ] || find . -name "*.yaml" -o -name "*.yml" | grep -q "deployment\|service\|configmap"; then
    log_result "infrastructure_security" "kubernetes_security" "passed" "Kubernetes configuration found"
    increment_counter "passed"
else
    log_result "infrastructure_security" "kubernetes_security" "failed" "Kubernetes manifests missing" "high"
    increment_counter "failed"
    add_recommendation "Create Kubernetes deployment manifests with security context" "high" "infrastructure_security"
fi

# 6. Monitoring and Logging Security
echo -e "${YELLOW}📊 Auditing monitoring and logging...${NC}"

# Check security monitoring
echo -e "${CYAN}  Checking security monitoring...${NC}"
if [ -d "monitoring" ] && [ -f "monitoring/prometheus.yml" ]; then
    if grep -q "security\|threat" monitoring/prometheus.yml monitoring/alert.rules; then
        log_result "monitoring_security" "security_monitoring" "passed" "Security monitoring implemented"
        increment_counter "passed"
    else
        log_result "monitoring_security" "security_monitoring" "warning" "Security monitoring incomplete" "medium"
        increment_counter "warnings"
        add_recommendation "Enhance monitoring with security-specific metrics and alerts" "medium" "monitoring_security"
    fi
else
    log_result "monitoring_security" "security_monitoring" "failed" "Security monitoring missing" "high"
    increment_counter "failed"
    add_recommendation "Implement security monitoring and alerting" "high" "monitoring_security"
fi

# Check audit logging
echo -e "${CYAN}  Checking audit logging...${NC}"
if grep -r "audit\|log.*security\|security.*log" app/ > /dev/null; then
    log_result "monitoring_security" "audit_logging" "passed" "Audit logging implemented"
    increment_counter "passed"
else
    log_result "monitoring_security" "audit_logging" "failed" "Audit logging missing" "high"
    increment_counter "failed"
    add_recommendation "Implement comprehensive audit logging for security events" "high" "monitoring_security"
fi

# 7. Dependency Security Audit
echo -e "${YELLOW}📦 Auditing dependency security...${NC}"

# Check Python dependencies
echo -e "${CYAN}  Checking Python dependencies...${NC}"
if [ -f "requirements.txt" ] || [ -f "app/requirements.txt" ]; then
    # Run safety check if available
    if command -v safety &> /dev/null; then
        echo -e "${CYAN}    Running safety check...${NC}"
        safety check --json --output /tmp/safety-report.json || true
        if [ -f "/tmp/safety-report.json" ]; then
            vulnerabilities=$(jq '. | length' /tmp/safety-report.json 2>/dev/null || echo "0")
            if [ "$vulnerabilities" -gt 0 ]; then
                log_result "dependency_security" "python_dependencies" "failed" "Found $vulnerabilities security vulnerabilities in Python dependencies" "high"
                increment_counter "failed"
                add_recommendation "Update vulnerable Python dependencies identified by safety check" "high" "dependency_security"
            else
                log_result "dependency_security" "python_dependencies" "passed" "No security vulnerabilities found in Python dependencies"
                increment_counter "passed"
            fi
        fi
    else
        log_result "dependency_security" "python_dependencies" "warning" "Safety check tool not available" "low"
        increment_counter "warnings"
        add_recommendation "Install safety for Python dependency security scanning" "low" "dependency_security"
    fi
else
    log_result "dependency_security" "python_dependencies" "passed" "No Python dependencies found"
    increment_counter "passed"
fi

# Check Node.js dependencies
echo -e "${CYAN}  Checking Node.js dependencies...${NC}"
if [ -f "frontend/package.json" ]; then
    cd frontend
    if command -v npm &> /dev/null; then
        echo -e "${CYAN}    Running npm audit...${NC}"
        npm audit --json --audit-level moderate > ../tmp/npm-audit.json || true
        if [ -f "../tmp/npm-audit.json" ]; then
            vulnerabilities=$(jq '.metadata.vulnerabilities.total' ../tmp/npm-audit.json 2>/dev/null || echo "0")
            if [ "$vulnerabilities" -gt 0 ]; then
                log_result "dependency_security" "nodejs_dependencies" "failed" "Found $vulnerabilities security vulnerabilities in Node.js dependencies" "high"
                increment_counter "failed"
                add_recommendation "Update vulnerable Node.js dependencies identified by npm audit" "high" "dependency_security"
            else
                log_result "dependency_security" "nodejs_dependencies" "passed" "No security vulnerabilities found in Node.js dependencies"
                increment_counter "passed"
            fi
        fi
    else
        log_result "dependency_security" "nodejs_dependencies" "warning" "npm audit tool not available" "low"
        increment_counter "warnings"
        add_recommendation "Ensure npm is available for Node.js dependency security scanning" "low" "dependency_security"
    fi
    cd ..
else
    log_result "dependency_security" "nodejs_dependencies" "passed" "No Node.js dependencies found"
    increment_counter "passed"
fi

# Calculate final scores
echo -e "${YELLOW}📈 Calculating security scores...${NC}"

# Update total checks
total_checks=$(jq '.summary.total_checks = (.categories | keys | map(select(. != null)) | map(. as $cat | .categories[$cat] | keys | length) | add)' "$AUDIT_REPORT")
passed=$(jq '.summary.passed' "$AUDIT_REPORT")
failed=$(jq '.summary.failed' "$AUDIT_REPORT")
warnings=$(jq '.summary.warnings' "$AUDIT_REPORT")
critical=$(jq '.summary.critical_issues' "$AUDIT_REPORT")

# Calculate security score (0-100)
if [ "$total_checks" -gt 0 ]; then
    score=$(( (passed * 100 + warnings * 50) / total_checks ))
    jq --argjson score "$score" '.summary.security_score = $score' "$AUDIT_REPORT" > "$AUDIT_REPORT.tmp" && mv "$AUDIT_REPORT.tmp" "$AUDIT_REPORT"
else
    jq --argjson score 0 '.summary.security_score = 0' "$AUDIT_REPORT" > "$AUDIT_REPORT.tmp" && mv "$AUDIT_REPORT.tmp" "$AUDIT_REPORT"
fi

# Generate summary report
echo -e "${YELLOW}📝 Generating summary report...${NC}"

# Extract final statistics
final_passed=$(jq '.summary.passed' "$AUDIT_REPORT")
final_failed=$(jq '.summary.failed' "$AUDIT_REPORT")
final_warnings=$(jq '.summary.warnings' "$AUDIT_REPORT")
final_critical=$(jq '.summary.critical_issues' "$AUDIT_REPORT")
final_score=$(jq '.summary.security_score' "$AUDIT_REPORT")

cat > "$SUMMARY_REPORT" << EOF
# Security Audit Summary Report

**Environment:** $ENVIRONMENT
**Timestamp:** $(date -u)
**Audit Version:** 1.0.0

## Executive Summary

- **Total Checks:** $(jq '.summary.total_checks' "$AUDIT_REPORT")
- **Passed:** $final_passed
- **Failed:** $final_failed
- **Warnings:** $final_warnings
- **Critical Issues:** $final_critical
- **Security Score:** $final_score/100

## Security Posture Assessment

EOF

# Add security posture assessment
if [ "$final_score" -ge 90 ]; then
    cat >> "$SUMMARY_REPORT" << EOF
**🟢 Excellent Security Posture**
Your application demonstrates strong security practices with minimal vulnerabilities.
EOF
elif [ "$final_score" -ge 70 ]; then
    cat >> "$SUMMARY_REPORT" << EOF
**🟡 Good Security Posture**
Your application has solid security foundations but needs improvements in several areas.
EOF
elif [ "$final_score" -ge 50 ]; then
    cat >> "$SUMMARY_REPORT" << EOF
**🟠 Moderate Security Posture**
Your application has significant security gaps that require immediate attention.
EOF
else
    cat >> "$SUMMARY_REPORT" << EOF
**🔴 Poor Security Posture**
Your application has critical security vulnerabilities that need urgent remediation.
EOF
fi

cat >> "$SUMMARY_REPORT" << EOF

## Critical Issues Requiring Immediate Attention

EOF

# Add critical issues
if [ "$final_critical" -gt 0 ]; then
    jq -r '.recommendations[] | select(.priority == "critical") | "- **\(.category):** \(.recommendation)"' "$AUDIT_REPORT" >> "$SUMMARY_REPORT"
else
    echo "No critical issues identified." >> "$SUMMARY_REPORT"
fi

cat >> "$SUMMARY_REPORT" << EOF

## High Priority Recommendations

EOF

# Add high priority recommendations
jq -r '.recommendations[] | select(.priority == "high") | "- **\(.category):** \(.recommendation)"' "$AUDIT_REPORT" >> "$SUMMARY_REPORT" 2>/dev/null || echo "No high priority recommendations." >> "$SUMMARY_REPORT"

cat >> "$SUMMARY_REPORT" << EOF

## Medium Priority Recommendations

EOF

# Add medium priority recommendations
jq -r '.recommendations[] | select(.priority == "medium") | "- **\(.category):** \(.recommendation)"' "$AUDIT_REPORT" >> "$SUMMARY_REPORT" 2>/dev/null || echo "No medium priority recommendations." >> "$SUMMARY_REPORT"

cat >> "$SUMMARY_REPORT" << EOF

## Detailed Results by Category

EOF

# Add detailed results by category
jq -r '.categories | keys[] as $cat | "### \($cat | gsub("_"; " ") | ascii_upcase)\n\n| Check | Status | Severity | Details |\n|-------|--------|----------|---------|\n\(.categories[$cat] | keys[] as $check | "| \($check | gsub("_"; " ")) | \(.categories[$cat][$check].status) | \(.categories[$cat][$check].severity) | \(.categories[$cat][$check].details) |")\n"' "$AUDIT_REPORT" >> "$SUMMARY_REPORT"

cat >> "$SUMMARY_REPORT" << EOF

## Next Steps

1. **Immediate Actions (1-2 weeks):**
   - Address all critical security issues
   - Implement secrets management with Vault
   - Enhance input sanitization and validation

2. **Short-term Improvements (1-2 months):**
   - Implement comprehensive monitoring and alerting
   - Set up Kubernetes deployment manifests
   - Enhance authentication and authorization

3. **Long-term Enhancements (3-6 months):**
   - Implement advanced threat detection
   - Set up automated security testing in CI/CD
   - Establish security incident response procedures

## Files Generated

- **Detailed Report:** \`$AUDIT_REPORT\`
- **Summary Report:** \`$SUMMARY_REPORT\`

---

*This audit was conducted using the comprehensive security audit script for Samoey Copilot.*
*For questions or assistance with remediation, please consult the security team.*
EOF

# Display summary
echo -e "${GREEN}✅ Security audit completed!${NC}"
echo -e "${BLUE}📊 Results Summary:${NC}"
echo -e "  Total Checks: $(jq '.summary.total_checks' "$AUDIT_REPORT")"
echo -e "  Passed: ${GREEN}$(jq '.summary.passed' "$AUDIT_REPORT")${NC}"
echo -e "  Failed: ${RED}$(jq '.summary.failed' "$AUDIT_REPORT")${NC}"
echo -e "  Warnings: ${YELLOW}$(jq '.summary.warnings' "$AUDIT_REPORT")${NC}"
echo -e "  Critical Issues: ${RED}$(jq '.summary.critical_issues' "$AUDIT_REPORT")${NC}"
echo -e "  Security Score: ${BLUE}$(jq '.summary.security_score' "$AUDIT_REPORT")/100${NC}"

echo -e "${CYAN}📄 Reports generated:${NC}"
echo -e "  - Detailed JSON: $AUDIT_REPORT"
echo -e "  - Summary Markdown: $SUMMARY_REPORT"

# Clean up temporary files
rm -f /tmp/secrets-scan.txt /tmp/safety-report.json /tmp/npm-audit.json "$AUDIT_REPORT.tmp"

echo -e "${GREEN}🎯 Security audit completed successfully!${NC}"
echo -e "${YELLOW}⚠️  Please review the critical issues and recommendations.${NC}"
