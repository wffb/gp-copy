CREATE TABLE IF NOT EXISTS user_read_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    first_read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- First time article was read
    last_read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- Most recent read time

    -- Prevent duplicate entries
    CONSTRAINT uq_user_read_history UNIQUE (user_id, article_id)
);

-- Indexes for read history queries
CREATE INDEX idx_user_read_history_user_id
    ON user_read_history(user_id);

CREATE INDEX idx_user_read_history_article_id
    ON user_read_history(article_id);

CREATE INDEX idx_user_read_history_recent
    ON user_read_history(user_id, last_read_at DESC);

-- Composite index for scoring queries
CREATE INDEX idx_user_read_history_user_article
    ON user_read_history(user_id, article_id);