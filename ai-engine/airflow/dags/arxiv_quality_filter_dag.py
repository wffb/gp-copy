"""
arXiv Quality Filter DAG
=========================

Quality filtering DAG for arXiv papers.

This DAG:
1. Validates system health and configuration
2. Fetches papers with status='pending'
3. Runs quality checks (metadata, PDF structure, content)
4. Updates paper status to 'ready_to_process' or 'rejected'

Schedule: Every 12 hours (runs after ingestion DAG)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.sdk import task
from tasks import (
    validate_airflow_variables,
    test_database_connectivity,
    generate_health_summary,
    filter_papers_batch,
    log_filter_summary,
)

DAG_ID = "arxiv_quality_filter_dag"
DEFAULT_ARGS = {
    "owner": "zara-etl-platform",
    "depends_on_past": False,
    "start_date": datetime(2025, 9, 1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "max_active_runs": 1,
}

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="Quality filtering for arXiv papers with PDF and content checks",
    schedule=timedelta(hours=12),
    catchup=False,
    max_active_runs=1,
    tags=["arxiv", "quality-filter", "production"],
    doc_md=__doc__,
) as dag:
    
    # Health checks
    variables_check = validate_airflow_variables()
    database_check = test_database_connectivity()
    
    health_summary = generate_health_summary(
        variables_check,
        database_check,
        {"timestamp": datetime.utcnow().isoformat(), "all_ok": True, "arxiv_ok": True},
        {"timestamp": datetime.utcnow().isoformat(), "warnings": [], "errors": []},
    )

    @task(task_id="get_filter_config")
    def get_filter_config(**context) -> dict:
        """Fetch quality filter config from Airflow Variables at runtime."""
        from airflow.sdk import Variable
        import os

        dag_run = context['dag_run']

        return {
            'run_id': dag_run.run_id,
            'dag_id': dag_run.dag_id,
            'database_url': Variable.get("DATABASE_URL", default=os.getenv("DATABASE_URL")),
            'filter_config': {
                'batch_size': int(Variable.get("QF_BATCH_SIZE", default=os.getenv("QF_BATCH_SIZE", "50"))),
                'QF_PDF_MIN_PAGES': int(Variable.get("QF_PDF_MIN_PAGES", default=os.getenv("QF_PDF_MIN_PAGES", "4"))),
                'QF_PDF_MAX_PAGES': int(Variable.get("QF_PDF_MAX_PAGES", default=os.getenv("QF_PDF_MAX_PAGES", "50"))),
                'QF_PDF_MIN_SIZE_KB': int(Variable.get("QF_PDF_MIN_SIZE_KB", default=os.getenv("QF_PDF_MIN_SIZE_KB", "100"))),
                'QF_PDF_MAX_SIZE_MB': int(Variable.get("QF_PDF_MAX_SIZE_MB", default=os.getenv("QF_PDF_MAX_SIZE_MB", "25"))),
                'QF_TEXT_MIN_CHARS': int(Variable.get("QF_TEXT_MIN_CHARS", default=os.getenv("QF_TEXT_MIN_CHARS", "1000"))),
                'QF_LANGUAGE': Variable.get("QF_LANGUAGE", default=os.getenv("QF_LANGUAGE", "en")),
                'QF_ABSTRACT_MIN_WORDS': int(Variable.get("QF_ABSTRACT_MIN_WORDS", default=os.getenv("QF_ABSTRACT_MIN_WORDS", "80"))),
                'QF_ABSTRACT_MAX_WORDS': int(Variable.get("QF_ABSTRACT_MAX_WORDS", default=os.getenv("QF_ABSTRACT_MAX_WORDS", "500"))),
                'QF_PRIORITY_CATEGORIES': Variable.get("QF_PRIORITY_CATEGORIES", default=os.getenv("QF_PRIORITY_CATEGORIES", "astro-ph,physics,cs.AI,cs.LG,q-bio")),
                'QF_EXCLUDE_CATEGORIES': Variable.get("QF_EXCLUDE_CATEGORIES", default=os.getenv("QF_EXCLUDE_CATEGORIES", "cs.CR")),
                'QF_RECENCY_YEARS': int(Variable.get("QF_RECENCY_YEARS", default=os.getenv("QF_RECENCY_YEARS", "5"))),
                'QF_MIN_SECTIONS': int(Variable.get("QF_MIN_SECTIONS", default=os.getenv("QF_MIN_SECTIONS", "3"))),
                'QF_MIN_FIGURES': int(Variable.get("QF_MIN_FIGURES", default=os.getenv("QF_MIN_FIGURES", "0"))),
                'QF_MAX_FIGURES': int(Variable.get("QF_MAX_FIGURES", default=os.getenv("QF_MAX_FIGURES", "10"))),
                'QF_ENABLE_PDF_DOWNLOAD': Variable.get("QF_ENABLE_PDF_DOWNLOAD", default=os.getenv("QF_ENABLE_PDF_DOWNLOAD", "true")),
            }
        }

    config = get_filter_config()
    
    filter_result = filter_papers_batch(config=config)
    filter_summary = log_filter_summary(filter_result)
    
    # Task dependencies
    [variables_check, database_check] >> health_summary >> config >> filter_result >> filter_summary

