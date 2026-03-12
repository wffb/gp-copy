-- Migration: Create schema_migrations tracking table
-- This is a special migration that must be run first to track all subsequent migrations
-- It should be idempotent and safe to run multiple times

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_version_format CHECK (version ~ '^[0-9]{4}_.*')
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at DESC);

-- Add comment to explain the table
COMMENT ON TABLE schema_migrations IS 'Tracks which database migrations have been applied';
COMMENT ON COLUMN schema_migrations.version IS 'Migration file name without .up.sql extension';
COMMENT ON COLUMN schema_migrations.applied_at IS 'Timestamp when the migration was applied';

