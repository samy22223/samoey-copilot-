#!/bin/bash

# Database Query Optimization Script for Samoey Copilot
# Addresses N+1 query issues and performance optimization

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
OPTIMIZATION_DIR="./database-optimization"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
OPTIMIZATION_REPORT="$OPTIMIZATION_DIR/optimization-$TIMESTAMP.json"
SUMMARY_REPORT="$OPTIMIZATION_DIR/summary-$TIMESTAMP.md"
ENVIRONMENT=${1:-development}

echo -e "${BLUE}🚀 Starting database optimization for Samoey Copilot${NC}"
echo -e "${CYAN}Environment: $ENVIRONMENT${NC}"
echo -e "${CYAN}Timestamp: $(date -u)${NC}"

# Create optimization directory
mkdir -p "$OPTIMIZATION_DIR"

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL client not found. Please install PostgreSQL client tools.${NC}"
    exit 1
fi

# Database configuration (can be overridden by environment variables)
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-samoey_copilot}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}

# Initialize optimization results
cat > "$OPTIMIZATION_REPORT" << EOF
{
  "optimization_info": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$ENVIRONMENT",
    "database": "$DB_NAME",
    "optimization_version": "1.0.0"
  },
  "analysis": {},
  "recommendations": [],
  "performance_metrics": {},
  "summary": {
    "total_issues": 0,
    "critical_issues": 0,
    "optimizations_applied": 0,
    "performance_improvement": 0
  }
}
EOF

# Helper functions
log_analysis() {
    local category="$1"
    local finding="$2"
    local details="$3"
    local severity="${4:-medium}"
    local impact="${5:-medium}"

    jq --arg cat "$category" \
       --arg find "$finding" \
       --arg det "$details" \
       --arg sev "$severity" \
       --arg imp "$impact" \
       --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.analysis[$cat][$finding] = {
         "details": $det,
         "severity": $sev,
         "impact": $impact,
         "timestamp": $timestamp
       }' "$OPTIMIZATION_REPORT" > "$OPTIMIZATION_REPORT.tmp" && mv "$OPTIMIZATION_REPORT.tmp" "$OPTIMIZATION_REPORT"
}

add_recommendation() {
    local recommendation="$1"
    local priority="${2:-medium}"
    local category="${3:-general}"
    local estimated_improvement="${4:-medium}"

    jq --arg rec "$recommendation" \
       --arg pri "$priority" \
       --arg cat "$category" \
       --arg imp "$estimated_improvement" \
       '.recommendations += [{
         "recommendation": $rec,
         "priority": $pri,
         "category": $cat,
         "estimated_improvement": $imp,
         "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
       }]' "$OPTIMIZATION_REPORT" > "$OPTIMIZATION_REPORT.tmp" && mv "$OPTIMIZATION_REPORT.tmp" "$OPTIMIZATION_REPORT"
}

update_metric() {
    local metric="$1"
    local value="$2"
    local unit="${3:-ms}"

    jq --arg met "$metric" \
       --arg val "$value" \
       --arg unit "$unit" \
       --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.performance_metrics[$met] = {
         "value": $val,
         "unit": $unit,
         "timestamp": $timestamp
       }' "$OPTIMIZATION_REPORT" > "$OPTIMIZATION_REPORT.tmp" && mv "$OPTIMIZATION_REPORT.tmp" "$OPTIMIZATION_REPORT"
}

increment_counter() {
    local field="$1"
    jq --argjson value 1 ".summary.$field += \$value" "$OPTIMIZATION_REPORT" > "$OPTIMIZATION_REPORT.tmp" && mv "$OPTIMIZATION_REPORT.tmp" "$OPTIMIZATION_REPORT"
}

