"""
DocETL Processing DAG
=====================

Processes papers into engaging articles using DocETL.

This DAG:
1. Validates system health and configuration
2. Fetches papers with status='ready_to_process'
3. Extracts full PDF text and figure metadata
4. Generates article components using DocETL pipeline
5. Validates generated content (LLM as judge)
6. Creates articles with blocks in database
7. Updates paper status to 'completed' or 'failed'

Schedule: Daily at 6 AM UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.sdk import task
from tasks import (
    validate_airflow_variables,
    test_database_connectivity,
    generate_health_summary,
    process_papers_batch,
    log_processing_summary,
)

DAG_ID = "docetl_processing_dag"
DEFAULT_ARGS = {
    "owner": "zara-etl-platform",
    "depends_on_past": False,
    "start_date": datetime(2025, 10, 1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "max_active_runs": 1,
}

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="DocETL-based paper-to-article processing pipeline with validation",
    schedule="0 6 * * *",  # Daily at 6 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=["docetl", "article-generation", "production"],
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

    @task(task_id="get_processing_config")
    def get_processing_config(**context) -> dict:
        """Fetch DocETL processing config from Airflow Variables at runtime."""
        from airflow.sdk import Variable
        import os

        dag_run = context['dag_run']

        return {
            'run_id': dag_run.run_id,
            'dag_id': dag_run.dag_id,
            'database_url': Variable.get("DATABASE_URL", default=os.getenv("DATABASE_URL")),
            'openai_api_key': Variable.get("OPENAI_API_KEY", default=os.getenv("OPENAI_API_KEY")),
            'openai_api_base': Variable.get("OPENAI_API_BASE", default=os.getenv("OPENAI_API_BASE", "")),
            'processing_config': {
                # Batch processing
                'batch_size': int(Variable.get("DOCETL_BATCH_SIZE", default=os.getenv("DOCETL_BATCH_SIZE", "10"))),
                'enable': Variable.get("DOCETL_ENABLE", default=os.getenv("DOCETL_ENABLE", "true")).lower() == 'true',
                'max_retries': int(Variable.get("DOCETL_MAX_RETRIES", default=os.getenv("DOCETL_MAX_RETRIES", "2"))),
                'timeout_seconds': int(Variable.get("DOCETL_TIMEOUT_SECONDS", default=os.getenv("DOCETL_TIMEOUT_SECONDS", "300"))),
                
                # LLM configuration
                'llm_provider': Variable.get("DOCETL_LLM_PROVIDER", default=os.getenv("DOCETL_LLM_PROVIDER", "openai")),
                'llm_model': Variable.get("DOCETL_LLM_MODEL", default=os.getenv("DOCETL_LLM_MODEL", "gpt-4o-mini")),
                'llm_judge_model': Variable.get("DOCETL_LLM_JUDGE_MODEL", default=os.getenv("DOCETL_LLM_JUDGE_MODEL", "gpt-4o-mini")),
                'llm_temperature': float(Variable.get("DOCETL_LLM_TEMPERATURE", default=os.getenv("DOCETL_LLM_TEMPERATURE", "0.7"))),
                'llm_max_tokens': int(Variable.get("DOCETL_LLM_MAX_TOKENS", default=os.getenv("DOCETL_LLM_MAX_TOKENS", "4000"))),
                'llm_request_timeout': int(Variable.get("DOCETL_LLM_REQUEST_TIMEOUT", default=os.getenv("DOCETL_LLM_REQUEST_TIMEOUT", "600"))),
                
                # Article generation settings
                'min_blocks': int(Variable.get("DOCETL_MIN_BLOCKS", default=os.getenv("DOCETL_MIN_BLOCKS", "5"))),
                'max_blocks': int(Variable.get("DOCETL_MAX_BLOCKS", default=os.getenv("DOCETL_MAX_BLOCKS", "20"))),
                'min_word_count': int(Variable.get("DOCETL_MIN_WORD_COUNT", default=os.getenv("DOCETL_MIN_WORD_COUNT", "500"))),
                'max_word_count': int(Variable.get("DOCETL_MAX_WORD_COUNT", default=os.getenv("DOCETL_MAX_WORD_COUNT", "2000"))),
                'paragraph_target_words': int(Variable.get("DOCETL_PARAGRAPH_TARGET_WORDS", default=os.getenv("DOCETL_PARAGRAPH_TARGET_WORDS", "150"))),
                
                # Validation thresholds
                'min_readability_score': float(Variable.get("DOCETL_MIN_READABILITY_SCORE", default=os.getenv("DOCETL_MIN_READABILITY_SCORE", "7.0"))),
                'min_engagement_score': float(Variable.get("DOCETL_MIN_ENGAGEMENT_SCORE", default=os.getenv("DOCETL_MIN_ENGAGEMENT_SCORE", "7.0"))),
                'min_accuracy_score': float(Variable.get("DOCETL_MIN_ACCURACY_SCORE", default=os.getenv("DOCETL_MIN_ACCURACY_SCORE", "9.0"))),
                'enable_validation': Variable.get("DOCETL_ENABLE_VALIDATION", default=os.getenv("DOCETL_ENABLE_VALIDATION", "true")).lower() == 'true',
                
                # Gleaning (automatic retries with validation feedback)
                'enable_gleaning': Variable.get("DOCETL_ENABLE_GLEANING", default=os.getenv("DOCETL_ENABLE_GLEANING", "true")).lower() == 'true',
                'gleaning_rounds': int(Variable.get("DOCETL_GLEANING_ROUNDS", default=os.getenv("DOCETL_GLEANING_ROUNDS", "2"))),
                'validation_prompt': Variable.get("DOCETL_VALIDATION_PROMPT", default=os.getenv("DOCETL_VALIDATION_PROMPT", "")),
                
                # PDF processing
                'extract_full_text': Variable.get("DOCETL_EXTRACT_FULL_TEXT", default=os.getenv("DOCETL_EXTRACT_FULL_TEXT", "true")).lower() == 'true',
                'extract_figures': Variable.get("DOCETL_EXTRACT_FIGURES", default=os.getenv("DOCETL_EXTRACT_FIGURES", "false")).lower() == 'true',
                'max_pdf_size_mb': int(Variable.get("DOCETL_MAX_PDF_SIZE_MB", default=os.getenv("DOCETL_MAX_PDF_SIZE_MB", "25"))),
                'pdf_download_timeout': int(Variable.get("DOCETL_PDF_DOWNLOAD_TIMEOUT", default=os.getenv("DOCETL_PDF_DOWNLOAD_TIMEOUT", "60"))),
                
                # DocETL internals
                'intermediate_dir': Variable.get("DOCETL_INTERMEDIATE_DIR", default=os.getenv("DOCETL_INTERMEDIATE_DIR", "storage/docetl_intermediate")),
            }
        }

    config = get_processing_config()
    
    processing_result = process_papers_batch(config=config)
    processing_summary = log_processing_summary(processing_result)
    
    # Task dependencies
    [variables_check, database_check] >> health_summary >> config >> processing_result >> processing_summary

