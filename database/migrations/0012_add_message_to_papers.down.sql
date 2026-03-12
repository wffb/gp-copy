-- Remove message column and index from papers table
DROP INDEX IF EXISTS ix_papers_message;
ALTER TABLE papers DROP COLUMN IF EXISTS message;

