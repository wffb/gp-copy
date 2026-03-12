"""
arXiv Ingestion DAG
===================

Main DAG for arXiv paper ingestion pipeline.

This DAG:
1. Validates system health and configuration
2. Tests database and API connectivity
3. Fetches papers from arXiv API
4. Ingests papers into database with full metadata
5. Tracks ingestion runs and individual paper processing

Schedule: Every 6 hours
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.sdk import task
from tasks import (
    validate_airflow_variables,
    test_database_connectivity,
    test_external_apis,
    check_system_resources,
    generate_health_summary,
    fetch_arxiv_papers,
    log_ingestion_summary,
    update_start_index,
)

# DAG Configuration
DAG_ID = "arxiv_ingestion_dag"
DEFAULT_ARGS = {
    "owner": "zara-etl-platform",
    "depends_on_past": False,
    "start_date": datetime(2025, 9, 1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "max_active_runs": 1,
}

# Create DAG
with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="arXiv paper ingestion pipeline with health checks and monitoring",
    schedule=timedelta(hours=6),
    catchup=False,
    max_active_runs=1,
    tags=["arxiv", "ingestion", "production"],
    doc_md=__doc__,
) as dag:
    
    # Health check tasks - run in parallel
    variables_check = validate_airflow_variables()
    database_check = test_database_connectivity()
    api_check = test_external_apis()
    resources_check = check_system_resources()
    
    # Generate health summary from all checks
    health_summary = generate_health_summary(
        variables_check,
        database_check,
        api_check,
        resources_check
    )

    # arXiv ingestion tasks - run after health checks pass
    @task(task_id="get_config")
    def get_arxiv_config(**context) -> dict:
        """Fetch config from Airflow Variables at runtime (allows UI updates)."""
        from airflow.sdk import Variable
        import os

        dag_run = context['dag_run']

        return {
            'run_id': dag_run.run_id,
            'dag_id': dag_run.dag_id,
            'database_url': Variable.get("DATABASE_URL", default=os.getenv("DATABASE_URL")),
            'arxiv_config': {
                'rate_limit_seconds': int(Variable.get("ARXIV_RATE_LIMIT_SECONDS", default=os.getenv("ARXIV_RATE_LIMIT_SECONDS", "3"))),
                'max_retries': int(Variable.get("ARXIV_MAX_RETRIES", default=os.getenv("ARXIV_MAX_RETRIES", "3"))),
                'max_results_per_request': int(Variable.get("ARXIV_MAX_RESULTS_PER_REQUEST", default=os.getenv("ARXIV_MAX_RESULTS_PER_REQUEST", "1000"))),
                'max_results': int(Variable.get("ARXIV_MAX_RESULTS", default=os.getenv("ARXIV_MAX_RESULTS", "1000"))),
                'categories': [cat.strip() for cat in Variable.get("ARXIV_CATEGORIES", default=os.getenv("ARXIV_CATEGORIES", "")).split(',') if cat.strip()],
                'sort_by': Variable.get("ARXIV_SORT_BY", default=os.getenv("ARXIV_SORT_BY", "submittedDate")),
                'sort_order': Variable.get("ARXIV_SORT_ORDER", default=os.getenv("ARXIV_SORT_ORDER", "descending")),
                'start_index': int(Variable.get("ARXIV_START_INDEX", default=os.getenv("ARXIV_START_INDEX", "0"))),
            }
        }

    # Get config at runtime (reflects UI changes)
    config = get_arxiv_config()
    
    arxiv_fetch = fetch_arxiv_papers(config=config)
    arxiv_summary = log_ingestion_summary(arxiv_fetch)
    start_index_update = update_start_index(arxiv_fetch)
    
    # Task dependencies
    # Health checks → summary → config → fetch → log summary and update start index
    [variables_check, database_check, api_check, resources_check] >> health_summary
    health_summary >> config >> arxiv_fetch >> [arxiv_summary, start_index_update]

