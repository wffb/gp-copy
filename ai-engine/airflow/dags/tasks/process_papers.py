"""
DocETL Processing Tasks
=======================
Tasks for processing papers into articles using DocETL.
"""

from airflow.sdk import task


@task.virtualenv(
    task_id="process_papers_batch",
    requirements=[
        "sqlalchemy==2.0.36",
        "psycopg2-binary==2.9.10",
        "requests==2.31.0",
        "PyMuPDF==1.26.5",
        "docetl>=0.1.0",
        "openai>=1.0.0",
    ],
    system_site_packages=True,
)
def process_papers_batch(config: dict) -> dict:
    """Process ready_to_process papers into articles using DocETL."""
    import logging
    import os
    from datetime import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from database.repositories.paper import PaperRepository
    from database.repositories.article import ArticleRepository, PromptRepository
    from database.repositories.arxiv_ingestion import PipelineRunRepository
    from database.transaction import TransactionManager
    from services.pdf_extraction_service import create_extraction_service_from_env
    from services.docetl_service import create_docetl_service_from_env
    from services.article_validation_service import create_validation_service_from_env
    from services.article_generation_service import create_generation_service_from_env

    os.environ['NO_COLOR'] = '1'
    os.environ['FORCE_COLOR'] = '0'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        force=True
    )
    
    logger = logging.getLogger(__name__)
    
    def _load_prompts_from_db(prompt_repo) -> dict:
        """Load active prompts from database."""
        prompt_names = [
            'extract_article_components',
            'generate_slug',
            'generate_article_blocks',
            'validate_readability',
            'validate_engagement',
            'validate_accuracy',
            'docetl_pipeline_system',
            'regenerate_with_feedback',
        ]
        
        prompts = {}
        for name in prompt_names:
            prompt = prompt_repo.find_active_by_name(name)
            if prompt:
                prompts[name] = prompt.template_content
            else:
                logger.warning(f"Prompt '{name}' not found in database")
        
        return prompts
    
    run_id = config.get('run_id')
    dag_id = config.get('dag_id')
    database_url = config.get('database_url')
    openai_api_key = config.get('openai_api_key')
    openai_api_base = config.get('openai_api_base')
    processing_config = config.get('processing_config')

    if not all([run_id, dag_id, database_url, openai_api_key, processing_config]):
        raise ValueError("Missing required config: run_id, dag_id, database_url, openai_api_key, processing_config")
    
    # Set OpenAI API configuration for DocETL
    os.environ['OPENAI_API_KEY'] = openai_api_key
    if openai_api_base:
        os.environ['OPENAI_API_BASE'] = openai_api_base
        logger.info(f"Using custom OpenAI API base: {openai_api_base}")

    logger.info("=" * 80)
    logger.info(f"DOCETL PROCESSING START - Run ID: {run_id}")
    logger.info("=" * 80)

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    paper_repo = PaperRepository(session)
    article_repo = ArticleRepository(session)
    prompt_repo = PromptRepository(session)
    pipeline_repo = PipelineRunRepository(session)
    transaction_mgr = TransactionManager(session)
    
    counts = {
        'total_processed': 0,
        'completed': 0,
        'failed': 0,
        'skipped': 0,
        'total_cost': 0.0,
    }
    
    batch_size = processing_config.get('batch_size', 10)
    
    try:
        # Get or create pipeline run (idempotent for retries)
        pipeline_run, created = pipeline_repo.get_or_create_run(
            run_id=run_id,
            dag_id=dag_id,
            execution_date=datetime.utcnow(),
            pipeline_type='docetl_processing',
            status='running',
            started_at=datetime.utcnow(),
            metrics=processing_config
        )
        
        # If run already exists (retry), reset to running state
        if not created:
            logger.info(f"Resuming existing pipeline run: {pipeline_run.id}")
            pipeline_run.status = 'running'
            pipeline_run.error_message = None
        else:
            logger.info(f"Created new pipeline run: {pipeline_run.id}")
        
        transaction_mgr.commit()
        
        # Load prompts from database
        prompts = _load_prompts_from_db(prompt_repo)
        
        # Initialize services
        pdf_service = create_extraction_service_from_env(processing_config)
        docetl_service = create_docetl_service_from_env(processing_config, prompts)
        validation_service = create_validation_service_from_env(processing_config) \
            if processing_config.get('enable_validation') else None
        
        generation_service = create_generation_service_from_env(
            processing_config,
            paper_repo,
            article_repo,
            prompt_repo,
            pdf_service,
            docetl_service,
            validation_service
        )
        
        # Fetch ready papers
        papers = paper_repo.find_by_status_batch('ready_to_process', limit=batch_size)
        logger.info(f"Found {len(papers)} papers ready to process")
        
        if not papers:
            logger.info("No papers to process")
            pipeline_run.status = 'completed'
            pipeline_run.completed_at = datetime.utcnow()
            pipeline_run.metrics = {**pipeline_run.metrics, **counts}
            transaction_mgr.commit()
            return counts
        
        # Process each paper
        for paper in papers:
            counts['total_processed'] += 1
            logger.info(f"Processing paper {counts['total_processed']}/{len(papers)}: {paper.arxiv_id}")
            
            try:
                result = generation_service.generate_article(paper)
                
                if result.success:
                    counts['completed'] += 1
                    logger.info(f"✓ Successfully generated article for {paper.arxiv_id}")
                else:
                    counts['failed'] += 1
                    logger.warning(f"✗ Failed to generate article for {paper.arxiv_id}: {result.message}")
                
                transaction_mgr.commit()
                
            except Exception as e:
                counts['failed'] += 1
                logger.error(f"✗ Error processing {paper.arxiv_id}: {str(e)[:200]}", exc_info=True)
                transaction_mgr.rollback()
                
                try:
                    paper_repo.update_status(paper, 'failed', f"Processing error: {str(e)[:200]}")
                    transaction_mgr.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update paper status: {update_error}")
                    transaction_mgr.rollback()
        
        # Update pipeline run
        pipeline_run.status = 'completed'
        pipeline_run.completed_at = datetime.utcnow()
        pipeline_run.metrics = {**pipeline_run.metrics, **counts}
        transaction_mgr.commit()
        
        logger.info("=" * 80)
        logger.info(f"DOCETL PROCESSING COMPLETE")
        logger.info(f"  Total Processed: {counts['total_processed']}")
        logger.info(f"  Completed: {counts['completed']}")
        logger.info(f"  Failed: {counts['failed']}")
        logger.info("=" * 80)
        
        return counts
        
    except Exception as e:
        logger.error(f"Fatal error in processing pipeline: {e}", exc_info=True)
        transaction_mgr.rollback()
        
        try:
            if 'pipeline_run' in locals():
                pipeline_run.status = 'failed'
                pipeline_run.completed_at = datetime.utcnow()
                pipeline_run.error_message = str(e)[:500]
                transaction_mgr.commit()
        except Exception as cleanup_error:
            logger.error(f"Failed to update pipeline run status: {cleanup_error}")
        
        raise
    
    finally:
        session.close()
        engine.dispose()


@task
def log_processing_summary(processing_result: dict) -> dict:
    """Log processing summary statistics."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("DOCETL PROCESSING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Processed:    {processing_result.get('total_processed', 0)}")
    logger.info(f"Completed:          {processing_result.get('completed', 0)}")
    logger.info(f"Failed:             {processing_result.get('failed', 0)}")
    logger.info(f"Skipped:            {processing_result.get('skipped', 0)}")
    logger.info("=" * 80)
    
    return processing_result

