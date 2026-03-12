-- Add template_content field to prompts table for flexible prompt templating
ALTER TABLE prompts ADD COLUMN template_content TEXT NOT NULL DEFAULT '';

-- Add prompt_metadata field for prompt configuration (temperature, max_tokens, etc.)
ALTER TABLE prompts ADD COLUMN prompt_metadata JSONB DEFAULT '{}'::jsonb;

-- Add version field for prompt versioning
ALTER TABLE prompts ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- Add is_active field to support multiple versions
ALTER TABLE prompts ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- Index for finding active prompts by type and name
CREATE INDEX ix_prompts_type_active ON prompts(type, is_active) WHERE is_active = true;
CREATE INDEX ix_prompts_name_version ON prompts(name, version);

-- Comments for documentation
COMMENT ON COLUMN prompts.template_content IS 'Jinja2 template content for prompt rendering';
COMMENT ON COLUMN prompts.prompt_metadata IS 'Prompt configuration (temperature, max_tokens, model preferences)';
COMMENT ON COLUMN prompts.version IS 'Version number for A/B testing and rollback';
COMMENT ON COLUMN prompts.is_active IS 'Whether this prompt version is currently active';

