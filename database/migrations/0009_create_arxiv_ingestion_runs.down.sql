BEGIN;

-- Drop arxiv ingestion tracking tables in reverse order

-- Drop indexes first (though CASCADE would handle them)
DROP INDEX IF EXISTS idx_arxiv_papers_status_run;
DROP INDEX IF EXISTS idx_arxiv_papers_processing_order;
DROP INDEX IF EXISTS idx_arxiv_papers_status;
DROP INDEX IF EXISTS idx_arxiv_papers_paper_id;
DROP INDEX IF EXISTS idx_arxiv_papers_arxiv_id;
DROP INDEX IF EXISTS idx_arxiv_papers_run_id;

-- Drop paper tracking table
DROP TABLE IF EXISTS arxiv_ingestion_papers CASCADE;

-- Drop run tracking indexes
DROP INDEX IF EXISTS idx_arxiv_runs_status_started;
DROP INDEX IF EXISTS idx_arxiv_runs_completed_at;
DROP INDEX IF EXISTS idx_arxiv_runs_started_at;
DROP INDEX IF EXISTS idx_arxiv_runs_status;
DROP INDEX IF EXISTS idx_arxiv_runs_execution_date;
DROP INDEX IF EXISTS idx_arxiv_runs_dag_id;
DROP INDEX IF EXISTS idx_arxiv_runs_run_id;

-- Drop run tracking table
DROP TABLE IF EXISTS arxiv_ingestion_runs CASCADE;

COMMIT;

