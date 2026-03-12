-- Rollback: Restore arxiv_ingestion_runs structure

-- Step 1: Restore specific columns from metrics JSONB
ALTER TABLE pipeline_runs ADD COLUMN search_query TEXT;
ALTER TABLE pipeline_runs ADD COLUMN categories VARCHAR(255)[] DEFAULT '{}';
ALTER TABLE pipeline_runs ADD COLUMN sort_by VARCHAR(50);
ALTER TABLE pipeline_runs ADD COLUMN sort_order VARCHAR(50);
ALTER TABLE pipeline_runs ADD COLUMN start_index INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN max_results INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN total_available INTEGER;
ALTER TABLE pipeline_runs ADD COLUMN papers_fetched INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN papers_new INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN papers_updated INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN papers_skipped INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN papers_failed INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN api_calls_made INTEGER DEFAULT 0;

-- Step 2: Restore data from JSONB to columns
UPDATE pipeline_runs SET
    search_query = metrics->>'search_query',
    categories = ARRAY(SELECT jsonb_array_elements_text(metrics->'categories')),
    sort_by = metrics->>'sort_by',
    sort_order = metrics->>'sort_order',
    start_index = COALESCE((metrics->>'start_index')::INTEGER, 0),
    max_results = COALESCE((metrics->>'max_results')::INTEGER, 0),
    total_available = (metrics->>'total_available')::INTEGER,
    papers_fetched = COALESCE((metrics->>'papers_fetched')::INTEGER, 0),
    papers_new = COALESCE((metrics->>'papers_new')::INTEGER, 0),
    papers_updated = COALESCE((metrics->>'papers_updated')::INTEGER, 0),
    papers_skipped = COALESCE((metrics->>'papers_skipped')::INTEGER, 0),
    papers_failed = COALESCE((metrics->>'papers_failed')::INTEGER, 0),
    api_calls_made = COALESCE((metrics->>'api_calls_made')::INTEGER, 0)
WHERE metrics IS NOT NULL;

-- Step 3: Drop new flexible fields
ALTER TABLE pipeline_runs DROP COLUMN pipeline_type;
ALTER TABLE pipeline_runs DROP COLUMN metrics;

-- Step 4: Rename table back
ALTER TABLE pipeline_runs RENAME TO arxiv_ingestion_runs;

-- Step 5: Restore original indexes
DROP INDEX IF EXISTS idx_pipeline_runs_run_id;
DROP INDEX IF EXISTS idx_pipeline_runs_dag_id;
DROP INDEX IF EXISTS idx_pipeline_runs_pipeline_type;
DROP INDEX IF EXISTS idx_pipeline_runs_execution_date;
DROP INDEX IF EXISTS idx_pipeline_runs_status;
DROP INDEX IF EXISTS idx_pipeline_runs_started_at;
DROP INDEX IF EXISTS idx_pipeline_runs_completed_at;
DROP INDEX IF EXISTS idx_pipeline_runs_status_started;
DROP INDEX IF EXISTS idx_pipeline_runs_type_status;

CREATE INDEX idx_arxiv_runs_run_id ON arxiv_ingestion_runs(run_id);
CREATE INDEX idx_arxiv_runs_dag_id ON arxiv_ingestion_runs(dag_id);
CREATE INDEX idx_arxiv_runs_execution_date ON arxiv_ingestion_runs(execution_date DESC);
CREATE INDEX idx_arxiv_runs_status ON arxiv_ingestion_runs(status);
CREATE INDEX idx_arxiv_runs_started_at ON arxiv_ingestion_runs(started_at DESC);
CREATE INDEX idx_arxiv_runs_completed_at ON arxiv_ingestion_runs(completed_at DESC);
CREATE INDEX idx_arxiv_runs_status_started ON arxiv_ingestion_runs(status, started_at DESC);

-- Step 6: Update foreign key back
ALTER TABLE arxiv_fetch_history 
    DROP CONSTRAINT IF EXISTS arxiv_fetch_history_run_id_fkey;

ALTER TABLE arxiv_fetch_history 
    ADD CONSTRAINT arxiv_fetch_history_run_id_fkey 
    FOREIGN KEY (run_id) REFERENCES arxiv_ingestion_runs(id) ON DELETE CASCADE;

