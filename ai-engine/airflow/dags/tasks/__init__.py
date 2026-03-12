"""
DAG Tasks Module
================

Contains individual task implementations for Airflow DAGs.
"""

from tasks.health_checks import (
    validate_airflow_variables,
    test_database_connectivity,
    test_external_apis,
    check_system_resources,
    generate_health_summary,
)
from tasks.fetch_arxiv_papers import (
    fetch_arxiv_papers,
    log_ingestion_summary,
    update_start_index
)
from tasks.filter_papers import (
    filter_papers_batch,
    log_filter_summary,
)
from tasks.process_papers import (
    process_papers_batch,
    log_processing_summary,
)

__all__ = [
    # Health check tasks
    'validate_airflow_variables',
    'test_database_connectivity',
    'test_external_apis',
    'check_system_resources',
    'generate_health_summary',
    # arXiv ingestion tasks
    'fetch_arxiv_papers',
    'log_ingestion_summary',
    'update_start_index',
    # Quality filter tasks
    'filter_papers_batch',
    'log_filter_summary',
    # DocETL processing tasks
    'process_papers_batch',
    'log_processing_summary',
]

