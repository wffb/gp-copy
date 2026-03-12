BEGIN;

-- Rename table
ALTER TABLE arxiv_ingestion_papers RENAME TO arxiv_fetch_history;

-- Drop old columns
ALTER TABLE arxiv_fetch_history DROP COLUMN IF EXISTS processing_order;
ALTER TABLE arxiv_fetch_history DROP COLUMN IF EXISTS title;
ALTER TABLE arxiv_fetch_history DROP COLUMN IF EXISTS primary_category;

-- Rename api_response column to paper_response
ALTER TABLE arxiv_fetch_history RENAME COLUMN api_response TO paper_response;

-- Add new paper_request column
ALTER TABLE arxiv_fetch_history ADD COLUMN paper_request JSONB;

-- Update status column comment to reflect API statuses
COMMENT ON COLUMN arxiv_fetch_history.status IS 'API fetch status: pending, processing, success, failed';

-- Update paper_response column comment
COMMENT ON COLUMN arxiv_fetch_history.paper_response IS 'API response (raw + transformed)';

-- Update paper_request column comment
COMMENT ON COLUMN arxiv_fetch_history.paper_request IS 'API request parameters sent';

-- Update table comment
COMMENT ON TABLE arxiv_fetch_history IS 'API audit trail: Track individual arXiv API fetch requests and responses';

-- Drop old indexes
DROP INDEX IF EXISTS idx_arxiv_papers_run_id;
DROP INDEX IF EXISTS idx_arxiv_papers_arxiv_id;
DROP INDEX IF EXISTS idx_arxiv_papers_paper_id;
DROP INDEX IF EXISTS idx_arxiv_papers_status;
DROP INDEX IF EXISTS idx_arxiv_papers_processing_order;
DROP INDEX IF EXISTS idx_arxiv_papers_status_run;

-- Drop old unique constraint
ALTER TABLE arxiv_fetch_history DROP CONSTRAINT IF EXISTS uq_run_arxiv_id;

-- Create new indexes
CREATE INDEX idx_fetch_history_run_id ON arxiv_fetch_history(run_id);
CREATE INDEX idx_fetch_history_arxiv_id ON arxiv_fetch_history(arxiv_id);
CREATE INDEX idx_fetch_history_paper_id ON arxiv_fetch_history(paper_id);
CREATE INDEX idx_fetch_history_status ON arxiv_fetch_history(status);
CREATE INDEX idx_fetch_history_status_run ON arxiv_fetch_history(status, run_id);

-- Create new unique constraint
ALTER TABLE arxiv_fetch_history ADD CONSTRAINT uq_fetch_history_run_arxiv UNIQUE (run_id, arxiv_id);

-- Update status column default value
ALTER TABLE arxiv_fetch_history ALTER COLUMN status SET DEFAULT 'pending';

COMMIT;

