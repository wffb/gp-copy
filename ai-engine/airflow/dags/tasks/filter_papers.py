"""
Quality Filter Tasks
====================
Tasks for filtering pending papers through quality checks.
"""

from airflow.sdk import task


@task.virtualenv(
    task_id="filter_papers_batch",
    requirements=[
        "sqlalchemy==2.0.36",
        "psycopg2-binary==2.9.10",
        "requests==2.31.0",
        "PyMuPDF==1.26.5",
        "langdetect==1.0.9",
    ],
    system_site_packages=True,
)
def filter_papers_batch(config: dict) -> dict:
    """Run quality checks on pending papers."""
    import logging
    import os
    from datetime import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from database.repositories.paper import PaperRepository
    from database.repositories.arxiv_ingestion import PipelineRunRepository
    from database.transaction import TransactionManager
    from services.quality_filter_service import QualityFilterService, create_quality_config_from_env

    os.environ['NO_COLOR'] = '1'
    os.environ['FORCE_COLOR'] = '0'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        force=True
    )
    
    logger = logging.getLogger(__name__)
    
    def _build_paper_data(paper) -> dict:
        """Build paper data dict for quality filter service."""
        return {
            'arxiv_id': paper.arxiv_id,
            'title': paper.title,
            'abstract': paper.abstract,
            'published_date': paper.published_date.isoformat() if paper.published_date else None,
            'primary_category': paper.categories[0] if paper.categories else '',
            'categories': paper.categories or [],
            'pdf_url': paper.pdf_url,
            'withdrawn': False,
        }
    
    run_id = config.get('run_id')
    dag_id = config.get('dag_id')
    database_url = config.get('database_url')
    filter_config = config.get('filter_config')

    if not all([run_id, dag_id, database_url, filter_config]):
        raise ValueError("Missing required config: run_id, dag_id, database_url, filter_config")

    logger.info("=" * 80)
    logger.info(f"QUALITY FILTER START - Run ID: {run_id}")
    logger.info("=" * 80)

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    paper_repo = PaperRepository(session)
    pipeline_repo = PipelineRunRepository(session)
    transaction_mgr = TransactionManager(session)
    quality_config = create_quality_config_from_env(filter_config)
    filter_service = QualityFilterService(quality_config)
    
    counts = {
        'total': 0,
        'ready_to_process': 0,
        'rejected': 0,
        'failed': 0
    }
    rejection_reasons = {}
    filter_run_id = None
    
    try:
        start_time = datetime.utcnow()
        batch_size = filter_config.get('batch_size', 50)
        
        # Get or create filter run (idempotent for retries)
        with transaction_mgr.transaction():
            filter_run, created = pipeline_repo.get_or_create_run(
                run_id=run_id,
                dag_id=dag_id,
                execution_date=start_time,
                started_at=start_time,
                status='running',
                pipeline_type='quality_filter',
                metrics={},
                processing_time_seconds=0.0
            )
            filter_run_id = filter_run.id
            if not created:
                logger.info(f"Resuming existing quality filter run: {filter_run_id}")
                filter_run.status = 'running'
                filter_run.error_message = None
            else:
                logger.info(f"Created new quality filter run: {filter_run_id}")
        
        logger.info(f"Quality filter run: {filter_run_id}")
        logger.info(f"Batch size: {batch_size}, PDF download: {filter_config.get('QF_ENABLE_PDF_DOWNLOAD', 'true')}")
        
        pending_papers = paper_repo.find_by_status_batch('pending', limit=batch_size)
        
        counts['total'] = len(pending_papers)
        logger.info(f"Found {counts['total']} pending papers to filter")
        
        if counts['total'] == 0:
            logger.info("No pending papers found")
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Update run record
            if filter_run_id:
                with transaction_mgr.transaction():
                    filter_run = pipeline_repo.find_one(id=filter_run_id)
                    filter_run.completed_at = end_time
                    filter_run.processing_time_seconds = processing_time
                    filter_run.status = 'completed'
                    filter_run.set_metric('batch_size', batch_size)
                    filter_run.set_metric('papers_total', counts['total'])
                
                logger.info(f"Updated quality filter run {filter_run_id}: no papers to process")
            
            return {
                'run_id': run_id,
                'filter_run_id': str(filter_run_id) if filter_run_id else None,
                'timestamp': end_time.isoformat(),
                'counts': counts,
                'rejection_reasons': rejection_reasons,
                'processing_time_seconds': processing_time,
            }
        
        for idx, paper in enumerate(pending_papers, 1):
            try:
                paper_data = _build_paper_data(paper)
                status, message = filter_service.filter_paper(paper_data)
                
                paper_repo.update_status(paper, status, message)
                session.commit()
                
                counts[status] += 1
                
                if status == 'rejected' and message:
                    reason_key = message.split(':')[0]
                    rejection_reasons[reason_key] = rejection_reasons.get(reason_key, 0) + 1
                
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{counts['total']} papers processed")
                
            except Exception as e:
                logger.error(f"Failed to filter paper {paper.arxiv_id}: {e}", exc_info=True)
                counts['failed'] += 1
                paper_repo.update_status(paper, 'rejected', f"Filter error: {str(e)[:200]}")
                session.commit()
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("QUALITY FILTER COMPLETE")
        logger.info(f"Total: {counts['total']}, Ready: {counts['ready_to_process']}, Rejected: {counts['rejected']}, Failed: {counts['failed']}")
        logger.info(f"Rejection reasons: {rejection_reasons}")
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info("=" * 80)
        
        # Update run record with final counts
        if filter_run_id:
            with transaction_mgr.transaction():
                filter_run = pipeline_repo.find_one(id=filter_run_id)
                filter_run.completed_at = end_time
                filter_run.processing_time_seconds = processing_time
                
                # Store counts in flexible metrics field
                filter_run.set_metric('batch_size', batch_size)
                filter_run.set_metric('papers_total', counts['total'])
                filter_run.set_metric('papers_ready', counts['ready_to_process'])
                filter_run.set_metric('papers_rejected', counts['rejected'])
                filter_run.set_metric('papers_failed', counts['failed'])
                filter_run.set_metric('rejection_reasons', rejection_reasons)
                filter_run.set_metric('pdf_download_enabled', filter_config.get('QF_ENABLE_PDF_DOWNLOAD', 'true'))
                
                # Determine final status
                if counts['total'] > 0 and counts['failed'] == counts['total']:
                    filter_run.status = 'failed'
                    filter_run.error_message = f"All {counts['total']} papers failed processing"
                elif counts['failed'] > 0:
                    filter_run.status = 'partial'
                else:
                    filter_run.status = 'completed'
            
            logger.info(f"Updated quality filter run {filter_run_id} with status: {filter_run.status}")
        
        result = {
            'run_id': run_id,
            'filter_run_id': str(filter_run_id) if filter_run_id else None,
            'timestamp': end_time.isoformat(),
            'counts': counts,
            'rejection_reasons': rejection_reasons,
            'processing_time_seconds': processing_time,
        }
        
        # Fail DAG only if ALL papers failed (catastrophic error)
        if counts['total'] > 0 and counts['failed'] == counts['total']:
            error_msg = f"Quality filter failed: ALL {counts['total']} papers failed processing"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Warn if some papers failed but continue
        if counts['failed'] > 0:
            logger.warning(f"Quality filter completed with {counts['failed']} failures (papers marked as rejected)")
        
        return result
        
    except Exception as e:
        logger.error(f"Quality filter batch failed: {e}", exc_info=True)
        raise
    finally:
        session.close()
        engine.dispose()


@task(task_id="log_filter_summary")
def log_filter_summary(filter_result: dict) -> None:
    """Log quality filter summary."""
    import logging
    logger = logging.getLogger(__name__)
    
    counts = filter_result.get('counts', {})
    rejection_reasons = filter_result.get('rejection_reasons', {})
    
    logger.info("=" * 80)
    logger.info("QUALITY FILTER SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total papers processed: {counts.get('total', 0)}")
    logger.info(f"Ready to process: {counts.get('ready_to_process', 0)}")
    logger.info(f"Rejected: {counts.get('rejected', 0)}")
    logger.info(f"Failed: {counts.get('failed', 0)}")
    
    if rejection_reasons:
        logger.info("")
        logger.info("Rejection Reasons:")
        for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {reason}: {count}")
    
    logger.info("=" * 80)

