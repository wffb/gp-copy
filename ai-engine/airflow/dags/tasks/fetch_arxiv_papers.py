"""Fetch arXiv Papers Task - Orchestrates paper fetching and ingestion."""

from airflow.sdk import task


@task.virtualenv(
    task_id="fetch_arxiv_papers",
    requirements=[
        "sqlalchemy==2.0.36",
        "psycopg2-binary==2.9.10",
        "feedparser==6.0.12",
        "requests==2.31.0",
    ],
    system_site_packages=True,
)
def fetch_arxiv_papers(config: dict) -> dict:
    """Fetch papers from arXiv and ingest into database."""
    import logging
    import os
    from datetime import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from database.repositories.arxiv_ingestion import PipelineRunRepository
    from database.transaction import TransactionManager
    from services.arxiv_api_service import ArxivAPIService, ArxivAPIError
    from services.paper_ingestion_service import PaperIngestionService

    os.environ['NO_COLOR'] = '1'
    os.environ['FORCE_COLOR'] = '0'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        force=True
    )
    
    logger = logging.getLogger(__name__)
    
    run_id = config.get('run_id')
    dag_id = config.get('dag_id')
    database_url = config.get('database_url')
    arxiv_config = config.get('arxiv_config')

    if not all([run_id, dag_id, database_url, arxiv_config]):
        raise ValueError("Missing required config: run_id, dag_id, database_url, arxiv_config")

    logger.info(f"=" * 80)
    logger.info(f"ARXIV INGESTION START - Run ID: {run_id}")
    logger.info(f"=" * 80)

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    pipeline_repo = PipelineRunRepository(session)
    transaction_mgr = TransactionManager(session)
    
    api_service = ArxivAPIService(
        rate_limit_seconds=arxiv_config['rate_limit_seconds'],
        max_retries=arxiv_config['max_retries'],
        max_results_per_request=arxiv_config['max_results_per_request']
    )
    
    ingestion_service = PaperIngestionService(session)

    ingestion_run_id = None
    
    try:
        start_time = datetime.utcnow()
        categories_str = ', '.join(arxiv_config['categories']) if arxiv_config['categories'] else 'all'
        
        with transaction_mgr.transaction():
            # Get or create ingestion run (idempotent for retries)
            ingestion_run, created = pipeline_repo.get_or_create_run(
                run_id=run_id,
                dag_id=dag_id,
                execution_date=start_time,
                started_at=start_time,
                status='running',
                pipeline_type='arxiv_ingestion',
                metrics={
                    'search_query': categories_str,
                    'categories': arxiv_config['categories'],
                    'sort_by': arxiv_config['sort_by'],
                    'sort_order': arxiv_config['sort_order'],
                    'start_index': arxiv_config['start_index'],
                    'max_results': arxiv_config['max_results'],
                    'total_available': 0,
                    'papers_fetched': 0,
                    'papers_new': 0,
                    'papers_updated': 0,
                    'papers_skipped': 0,
                    'papers_failed': 0,
                    'api_calls_made': 0,
                },
                processing_time_seconds=0.0
            )
            ingestion_run_id = ingestion_run.id
            if not created:
                logger.info(f"Resuming existing ingestion run: {ingestion_run_id}")
                ingestion_run.status = 'running'
                ingestion_run.error_message = None
            else:
                logger.info(f"Created new ingestion run: {ingestion_run_id}")

        logger.info(f"Ingestion run: {ingestion_run_id}")
        logger.info(f"Query categories: {categories_str}")
        logger.info(f"Sort: {arxiv_config['sort_by']} ({arxiv_config['sort_order']})")

        api_service.set_query_params(
            categories=arxiv_config['categories'],
            start=arxiv_config['start_index'],
                    sort_by=arxiv_config['sort_by'],
                    sort_order=arxiv_config['sort_order']
                )
        logger.info(f"Target: {arxiv_config['max_results']} papers (up to {arxiv_config['max_results_per_request']} per batch)")
        logger.info(f"Rate limit: {arxiv_config['rate_limit_seconds']}s between requests")

        papers = api_service.fetch_all(
            max_results=arxiv_config['max_results'],
            session=session,
            run_id=ingestion_run_id
        )

        logger.info(f"API fetch complete: {len(papers)} papers retrieved")

        if not papers:
            logger.warning("No papers fetched from arXiv")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            with transaction_mgr.transaction():
                ingestion_run = pipeline_repo.find_one(id=ingestion_run_id)
                ingestion_run.set_metric('papers_fetched', 0)
                ingestion_run.set_metric('papers_new', 0)
                ingestion_run.set_metric('papers_updated', 0)
                ingestion_run.set_metric('papers_skipped', 0)
                ingestion_run.set_metric('papers_failed', 0)
                ingestion_run.completed_at = datetime.utcnow()
                ingestion_run.status = 'completed'
                ingestion_run.processing_time_seconds = processing_time
            
            session.close()
            return {
                'status': 'success',
                'run_id': str(ingestion_run_id),
                'papers_fetched': 0,
                'papers_new': 0,
                'papers_updated': 0,
                'papers_skipped': 0,
                'papers_failed': 0,
                'processing_time_seconds': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }

        logger.info("Starting bulk paper ingestion...")
        counts = ingestion_service.ingest_papers(papers)

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        with transaction_mgr.transaction():
            ingestion_run = pipeline_repo.find_one(id=ingestion_run_id)
            ingestion_run.set_metric('papers_fetched', len(papers))
            ingestion_run.set_metric('papers_new', counts['new'])
            ingestion_run.set_metric('papers_updated', counts['updated'])
            ingestion_run.set_metric('papers_skipped', counts['skipped'])
            ingestion_run.set_metric('papers_failed', counts['failed'])
            ingestion_run.set_metric('api_calls_made', api_service.api_calls_made if hasattr(api_service, 'api_calls_made') else 0)
            ingestion_run.completed_at = end_time
            ingestion_run.status = 'completed'
            ingestion_run.processing_time_seconds = processing_time
        
        next_start_index = arxiv_config['start_index'] + len(papers)

        logger.info("=" * 80)
        logger.info("INGESTION COMPLETE")
        logger.info(f"Fetched: {len(papers)} | New: {counts['new']} | Updated: {counts['updated']} | Skipped: {counts['skipped']} | Failed: {counts['failed']}")
        logger.info(f"Time: {processing_time:.2f}s")
        logger.info(f"Next start index: {next_start_index}")
        logger.info("=" * 80)

        session.close()
        
        return {
            'status': 'success',
            'run_id': str(ingestion_run_id),
            'papers_fetched': len(papers),
            'papers_new': counts['new'],
            'papers_updated': counts['updated'],
            'papers_skipped': counts['skipped'],
            'papers_failed': counts['failed'],
            'processing_time_seconds': processing_time,
            'next_start_index': next_start_index,
            'timestamp': end_time.isoformat()
        }
        
    except ArxivAPIError as e:
        logger.error(f"=" * 80)
        logger.error(f"ARXIV API ERROR: {e}")
        logger.error(f"=" * 80)
        
        if ingestion_run_id:
            try:
                with transaction_mgr.transaction():
                    ingestion_run = pipeline_repo.find_one(id=ingestion_run_id)
                    if ingestion_run:
                        ingestion_run.completed_at = datetime.utcnow()
                        ingestion_run.status = 'failed'
                        ingestion_run.error_message = f"arXiv API Error: {e}"[:1000]
                        logger.info(f"Updated run {ingestion_run_id} status to 'failed'")
            except Exception as update_err:
                logger.error(f"Failed to update run status: {update_err}")
        else:
            logger.warning("No ingestion run to update (error occurred before run creation)")

        session.close()
        return {
            'status': 'failed',
            'error': str(e),
            'error_type': 'arxiv_api_error',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"=" * 80)
        logger.error(f"UNEXPECTED ERROR: {e}")
        logger.error(f"=" * 80, exc_info=True)
        
        if ingestion_run_id:
            try:
                with transaction_mgr.transaction():
                    ingestion_run = pipeline_repo.find_one(id=ingestion_run_id)
                    if ingestion_run:
                        ingestion_run.completed_at = datetime.utcnow()
                        ingestion_run.status = 'failed'
                        ingestion_run.error_message = str(e)[:1000]
                        logger.info(f"Updated run {ingestion_run_id} status to 'failed'")
            except Exception as update_err:
                logger.error(f"Failed to update run status: {update_err}")
        else:
            logger.warning("No ingestion run to update (error occurred before run creation)")
        
        session.close()
        return {
            'status': 'failed',
            'error': str(e),
            'error_type': 'general_error',
            'timestamp': datetime.utcnow().isoformat()
        }


