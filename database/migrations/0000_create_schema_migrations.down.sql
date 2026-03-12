-- Rollback: Drop schema_migrations tracking table
-- WARNING: This will remove all migration history tracking

DROP TABLE IF EXISTS schema_migrations;