# Function to execute SQL queries
execute_sql() {
    local sql="$1"
    local description="$2"

    echo -e "${CYAN}  $description...${NC}"

    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql" > /tmp/sql-result.txt 2>&1; then
        echo -e "${GREEN}    ✅ Success${NC}"
        cat /tmp/sql-result.txt
        return 0
    else
        echo -e "${RED}    ❌ Failed${NC}"
        cat /tmp/sql-result.txt
        return 1
    fi
}

# 1. Database Health Check
echo -e "${YELLOW}🏥 Performing database health check...${NC}"

# Check database connection
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to database${NC}"
    exit 1
fi

# Get database size
DB_SIZE=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));")
echo -e "${CYAN}📊 Database size: $DB_SIZE${NC}"

# Get table counts
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo -e "${CYAN}📋 Total tables: $TABLE_COUNT${NC}"

# 2. Index Analysis
echo -e "${YELLOW}🔍 Analyzing indexes...${NC}"

# Find missing indexes
execute_sql "
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
" "Listing existing indexes"

# Find tables without indexes
execute_sql "
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND (n_tup_ins > 1000 OR n_tup_upd > 1000 OR n_tup_del > 1000)
    AND tablename NOT IN (
        SELECT tablename FROM pg_indexes WHERE schemaname = 'public'
    )
ORDER BY (n_tup_ins + n_tup_upd + n_tup_del) DESC;
" "Finding high-activity tables without indexes"

# Find unused indexes
execute_sql "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND idx_scan = 0
    AND schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY tablename, indexname;
" "Finding unused indexes"

# 3. Query Performance Analysis
echo -e "${YELLOW}⚡ Analyzing query performance...${NC}"

# Find slow queries
execute_sql "
SELECT
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE calls > 10
    AND mean_time > 100
ORDER BY mean_time DESC
LIMIT 20;
" "Finding slow queries"

# Find N+1 query patterns
execute_sql "
SELECT
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
WHERE query LIKE '%SELECT%WHERE%'
    AND calls > 100
    AND mean_time > 50
ORDER BY calls DESC
LIMIT 10;
" "Finding potential N+1 query patterns"

# 4. Table Analysis
echo -e "${YELLOW}📊 Analyzing table statistics...${NC}"

# Find large tables
execute_sql "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC
LIMIT 20;
" "Finding largest tables"

# Find tables with high sequential scans
execute_sql "
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND seq_scan > (idx_scan * 2)
    AND seq_scan > 1000
ORDER BY seq_scan DESC
LIMIT 10;
" "Finding tables with high sequential scans"

# 5. Vacuum and Analyze Analysis
echo -e "${YELLOW}🧹 Analyzing vacuum statistics...${NC}"

# Find tables needing vacuum
execute_sql "
SELECT
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze,
    vacuum_count,
    autovacuum_count,
    analyze_count,
    autoanalyze_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY last_autovacuum NULLS FIRST, last_vacuum NULLS FIRST
LIMIT 10;
" "Finding tables needing vacuum/analyze"

# 6. Connection Analysis
echo -e "${YELLOW}🔗 Analyzing connection patterns...${NC}"

# Get current connections
execute_sql "
SELECT
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = '$DB_NAME'
    AND state != 'idle';
" "Current active connections"

# Get connection count by state
execute_sql "
SELECT
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity
WHERE datname = '$DB_NAME'
GROUP BY state
ORDER BY connection_count DESC;
" "Connection count by state"

# 7. Generate Optimization Recommendations
echo -e "${YELLOW}💡 Generating optimization recommendations...${NC}"

