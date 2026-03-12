#!/bin/bash
set -e

# Get database names from environment variables with defaults
AIRFLOW_DB_NAME="${AIRFLOW_DB_NAME:-zara_airflow}"
ETL_DB_NAME="${ETL_DB_NAME:-zara_etl}"

echo "Creating databases if they don't exist..."
echo "  - Airflow DB: $AIRFLOW_DB_NAME"
echo "  - ETL DB: $ETL_DB_NAME"

# Create databases if they don't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE $AIRFLOW_DB_NAME'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$AIRFLOW_DB_NAME')\gexec
    
    SELECT 'CREATE DATABASE $ETL_DB_NAME'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$ETL_DB_NAME')\gexec
EOSQL

echo "Databases initialized successfully ($AIRFLOW_DB_NAME, $ETL_DB_NAME)"
