-- Add message column to papers table for quality filter rejection reasons
ALTER TABLE papers ADD COLUMN message TEXT;

-- Index for filtering papers with messages (rejections)
CREATE INDEX ix_papers_message ON papers(message) WHERE message IS NOT NULL;

-- Comment for documentation
COMMENT ON COLUMN papers.message IS 'Quality filter rejection reason or processing message';

