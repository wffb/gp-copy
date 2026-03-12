BEGIN;

-- ===========================================
-- arXiv Ingestion Run Tracking
-- ===========================================

-- Track each DAG run for arXiv paper ingestion
CREATE TABLE arxiv_ingestion_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            VARCHAR(255) NOT NULL UNIQUE,  -- Airflow run_id
    dag_id            VARCHAR(255) NOT NULL,         -- DAG identifier (e.g., 'main_etl_dag')
    execution_date    TIMESTAMPTZ NOT NULL,          -- When DAG execution started
    
    -- Search parameters used for this run
    search_query      TEXT NOT NULL,                 -- Full search query sent to arXiv
    categories        TEXT[] NOT NULL,               -- Categories searched (e.g., ['cs.AI', 'cs.LG'])
    sort_by           VARCHAR(50),                   -- Sort criteria (submittedDate, lastUpdatedDate, relevance)
    sort_order        VARCHAR(50),                   -- Sort order (ascending, descending)
    
    -- Pagination tracking
    start_index       INTEGER NOT NULL DEFAULT 0,    -- Starting index for this run
    max_results       INTEGER NOT NULL,              -- Maximum results requested per API call
    total_available   INTEGER,                       -- Total papers available from arXiv (from opensearch:totalResults)
    
    -- Results summary
    papers_fetched    INTEGER DEFAULT 0,             -- Total papers retrieved from arXiv API
    papers_new        INTEGER DEFAULT 0,             -- New papers added to database
    papers_updated    INTEGER DEFAULT 0,             -- Existing papers updated with new versions
    papers_skipped    INTEGER DEFAULT 0,             -- Papers skipped (already up-to-date)
    papers_failed     INTEGER DEFAULT 0,             -- Papers that failed to process
    
    -- Run status
    status            VARCHAR(50) NOT NULL DEFAULT 'running',  -- running | completed | failed | partial
    error_message     TEXT,                          -- Error details if run failed
    
    -- Performance metrics
    api_calls_made    INTEGER DEFAULT 0,             -- Number of API requests made
    processing_time_seconds FLOAT,                   -- Total processing time in seconds
    
    -- Timestamps
    started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,                   -- When run finished (success or failure)
    
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for run tracking queries
CREATE INDEX idx_arxiv_runs_run_id ON arxiv_ingestion_runs(run_id);
CREATE INDEX idx_arxiv_runs_dag_id ON arxiv_ingestion_runs(dag_id);
CREATE INDEX idx_arxiv_runs_execution_date ON arxiv_ingestion_runs(execution_date DESC);
CREATE INDEX idx_arxiv_runs_status ON arxiv_ingestion_runs(status);
CREATE INDEX idx_arxiv_runs_started_at ON arxiv_ingestion_runs(started_at DESC);
CREATE INDEX idx_arxiv_runs_completed_at ON arxiv_ingestion_runs(completed_at DESC);

-- Composite index for finding recent successful runs
CREATE INDEX idx_arxiv_runs_status_started ON arxiv_ingestion_runs(status, started_at DESC);

-- ===========================================
-- Individual Paper Processing Tracking
-- ===========================================

-- Track processing of individual papers within each run
CREATE TABLE arxiv_ingestion_papers (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            UUID NOT NULL REFERENCES arxiv_ingestion_runs(id) ON DELETE CASCADE,
    
    -- Paper identification
    arxiv_id          VARCHAR(50) NOT NULL,          -- arXiv ID with version (e.g., "1903.12284v3")
    paper_id          UUID REFERENCES papers(id) ON DELETE SET NULL,  -- Link to papers table (null if failed to create)
    
    -- Processing status
    status            VARCHAR(50) NOT NULL,          -- new | updated | skipped | failed
    error_message     TEXT,                          -- Error details if processing failed
    
    -- Processing metadata
    processing_order  INTEGER,                       -- Order in which paper was processed (0-based)
    api_response      JSONB,                         -- Raw parsed API response for debugging (optional)
    
    -- Extracted metadata for reference
    title             TEXT,                          -- Paper title (for quick reference)
    primary_category  VARCHAR(50),                   -- Primary category from arXiv
    
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure unique arxiv_id per run
    CONSTRAINT uq_run_arxiv_id UNIQUE (run_id, arxiv_id)
);

-- Indexes for paper tracking queries
CREATE INDEX idx_arxiv_papers_run_id ON arxiv_ingestion_papers(run_id);
CREATE INDEX idx_arxiv_papers_arxiv_id ON arxiv_ingestion_papers(arxiv_id);
CREATE INDEX idx_arxiv_papers_paper_id ON arxiv_ingestion_papers(paper_id);
CREATE INDEX idx_arxiv_papers_status ON arxiv_ingestion_papers(status);
CREATE INDEX idx_arxiv_papers_processing_order ON arxiv_ingestion_papers(run_id, processing_order);

-- Composite index for finding failed papers
CREATE INDEX idx_arxiv_papers_status_run ON arxiv_ingestion_papers(status, run_id);

COMMIT;

