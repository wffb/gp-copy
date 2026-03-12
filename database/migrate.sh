#!/usr/bin/env bash
set -euo pipefail

# Simple migration runner for PostgreSQL
# Usage:
#   ./migrate.sh up     # Apply all *.up.sql in order
#   ./migrate.sh down   # Apply all *.down.sql in reverse order
# Environment:
#   DATABASE_URL or standard PG* env vars (PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)

MIGRATIONS_DIR="$(cd "$(dirname "$0")" && pwd)/migrations"

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql is not installed or not in PATH" >&2
  exit 1
fi

if [ ! -d "$MIGRATIONS_DIR" ]; then
  echo "Error: migrations directory not found at $MIGRATIONS_DIR" >&2
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 {up|down}" >&2
  exit 1
fi

CMD="$1"

# Build psql base args
PSQL_ARGS=("-v" "ON_ERROR_STOP=1")
if [ -n "${DATABASE_URL:-}" ]; then
  PSQL_CONN=("$DATABASE_URL")
else
  PSQL_CONN=()
fi

run_file() {
  local file="$1"
  echo "Applying: $(basename "$file")"
  if [ ${#PSQL_CONN[@]} -gt 0 ]; then
    psql "${PSQL_CONN[@]}" "${PSQL_ARGS[@]}" -f "$file"
  else
    psql "${PSQL_ARGS[@]}" -f "$file"
  fi
}

case "$CMD" in
  up)
    mapfile -t files < <(find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name "*.up.sql" | sort)
    if [ ${#files[@]} -eq 0 ]; then
      echo "No up migrations found in $MIGRATIONS_DIR" >&2
      exit 1
    fi
    for f in "${files[@]}"; do
      run_file "$f"
    done
    echo "All up migrations applied."
    ;;
  down)
    mapfile -t files < <(find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name "*.down.sql" | sort -r)
    if [ ${#files[@]} -eq 0 ]; then
      echo "No down migrations found in $MIGRATIONS_DIR" >&2
      exit 1
    fi
    for f in "${files[@]}"; do
      run_file "$f"
    done
    echo "All down migrations applied."
    ;;
  *)
    echo "Unknown command: $CMD" >&2
    echo "Usage: $0 {up|down}" >&2
    exit 1
    ;;
esac