@task(task_id="log_ingestion_summary")
def log_ingestion_summary(fetch_result: dict) -> None:
    """Log human-readable summary of ingestion results."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    status = fetch_result.get('status', 'unknown')
    
    logger.info("+" + "=" * 78 + "+")
    logger.info("|" + " " * 25 + "INGESTION SUMMARY" + " " * 36 + "|")
    logger.info("+" + "=" * 78 + "+")
    
    if status == 'success':
        fetched = fetch_result.get('papers_fetched', 0)
        new = fetch_result.get('papers_new', 0)
        updated = fetch_result.get('papers_updated', 0)
        skipped = fetch_result.get('papers_skipped', 0)
        failed = fetch_result.get('papers_failed', 0)
        time_sec = fetch_result.get('processing_time_seconds', 0)
        
        logger.info(f"| Status        : [OK] SUCCESS" + " " * 49 + "|")
        logger.info(f"| Run ID        : {fetch_result.get('run_id', 'N/A')[:38]}" + " " * (40 - len(fetch_result.get('run_id', 'N/A')[:38])) + "|")
        logger.info("+" + "-" * 78 + "+")
        logger.info(f"| Papers Fetched: {fetched:>6}" + " " * 55 + "|")
        logger.info(f"|   - New       : {new:>6}" + " " * 55 + "|")
        logger.info(f"|   - Updated   : {updated:>6}" + " " * 55 + "|")
        logger.info(f"|   - Skipped   : {skipped:>6}" + " " * 55 + "|")
        logger.info(f"|   - Failed    : {failed:>6}" + " " * 55 + "|")
        logger.info("+" + "-" * 78 + "+")
        logger.info(f"| Processing    : {time_sec:>6.2f}s" + " " * 54 + "|")
        
        if fetched > 0:
            success_rate = ((new + updated + skipped) / fetched) * 100
            logger.info(f"| Success Rate  : {success_rate:>6.1f}%" + " " * 54 + "|")
    
    elif status == 'failed':
        error_type = fetch_result.get('error_type', 'Unknown')
        error_msg = fetch_result.get('error', 'No message')[:60]
        
        logger.info(f"| Status        : [FAIL] FAILED" + " " * 48 + "|")
        logger.info("+" + "-" * 78 + "+")
        logger.info(f"| Error Type    : {error_type}" + " " * (60 - len(error_type)) + "|")
        logger.info(f"| Error Message : {error_msg}" + " " * (60 - len(error_msg)) + "|")
    
    else:
        logger.info(f"| Status        : {status.upper()}" + " " * (60 - len(status)) + "|")
    
    logger.info("+" + "=" * 78 + "+")


@task(task_id="update_start_index")
def update_start_index(fetch_result: dict) -> None:
    """Update ARXIV_START_INDEX variable for next run."""
    from airflow.sdk import Variable
    import logging

    logger = logging.getLogger(__name__)
    
    if fetch_result.get('status') != 'success':
        logger.info("Skipping start index update - fetch was not successful")
        return
    
    next_start_index = fetch_result.get('next_start_index')
    if next_start_index is None:
        logger.warning("No next_start_index in fetch result")
        return
    
    try:
        Variable.set("ARXIV_START_INDEX", str(next_start_index))
        logger.info(f"✓ Updated ARXIV_START_INDEX to {next_start_index}")
        logger.info(f"  Next DAG run will fetch papers starting from index {next_start_index}")
    except Exception as e:
        logger.error(f"Failed to update ARXIV_START_INDEX: {e}")
        raise