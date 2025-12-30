-- VOID Suite License Tracking Database Schema
--
-- This schema supports license activation tracking, usage monitoring,
-- and audit logging for compliance.
--
-- PROPRIETARY SOFTWARE
-- Copyright (c) 2024 Roach Labs. All rights reserved.
-- Made by James Michael Roach Jr.

-- ============================================================================
-- LICENSE ACTIVATIONS TABLE
-- ============================================================================
-- Tracks device activations for license management

CREATE TABLE IF NOT EXISTS license_activations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- License information
    license_key TEXT NOT NULL,
    license_type TEXT NOT NULL CHECK(license_type IN ('trial', 'personal', 'professional', 'enterprise')),
    customer_email TEXT,
    
    -- Device information
    device_fingerprint TEXT NOT NULL,
    device_name TEXT,
    os_type TEXT,
    os_version TEXT,
    hostname TEXT,
    
    -- Activation tracking
    activated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deactivated_at DATETIME,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    
    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'deactivated', 'suspended')),
    
    -- Audit
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    UNIQUE(license_key, device_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_license_activations_key 
ON license_activations(license_key);

CREATE INDEX IF NOT EXISTS idx_license_activations_fingerprint 
ON license_activations(device_fingerprint);

CREATE INDEX IF NOT EXISTS idx_license_activations_status 
ON license_activations(status);

CREATE INDEX IF NOT EXISTS idx_license_activations_active 
ON license_activations(is_active);


-- ============================================================================
-- USAGE TRACKING TABLE
-- ============================================================================
-- Tracks software usage for analytics and compliance

CREATE TABLE IF NOT EXISTS usage_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Session information
    session_id TEXT NOT NULL,
    activation_id INTEGER,
    license_key TEXT NOT NULL,
    device_fingerprint TEXT NOT NULL,
    
    -- Usage details
    event_type TEXT NOT NULL, -- startup, shutdown, feature_used, command_executed, etc.
    event_name TEXT, -- specific feature or command name
    event_data TEXT, -- JSON data with additional details
    
    -- Duration (for shutdown events)
    duration_seconds INTEGER,
    
    -- Timestamp
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Context
    os_type TEXT,
    os_version TEXT,
    void_version TEXT,
    
    -- Foreign key
    FOREIGN KEY (activation_id) REFERENCES license_activations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_session 
ON usage_tracking(session_id);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_license 
ON usage_tracking(license_key);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_timestamp 
ON usage_tracking(timestamp);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_event_type 
ON usage_tracking(event_type);


-- ============================================================================
-- DEVICE ACCESS LOG TABLE
-- ============================================================================
-- Audit log for device access (compliance requirement)

CREATE TABLE IF NOT EXISTS device_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Session and license
    session_id TEXT NOT NULL,
    license_key TEXT NOT NULL,
    user_fingerprint TEXT NOT NULL,
    
    -- Accessed device information
    device_make TEXT,
    device_model TEXT,
    device_imei TEXT,
    device_serial TEXT,
    
    -- Operation details
    operation_type TEXT NOT NULL, -- frp_bypass, edl_flash, backup, etc.
    operation_details TEXT, -- JSON with additional info
    
    -- Authorization
    authorization_ref TEXT, -- Reference to authorization document
    authorization_verified BOOLEAN DEFAULT 0,
    
    -- Outcome
    status TEXT NOT NULL CHECK(status IN ('started', 'in_progress', 'completed', 'failed', 'cancelled')),
    result TEXT, -- Success/failure details
    
    -- Timestamps
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration_seconds INTEGER,
    
    -- Compliance
    requires_audit BOOLEAN DEFAULT 1,
    audit_exported BOOLEAN DEFAULT 0,
    audit_exported_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_device_access_session 
ON device_access_log(session_id);

CREATE INDEX IF NOT EXISTS idx_device_access_license 
ON device_access_log(license_key);

CREATE INDEX IF NOT EXISTS idx_device_access_operation 
ON device_access_log(operation_type);

CREATE INDEX IF NOT EXISTS idx_device_access_timestamp 
ON device_access_log(started_at);

CREATE INDEX IF NOT EXISTS idx_device_access_audit 
ON device_access_log(requires_audit, audit_exported);


-- ============================================================================
-- FEATURE USAGE TABLE
-- ============================================================================
-- Tracks which features are used (for analytics)

CREATE TABLE IF NOT EXISTS feature_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- License and device
    license_key TEXT NOT NULL,
    device_fingerprint TEXT NOT NULL,
    
    -- Feature information
    feature_category TEXT NOT NULL, -- device_management, backup, frp, edl, etc.
    feature_name TEXT NOT NULL, -- Specific feature
    
    -- Usage count
    usage_count INTEGER NOT NULL DEFAULT 1,
    
    -- Timestamps
    first_used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(license_key, device_fingerprint, feature_category, feature_name)
);

CREATE INDEX IF NOT EXISTS idx_feature_usage_license 
ON feature_usage(license_key);

CREATE INDEX IF NOT EXISTS idx_feature_usage_category 
ON feature_usage(feature_category);


-- ============================================================================
-- ERROR LOG TABLE
-- ============================================================================
-- Tracks errors and crashes for debugging

CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Session information
    session_id TEXT NOT NULL,
    license_key TEXT,
    device_fingerprint TEXT,
    
    -- Error details
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_traceback TEXT,
    
    -- Context
    operation TEXT, -- What was being done when error occurred
    context_data TEXT, -- JSON with additional context
    
    -- System information
    os_type TEXT,
    os_version TEXT,
    void_version TEXT,
    python_version TEXT,
    
    -- Timestamp
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Resolution
    resolved BOOLEAN DEFAULT 0,
    resolution_notes TEXT,
    resolved_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_error_log_session 
