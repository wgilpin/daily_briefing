-- Initial database schema for Unified Feed App
-- Migration: 001_initial.sql
-- Created: 2026-01-30

-- Feed items from all sources
CREATE TABLE IF NOT EXISTS feed_items (
    id VARCHAR(255) PRIMARY KEY,  -- source_type:source_id
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    item_date TIMESTAMP NOT NULL,
    summary TEXT,
    link TEXT,
    metadata JSONB DEFAULT '{}',
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_feed_items_source ON feed_items(source_type);
CREATE INDEX IF NOT EXISTS idx_feed_items_date ON feed_items(item_date DESC);

-- Source configurations
CREATE TABLE IF NOT EXISTS source_configs (
    source_type VARCHAR(50) PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    last_refresh TIMESTAMP,
    last_error TEXT,
    settings JSONB DEFAULT '{}',
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Application settings (key-value)
CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- OAuth tokens (encrypted)
CREATE TABLE IF NOT EXISTS oauth_tokens (
    provider VARCHAR(50) PRIMARY KEY,  -- e.g., 'gmail'
    encrypted_token TEXT NOT NULL,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Insert default source configurations
INSERT INTO source_configs (source_type, enabled, settings)
VALUES
    ('zotero', true, '{}'),
    ('newsletter', true, '{}')
ON CONFLICT (source_type) DO NOTHING;

-- Insert default app settings
INSERT INTO app_settings (key, value)
VALUES
    ('default_days_lookback', '7'),
    ('page_size', '50'),
    ('refresh_timeout_seconds', '60')
ON CONFLICT (key) DO NOTHING;
