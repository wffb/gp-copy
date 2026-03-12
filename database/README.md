Database Migrations

- Directory: `migrations/` contains all `*.up.sql` and `*.down.sql` files.
- Runners:
  - `./migrate.sh` (Bash) uses `psql`.
  - `python migrate.py` (Python) uses `psycopg`/`psycopg2` if available, else falls back to `psql`.

Usage

- Set connection via `DATABASE_URL` (recommended) or standard `PG*` env vars.
- Apply all up migrations: `./migrate.sh up` or `python migrate.py up`
- Roll back all down migrations: `./migrate.sh down` or `python migrate.py down`

Notes

- Files run in lexical order for `*.up.sql` and reverse order for `*.down.sql`.
- The script uses `psql -v ON_ERROR_STOP=1` to stop on the first error.
- Example `DATABASE_URL`: `postgres://user:password@localhost:5432/newsai`.

PyCharm

- Create a Python Run Configuration:
  - Script path: `$PROJECT_DIR$/migrate.py`
  - Parameters: `up` (or `down`)
  - Working directory: `$PROJECT_DIR$`
  - Environment: set `DATABASE_URL` (e.g., `postgres://user:password@localhost:5432/newsai`)
- Optional: Install driver for pure-Python execution: `pip install psycopg[binary]` (preferred) or `pip install psycopg2-binary`.
- If you prefer using `psql`, ensure it’s on PATH. On macOS with Homebrew: `brew install libpq` then add `$(brew --prefix)/opt/libpq/bin` to PATH.

Seeds

- Directory: `seeds/` contains SQL seed files.
- Files:
  - `seeds/seed_articles.sql` — seeds papers, articles, and article_blocks (idempotent).
  - `seeds/seed_all.sql` — psql script that includes all seed files.
- Usage (SQL-only):
  - Set `DATABASE_URL` (same as migrations).
  - Run all seeds: `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f seeds/seed_all.sql`
  - Or run a specific file: `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f seeds/seed_articles.sql`
