-- Drop indexes
DROP INDEX IF EXISTS ix_prompts_type_active;
DROP INDEX IF EXISTS ix_prompts_name_version;

-- Drop columns
ALTER TABLE prompts DROP COLUMN IF EXISTS is_active;
ALTER TABLE prompts DROP COLUMN IF EXISTS version;
ALTER TABLE prompts DROP COLUMN IF EXISTS prompt_metadata;
ALTER TABLE prompts DROP COLUMN IF EXISTS template_content;