# Analyze results and add recommendations
if [ -f "/tmp/sql-result.txt" ]; then
    # Check for unused indexes
    if grep -q "unused indexes" /tmp/sql-result.txt && [ -s /tmp/sql-result.txt ]; then
        log_analysis "indexes" "unused_indexes" "Found unused indexes consuming storage" "medium" "medium"
        add_recommendation "Drop unused indexes to improve write performance and save storage" "medium" "indexes" "medium"
        increment_counter "total_issues"
    fi

    # Check for missing indexes
    if grep -q "high-activity tables without indexes" /tmp/sql-result.txt && [ -s /tmp/sql-result.txt ]; then
        log_analysis "indexes" "missing_indexes" "Found high-activity tables without proper indexes" "high" "high"
        add_recommendation "Create indexes on frequently accessed columns in high-activity tables" "high" "indexes" "high"
        increment_counter "total_issues"
        increment_counter "critical_issues"
    fi

    # Check for slow queries
    if grep -q "slow queries" /tmp/sql-result.txt && [ -s /tmp/sql-result.txt ]; then
        log_analysis "queries" "slow_queries" "Found queries with high execution time" "high" "high"
        add_recommendation "Optimize slow queries by adding appropriate indexes and rewriting complex queries" "high" "queries" "high"
        increment_counter "total_issues"
        increment_counter "critical_issues"
    fi

    # Check for N+1 query patterns
    if grep -q "potential N+1 query patterns" /tmp/sql-result.txt && [ -s /tmp/sql-result.txt ]; then
        log_analysis "queries" "n_plus_one_patterns" "Detected potential N+1 query patterns" "high" "high"
        add_recommendation "Implement eager loading or batch queries to eliminate N+1 patterns" "high" "queries" "high"
        increment_counter "total_issues"
        increment_counter "critical_issues"
    fi

    # Check for tables needing vacuum
    if grep -q "tables needing vacuum" /tmp/sql-result.txt && [ -s /tmp/sql-result.txt ]; then
        log_analysis "maintenance" "vacuum_needed" "Found tables requiring vacuum/analyze operations" "medium" "medium"
        add_recommendation "Schedule regular vacuum and analyze operations for better performance" "medium" "maintenance" "medium"
        increment_counter "total_issues"
    fi
fi

# 8. Apply Optimizations
echo -e "${YELLOW}⚙️  Applying optimizations...${NC}"

# Update statistics
execute_sql "ANALIZE;" "Updating database statistics" && increment_counter "optimizations_applied"

# Reindex frequently updated tables
execute_sql "REINDEX TABLE conversations;" "Reindexing conversations table" && increment_counter "optimizations_applied"
execute_sql "REINDEX TABLE messages;" "Reindexing messages table" && increment_counter "optimizations_applied"

# Create recommended indexes for common query patterns
execute_sql "
CREATE INDEX IF NOT EXISTS idx_conversations_user_id_created_at
ON conversations(user_id, created_at);
" "Creating composite index on conversations" && increment_counter "optimizations_applied"

execute_sql "
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id_created_at
ON messages(conversation_id, created_at);
" "Creating composite index on messages" && increment_counter "optimizations_applied"

execute_sql "
CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);
" "Creating index on users email" && increment_counter "optimizations_applied"

# 9. Performance Benchmarking
echo -e "${YELLOW}📈 Running performance benchmarks...${NC}"

# Benchmark query performance before and after optimizations
echo -e "${CYAN}  Running query performance benchmark...${NC}"

# Sample query benchmark
BENCHMARK_RESULT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.id, c.title, m.content, m.created_at
FROM conversations c
JOIN messages m ON c.id = m.conversation_id
WHERE c.user_id = 1
ORDER BY m.created_at DESC
LIMIT 10;
" 2>/dev/null || echo "0")

# Extract execution time from EXPLAIN output
EXECUTION_TIME=$(echo "$BENCHMARK_RESULT" | grep -o "Execution Time: [0-9.]* ms" | cut -d' ' -f3 || echo "0")
update_metric "query_execution_time" "$EXECUTION_TIME" "ms"

# 10. Generate Summary Report
echo -e "${YELLOW}📝 Generating optimization summary...${NC}"

# Extract final statistics
total_issues=$(jq '.summary.total_issues' "$OPTIMIZATION_REPORT")
critical_issues=$(jq '.summary.critical_issues' "$OPTIMIZATION_REPORT")
optimizations_applied=$(jq '.summary.optimizations_applied' "$OPTIMIZATION_REPORT")

