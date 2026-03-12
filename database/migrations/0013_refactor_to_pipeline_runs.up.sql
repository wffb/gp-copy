-- Refactor arxiv_ingestion_runs to generic pipeline_runs table
-- This makes it flexible for any DAG type (ingestion, quality filter, future pipelines)

-- Step 1: Rename table
ALTER TABLE arxiv_ingestion_runs RENAME TO pipeline_runs;

-- Step 2: Add new flexible fields
ALTER TABLE pipeline_runs ADD COLUMN pipeline_type VARCHAR(50) NOT NULL DEFAULT 'arxiv_ingestion';
ALTER TABLE pipeline_runs ADD COLUMN metrics JSONB;

-- Step 3: Migrate existing data to new structure
-- Move specific metrics into flexible JSONB metrics field
UPDATE pipeline_runs SET metrics = jsonb_build_object(
    'search_query', search_query,
    'categories', categories,
    'sort_by', sort_by,
    'sort_order', sort_order,
    'start_index', start_index,
    'max_results', max_results,
    'total_available', total_available,
    'papers_fetched', papers_fetched,
    'papers_new', papers_new,
    'papers_updated', papers_updated,
    'papers_skipped', papers_skipped,
    'papers_failed', papers_failed,
    'api_calls_made', api_calls_made
);

-- Step 4: Drop old specific columns (data already in metrics JSONB)
ALTER TABLE pipeline_runs DROP COLUMN search_query;
ALTER TABLE pipeline_runs DROP COLUMN categories;
ALTER TABLE pipeline_runs DROP COLUMN sort_by;
ALTER TABLE pipeline_runs DROP COLUMN sort_order;
ALTER TABLE pipeline_runs DROP COLUMN start_index;
ALTER TABLE pipeline_runs DROP COLUMN max_results;
ALTER TABLE pipeline_runs DROP COLUMN total_available;
ALTER TABLE pipeline_runs DROP COLUMN papers_fetched;
ALTER TABLE pipeline_runs DROP COLUMN papers_new;
ALTER TABLE pipeline_runs DROP COLUMN papers_updated;
ALTER TABLE pipeline_runs DROP COLUMN papers_skipped;
ALTER TABLE pipeline_runs DROP COLUMN papers_failed;
ALTER TABLE pipeline_runs DROP COLUMN api_calls_made;

-- Step 5: Update indexes to reflect new table name
DROP INDEX IF EXISTS idx_arxiv_runs_run_id;
DROP INDEX IF EXISTS idx_arxiv_runs_dag_id;
DROP INDEX IF EXISTS idx_arxiv_runs_execution_date;
DROP INDEX IF EXISTS idx_arxiv_runs_status;
DROP INDEX IF EXISTS idx_arxiv_runs_started_at;
DROP INDEX IF EXISTS idx_arxiv_runs_completed_at;
DROP INDEX IF EXISTS idx_arxiv_runs_status_started;

CREATE INDEX idx_pipeline_runs_run_id ON pipeline_runs(run_id);
CREATE INDEX idx_pipeline_runs_dag_id ON pipeline_runs(dag_id);
CREATE INDEX idx_pipeline_runs_pipeline_type ON pipeline_runs(pipeline_type);
CREATE INDEX idx_pipeline_runs_execution_date ON pipeline_runs(execution_date DESC);
CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC);
CREATE INDEX idx_pipeline_runs_completed_at ON pipeline_runs(completed_at DESC);
CREATE INDEX idx_pipeline_runs_status_started ON pipeline_runs(status, started_at DESC);
CREATE INDEX idx_pipeline_runs_type_status ON pipeline_runs(pipeline_type, status);

-- Step 6: Update foreign key constraint in arxiv_fetch_history
ALTER TABLE arxiv_fetch_history 
    DROP CONSTRAINT IF EXISTS arxiv_fetch_history_run_id_fkey;

ALTER TABLE arxiv_fetch_history 
    ADD CONSTRAINT arxiv_fetch_history_run_id_fkey 
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(id) ON DELETE CASCADE;

-- Step 7: Add comments
COMMENT ON TABLE pipeline_runs IS 'Generic pipeline/DAG run tracking for all pipeline types';
COMMENT ON COLUMN pipeline_runs.pipeline_type IS 'Type of pipeline: arxiv_ingestion, quality_filter, etc.';
COMMENT ON COLUMN pipeline_runs.metrics IS 'Flexible JSONB field for pipeline-specific metrics and configuration';

