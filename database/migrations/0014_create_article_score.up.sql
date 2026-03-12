CREATE TABLE IF NOT EXISTS article_score (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    final_score FLOAT NOT NULL DEFAULT 0.0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- When score was calculated

    -- Prevent duplicate scores
    CONSTRAINT uq_article_score UNIQUE (user_id, article_id)
);

-- Indexes for score queries
CREATE INDEX idx_article_score_user_id
    ON article_score(user_id);

CREATE INDEX idx_article_score_article_id
    ON article_score(article_id);

-- Most important index: fetch ranked articles for user
CREATE INDEX idx_article_score_user_final_score
    ON article_score(user_id, final_score DESC);

-- Index for background job: find scores to update
CREATE INDEX idx_article_score_calculated_at
    ON article_score(calculated_at);