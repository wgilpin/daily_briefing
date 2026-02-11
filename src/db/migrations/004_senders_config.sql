-- 004_senders_config.sql
-- Migrate sender configuration from senders.json to PostgreSQL

CREATE TABLE IF NOT EXISTS senders (
    email         TEXT PRIMARY KEY,
    display_name  TEXT,
    parsing_prompt TEXT NOT NULL DEFAULT '',
    enabled       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS newsletter_config (
    setting_name  TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);
