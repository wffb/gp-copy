CREATE TABLE bookmark (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    article_id UUID NOT NULL,
    CONSTRAINT uq_user_article UNIQUE (user_id, article_id)
);

CREATE INDEX ix_user_id_article_id ON bookmark (user_id, article_id);
