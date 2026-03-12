BEGIN;

-- Drop new indexes
DROP INDEX IF EXISTS idx_fetch_history_run_id;
DROP INDEX IF EXISTS idx_fetch_history_arxiv_id;
DROP INDEX IF EXISTS idx_fetch_history_paper_id;
DROP INDEX IF EXISTS idx_fetch_history_status;
DROP INDEX IF EXISTS idx_fetch_history_status_run;

-- Drop new unique constraint
ALTER TABLE arxiv_fetch_history DROP CONSTRAINT IF EXISTS uq_fetch_history_run_arxiv;

-- Drop new paper_request column
ALTER TABLE arxiv_fetch_history DROP COLUMN IF EXISTS paper_request;

-- Rename paper_response back to api_response
ALTER TABLE arxiv_fetch_history RENAME COLUMN paper_response TO api_response;

-- Add back old columns (with defaults)
ALTER TABLE arxiv_fetch_history ADD COLUMN processing_order INTEGER;
ALTER TABLE arxiv_fetch_history ADD COLUMN title TEXT;
ALTER TABLE arxiv_fetch_history ADD COLUMN primary_category VARCHAR(50);

-- Rename table back
ALTER TABLE arxiv_fetch_history RENAME TO arxiv_ingestion_papers;

-- Recreate old indexes
CREATE INDEX idx_arxiv_papers_run_id ON arxiv_ingestion_papers(run_id);
CREATE INDEX idx_arxiv_papers_arxiv_id ON arxiv_ingestion_papers(arxiv_id);
CREATE INDEX idx_arxiv_papers_paper_id ON arxiv_ingestion_papers(paper_id);
CREATE INDEX idx_arxiv_papers_status ON arxiv_ingestion_papers(status);
CREATE INDEX idx_arxiv_papers_processing_order ON arxiv_ingestion_papers(run_id, processing_order);
CREATE INDEX idx_arxiv_papers_status_run ON arxiv_ingestion_papers(status, run_id);

-- Recreate old unique constraint
ALTER TABLE arxiv_ingestion_papers ADD CONSTRAINT uq_run_arxiv_id UNIQUE (run_id, arxiv_id);

-- Restore old comments
COMMENT ON TABLE arxiv_ingestion_papers IS 'Track individual paper processing within each ingestion run';
COMMENT ON COLUMN arxiv_ingestion_papers.status IS 'Processing status';
COMMENT ON COLUMN arxiv_ingestion_papers.api_response IS 'Raw API response for debugging';

COMMIT;