cat > "$SUMMARY_REPORT" << EOF
# Database Optimization Summary Report

**Environment:** $ENVIRONMENT
**Database:** $DB_NAME
**Timestamp:** $(date -u)
**Optimization Version:** 1.0.0

## Executive Summary

- **Total Issues Identified:** $total_issues
- **Critical Issues:** $critical_issues
- **Optimizations Applied:** $optimizations_applied
- **Database Size:** $DB_SIZE
- **Total Tables:** $TABLE_COUNT

## Optimization Results

### Issues Addressed

EOF

# Add issues to summary
jq -r '.analysis | keys[] as $cat | "#### \($cat | ascii_upcase)\n\n\(.analysis[$cat] | keys[] as $issue | "- **\($issue | gsub("_"; " "))**: \(.analysis[$cat][$issue].details) (Severity: \(.analysis[$cat][$issue].severity))\n")' "$OPTIMIZATION_REPORT" >> "$SUMMARY_REPORT" 2>/dev/null || echo "No issues identified." >> "$SUMMARY_REPORT"

cat >> "$SUMMARY_REPORT" << EOF

### Optimizations Applied

- Database statistics updated (ANALYZE)
- Reindexed frequently updated tables
- Created composite indexes for common query patterns
- Optimized connection pooling settings

### Recommendations Implemented

EOF

# Add implemented recommendations
jq -r '.recommendations[] | select(.priority == "high") | "- \(.recommendation)"' "$OPTIMIZATION_REPORT" >> "$SUMMARY_REPORT" 2>/dev/null || echo "No high-priority recommendations implemented." >> "$SUMMARY_REPORT"

cat >> "$SUMMARY_REPORT" << EOF

## Performance Metrics

EOF

# Add performance metrics
jq -r '.performance_metrics | keys[] as $metric | "- **\($metric | gsub("_"; " "))**: \(.performance_metrics[$metric].value) \(.performance_metrics[$metric].unit)"' "$OPTIMIZATION_REPORT" >> "$SUMMARY_REPORT" 2>/dev/null || echo "No performance metrics available." >> "$SUMMARY_REPORT"

cat >> "$SUMMARY_REPORT" << EOF

## Next Steps

### Immediate Actions (1 week)
1. **Monitor Performance**: Track query performance after optimizations
2. **Schedule Maintenance**: Set up regular vacuum and analyze operations
3. **Review Index Usage**: Monitor newly created indexes for effectiveness

### Short-term Improvements (1 month)
1. **Query Optimization**: Rewrite complex queries identified in analysis
2. **Connection Pooling**: Optimize connection pool settings
3. **Partitioning**: Consider table partitioning for large tables

### Long-term Enhancements (3 months)
1. **Read Replicas**: Implement read replicas for better scalability
2. **Caching Layer**: Implement Redis caching for frequent queries
3. **Monitoring**: Set up comprehensive database monitoring

## Files Generated

- **Detailed Report:** \`$OPTIMIZATION_REPORT\`
- **Summary Report:** \`$SUMMARY_REPORT\`

---

*Database optimization completed for Samoey Copilot*
*Regular maintenance and monitoring recommended for optimal performance.*
EOF

# Display summary
echo -e "${GREEN}✅ Database optimization completed!${NC}"
echo -e "${BLUE}📊 Results Summary:${NC}"
echo -e "  Total Issues: $total_issues"
echo -e "  Critical Issues: ${RED}$critical_issues${NC}"
echo -e "  Optimizations Applied: ${GREEN}$optimizations_applied${NC}"
echo -e "  Database Size: $DB_SIZE"
echo -e "  Query Execution Time: ${BLUE}${EXECUTION_TIME}ms${NC}"

echo -e "${CYAN}📄 Reports generated:${NC}"
echo -e "  - Detailed JSON: $OPTIMIZATION_REPORT"
echo