ON error_log(session_id);

CREATE INDEX IF NOT EXISTS idx_error_log_type 
ON error_log(error_type);

CREATE INDEX IF NOT EXISTS idx_error_log_timestamp 
ON error_log(timestamp);


-- ============================================================================
-- LICENSE TRANSFER HISTORY TABLE
-- ============================================================================
-- Tracks license transfers between devices

CREATE TABLE IF NOT EXISTS license_transfer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- License information
    license_key TEXT NOT NULL,
    license_type TEXT NOT NULL,
    
    -- Transfer details
    from_device_fingerprint TEXT,
    to_device_fingerprint TEXT NOT NULL,
    transfer_reason TEXT,
    
    -- Authorization
    authorized_by TEXT, -- Email of person authorizing transfer
    authorization_notes TEXT,
    
    -- Timestamp
    transferred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transfer_history_license 
ON license_transfer_history(license_key);

CREATE INDEX IF NOT EXISTS idx_transfer_history_timestamp 
ON license_transfer_history(transferred_at);


-- ============================================================================
-- TELEMETRY OPT-IN TABLE
-- ============================================================================
-- Tracks telemetry consent

CREATE TABLE IF NOT EXISTS telemetry_consent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Device identification
    device_fingerprint TEXT NOT NULL UNIQUE,
    anonymous_id TEXT NOT NULL,
    
    -- Consent details
    opted_in BOOLEAN NOT NULL DEFAULT 0,
    crash_reporting BOOLEAN NOT NULL DEFAULT 0,
    usage_stats BOOLEAN NOT NULL DEFAULT 0,
    
    -- Timestamps
    opted_in_at DATETIME,
    opted_out_at DATETIME,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- AUDIT EXPORT LOG TABLE
-- ============================================================================
-- Tracks when audit logs are exported (compliance)

CREATE TABLE IF NOT EXISTS audit_export_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Export details
    export_type TEXT NOT NULL CHECK(export_type IN ('device_access', 'usage', 'full')),
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    
    -- Export info
    record_count INTEGER NOT NULL,
    export_file_path TEXT,
    export_format TEXT, -- csv, json, pdf
    
    -- Export metadata
    exported_by TEXT, -- User/admin who exported
    export_reason TEXT, -- Audit, compliance, investigation, etc.
    
    -- Timestamp
    exported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_export_timestamp 
ON audit_export_log(exported_at);


-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active licenses view
CREATE VIEW IF NOT EXISTS v_active_licenses AS
SELECT 
    license_key,
    license_type,
    customer_email,
    COUNT(*) as active_devices,
    MAX(last_seen) as last_activity
FROM license_activations
WHERE is_active = 1
GROUP BY license_key;


-- Device access summary view
CREATE VIEW IF NOT EXISTS v_device_access_summary AS
SELECT 
    license_key,
    operation_type,
    COUNT(*) as operation_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(started_at) as last_operation
FROM device_access_log
GROUP BY license_key, operation_type;


-- Feature usage summary view
CREATE VIEW IF NOT EXISTS v_feature_usage_summary AS
SELECT 
    feature_category,
    feature_name,
    COUNT(DISTINCT license_key) as unique_licenses,
    SUM(usage_count) as total_usage,
    MAX(last_used_at) as last_used
FROM feature_usage
GROUP BY feature_category, feature_name
ORDER BY total_usage DESC;


-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATE
-- ============================================================================

-- Update last_seen timestamp on usage tracking insert
CREATE TRIGGER IF NOT EXISTS update_license_last_seen
AFTER INSERT ON usage_tracking
FOR EACH ROW
WHEN NEW.event_type = 'startup'
BEGIN
    UPDATE license_activations
    SET last_seen = NEW.timestamp,
        updated_at = CURRENT_TIMESTAMP
    WHERE license_key = NEW.license_key 
    AND device_fingerprint = NEW.device_fingerprint;
END;


-- Update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_license_activations_timestamp
AFTER UPDATE ON license_activations
FOR EACH ROW
BEGIN
    UPDATE license_activations
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;


-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Get active devices for a license
-- SELECT * FROM license_activations 
-- WHERE license_key = 'xxx' AND is_active = 1;

-- Get device access log for compliance audit
-- SELECT * FROM device_access_log 
-- WHERE started_at BETWEEN '2024-01-01' AND '2024-12-31'
-- AND operation_type = 'frp_bypass'
-- ORDER BY started_at DESC;

-- Get most used features
-- SELECT * FROM v_feature_usage_summary LIMIT 10;

-- Find licenses with high error rates
-- SELECT license_key, COUNT(*) as error_count
-- FROM error_log
-- WHERE timestamp > datetime('now', '-7 days')
-- GROUP BY license_key
-- ORDER BY error_count DESC;


-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Clean up old usage tracking (keep last 90 days)
-- DELETE FROM usage_tracking 
-- WHERE timestamp < datetime('now', '-90 days');

-- Clean up old error logs (keep last 30 days)
-- DELETE FROM error_log 
-- WHERE timestamp < datetime('now', '-30 days') AND resolved = 1;

-- Archive old device access logs
-- INSERT INTO device_access_log_archive 
-- SELECT * FROM device_access_log 
-- WHERE completed_at < datetime('now', '-365 days');


-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- 1. Regular maintenance recommended to keep database size manageable
-- 2. Export and archive old audit logs for long-term compliance
-- 3. Use views for reporting and analytics
-- 4. Ensure GDPR compliance by allowing data deletion on request
-- 5. Encrypt database file for sensitive information
-- 6. Regular backups essential for audit trail preservation
--
-- ============================================================================
