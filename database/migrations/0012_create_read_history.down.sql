DROP INDEX IF EXISTS idx_user_read_history_user_article;
DROP INDEX IF EXISTS idx_user_read_history_recent;
DROP INDEX IF EXISTS idx_user_read_history_article_id;
DROP INDEX IF EXISTS idx_user_read_history_user_id;

DROP TABLE IF EXISTS user_read_history CASCADE;