CREATE TABLE IF NOT EXISTS user_more_like_this (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate preferences
    CONSTRAINT uq_user_more_like_this UNIQUE (user_id, article_id)
);

-- Indexes for preference queries
CREATE INDEX idx_user_more_like_this_user_id
    ON user_more_like_this(user_id);

CREATE INDEX idx_user_more_like_this_article_id
    ON user_more_like_this(article_id);

CREATE INDEX idx_user_more_like_this_created
    ON user_more_like_this(user_id, created_at DESC);