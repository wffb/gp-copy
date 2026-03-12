DROP INDEX IF EXISTS idx_article_score_calculated_at;
DROP INDEX IF EXISTS idx_article_score_stale;
DROP INDEX IF EXISTS idx_article_score_user_final_score;
DROP INDEX IF EXISTS idx_article_score_article_id;
DROP INDEX IF EXISTS idx_article_score_user_id;

DROP TABLE IF EXISTS article_score CASCADE;