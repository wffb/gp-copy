
CREATE TABLE IF NOT EXISTS user_search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,                           -- The search query text
    last_searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- most recent search
    is_saved BOOLEAN NOT NULL DEFAULT FALSE,       -- Whether user explicitly saved this search
    saved_at TIMESTAMPTZ,                              -- most recent saved
    search_count INT NOT NULL DEFAULT 1,                 -- total times this query was searched

    -- Prevent duplicate queries per user (lower case)
    CONSTRAINT uq_user_search_query UNIQUE (user_id, query)
);

-- Indexes for search history queries
CREATE INDEX idx_user_search_history_user_id
    ON user_search_history(user_id);

CREATE INDEX idx_user_search_history_is_saved
    ON user_search_history(user_id, is_saved)
    WHERE is_saved = TRUE;

CREATE INDEX idx_user_search_history_recent
    ON user_search_history(user_id, saved_at DESC);