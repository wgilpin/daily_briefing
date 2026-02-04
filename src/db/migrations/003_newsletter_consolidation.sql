-- Migration 003: Newsletter Database Consolidation
-- Created: 2026-02-04
-- Purpose: Consolidate newsletter tracking from SQLite to PostgreSQL

-- Table for tracking processed newsletter emails
CREATE TABLE IF NOT EXISTS processed_emails (
    message_id VARCHAR(255) PRIMARY KEY,
    sender_email VARCHAR(255) NOT NULL,
    subject TEXT,
    collected_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL CHECK (status IN ('collected', 'converted', 'parsed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for processed_emails
CREATE INDEX IF NOT EXISTS idx_processed_emails_sender ON processed_emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_processed_emails_status ON processed_emails(status);
CREATE INDEX IF NOT EXISTS idx_processed_emails_processed_at ON processed_emails(processed_at DESC);

-- Table for tracking data migrations (idempotency)
CREATE TABLE IF NOT EXISTS migration_history (
    migration_name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    rows_migrated INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10, 2)
);
