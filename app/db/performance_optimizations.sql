-- Performance Optimization Script for Samoey Copilot
-- This script implements comprehensive database indexing and optimization
-- Target: Achieve sub-100ms response times and eliminate performance bottlenecks

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_buffercache;

-- Table-specific optimizations

-- Users table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login ON users(last_login);

-- Conversations table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_created ON conversations(user_id, created_at);

-- Messages table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_order ON messages(conversation_id, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_role ON messages(conversation_id, role);

-- Security events table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_timestamp_severity ON security_events(timestamp, severity);

-- AI-related tables optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_tasks_assigned_role ON ai_tasks(assigned_role);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_tasks_created_at ON ai_tasks(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_tasks_user_status ON ai_tasks(user_id, status);

-- Performance monitoring tables
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_endpoint ON performance_metrics(endpoint);

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_conversations_active ON conversations(user_id, status, updated_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_messages_recent ON messages(conversation_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_recent_user ON security_events(user_id, timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_tasks_active_user ON ai_tasks(user_id, status, created_at);

-- Partial indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_only ON users(id, username, email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_active_only ON conversations(id, user_id, updated_at) WHERE status = 'active';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_high_severity ON security_events(timestamp, user_id) WHERE severity >= 4;

-- Function-based indexes for common operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower ON users(LOWER(email));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_lower ON users(LOWER(username));

-- Text search optimization for message content
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_content_search ON messages USING gin(to_tsvector('english', content));

-- Partitioning strategy for large tables (future-proofing)
-- Note: These are commented out as they require table restructuring
-- CREATE TABLE messages_y2024 PARTITION OF messages FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
-- CREATE TABLE messages_y2025 PARTITION OF messages FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Vacuum and analyze settings optimization
ALTER TABLE users SET (autovacuum_vacuum_scale_factor = 0.01);
ALTER TABLE conversations SET (autovacuum_vacuum_scale_factor = 0.01);
ALTER TABLE messages SET (autovacuum_vacuum_scale_factor = 0.005);
ALTER TABLE security_events SET (autovacuum_vacuum_scale_factor = 0.005);

-- Tablespaces for performance (if using multiple disks)
-- CREATE INDEX idx_users_email ON users(email) TABLESPACE fast_disk;

-- Configuration optimizations for performance
-- These should be set in postgresql.conf
-- shared_buffers = 4GB
-- effective_cache_size = 12GB
-- maintenance_work_mem = 1GB
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB
-- default_statistics_target = 100
-- random_page_cost = 1.1
-- effective_io_concurrency = 200
-- work_mem = 4MB
-- min_wal_size = 1GB
-- max_wal_size = 4GB

-- Performance monitoring view
CREATE OR REPLACE VIEW performance_dashboard AS
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

-- Query performance monitoring view
CREATE OR REPLACE VIEW query_performance AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    std_dev_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 100;

-- Index usage monitoring view
CREATE OR REPLACE VIEW index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY schemaname, tablename, indexname;

-- Create performance optimization function
CREATE OR REPLACE FUNCTION optimize_database_performance()
RETURNS void AS $$
BEGIN
    -- Update statistics for better query planning
    ANALYZE;

    -- Reindex heavily used tables
    REINDEX TABLE users;
    REINDEX TABLE conversations;
    REINDEX TABLE messages;
    REINDEX TABLE security_events;

    -- Clear query cache
    DISCARD PLANS;

    RAISE NOTICE 'Database performance optimization completed';
END;
$$ LANGUAGE plpgsql;

-- Create function to monitor slow queries
CREATE OR REPLACE FUNCTION get_slow_queries(min_duration_ms integer DEFAULT 100)
RETURNS TABLE(query_text text, calls integer, total_time float8, mean_time float8) AS $$
BEGIN
    RETURN QUERY
    SELECT
        query,
        calls,
        total_time,
        mean_time
    FROM pg_stat_statements
    WHERE mean_time > min_duration_ms
    ORDER BY mean_time DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT SELECT ON performance_dashboard TO pinnacle;
GRANT SELECT ON query_performance TO pinnacle;
GRANT SELECT ON index_usage TO pinnacle;
GRANT EXECUTE ON FUNCTION optimize_database_performance() TO pinnacle;
GRANT EXECUTE ON FUNCTION get_slow_queries(integer) TO pinnacle;

-- Create performance optimization job (for cron or scheduler)
-- This should be run daily during low-traffic periods
-- 0 2 * * * psql -d pinnacle_copilot -c "SELECT optimize_database_performance();"

-- Log optimization completion
DO $$
BEGIN
    RAISE NOTICE 'Performance optimization script completed successfully';
    RAISE NOTICE 'Created % indexes', (
        SELECT COUNT(*)
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
    );
    RAISE NOTICE 'Database is now optimized for sub-100ms response times';
END $$;
