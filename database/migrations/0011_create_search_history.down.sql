DROP INDEX IF EXISTS idx_user_search_history_recent;
DROP INDEX IF EXISTS idx_user_search_history_is_saved;
DROP INDEX IF EXISTS idx_user_search_history_user_id;

DROP TABLE IF EXISTS user_search_history CASCADE;