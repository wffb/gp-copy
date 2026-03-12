DROP INDEX IF EXISTS idx_user_more_like_this_created;
DROP INDEX IF EXISTS idx_user_more_like_this_article_id;
DROP INDEX IF EXISTS idx_user_more_like_this_user_id;

DROP TABLE IF EXISTS user_more_like_this CASCADE;