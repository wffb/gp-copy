#!/bin/bash
set -e

# Get database name from environment variable with default
ETL_DB_NAME="${ETL_DB_NAME:-zara_etl}"
SKIP_DB_CREATION="${SKIP_DB_CREATION:-false}"

echo "Running SQL migrations from shared folder..."
echo "Target database: $ETL_DB_NAME"

# Check if migrations directory exists
SHARED_MIGRATIONS="/shared_migrations/migrations"

# Use shared migrations if mounted
if [ -d "$SHARED_MIGRATIONS" ] && [ "$(ls -A $SHARED_MIGRATIONS/*.up.sql 2>/dev/null)" ]; then
    MIGRATIONS_DIR="$SHARED_MIGRATIONS"
    echo "Using shared migrations from: $MIGRATIONS_DIR"
else
    echo "ERROR: No migrations found in $SHARED_MIGRATIONS"
    echo "Please ensure ../database/migrations is properly mounted"
    exit 1
fi

# Find and run all .up.sql files in order
for migration_file in $(ls $MIGRATIONS_DIR/*.up.sql 2>/dev/null | sort); do
    migration_name=$(basename "$migration_file" .up.sql)
    
    # Check if migration was already applied
    # For the first migration (0000_create_schema_migrations), this will fail if table doesn't exist
    # We handle this by checking if the table exists first
    table_exists=$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$ETL_DB_NAME" -tAc \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schema_migrations')")
    
    if [ "$table_exists" = "t" ]; then
        already_applied=$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$ETL_DB_NAME" -tAc \
            "SELECT COUNT(*) FROM schema_migrations WHERE version='$migration_name'")
    else
        # Table doesn't exist yet, so no migrations have been applied
        already_applied=0
    fi
    
    if [ "$already_applied" -eq "0" ]; then
        echo "  Applying migration: $migration_name"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$ETL_DB_NAME" -f "$migration_file"
        
        # Record migration as applied (table will exist after first migration)
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$ETL_DB_NAME" <<-EOSQL
            INSERT INTO schema_migrations (version) VALUES ('$migration_name');
EOSQL
        echo "  Applied: $migration_name"
    else
        echo "  Skipping (already applied): $migration_name"
    fi
done

echo "All migrations completed successfully for database: $ETL_DB_NAME"
