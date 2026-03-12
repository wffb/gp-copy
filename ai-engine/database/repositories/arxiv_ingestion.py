"""
Pipeline Run Repository
=======================
Repository for PipelineRun (formerly ArxivIngestionRun) and ArxivFetchHistory models.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from database.models.arxiv_ingestion import PipelineRun, ArxivFetchHistory
from .base import BaseRepository

logger = logging.getLogger(__name__)


class PipelineRunRepository(BaseRepository):
    """Repository for generic pipeline/DAG run tracking."""
    
    def __init__(self, session: Session):
        super().__init__(session, PipelineRun)
    
    def find_by_run_id(self, run_id: str) -> Optional[PipelineRun]:
        """Find pipeline run by Airflow run_id."""
        return self.find_one(run_id=run_id)
    
    def find_by_dag_id(self, dag_id: str) -> List[PipelineRun]:
        """Find all runs for a DAG."""
        return self.find_all(dag_id=dag_id)
    
    def find_by_pipeline_type(self, pipeline_type: str) -> List[PipelineRun]:
        """Find all runs for a specific pipeline type."""
        return self.find_all(pipeline_type=pipeline_type)
    
    def get_or_create_run(self, run_id: str, **defaults) -> tuple[PipelineRun, bool]:
        """
        Get existing pipeline run or create a new one.
        
        Args:
            run_id: Airflow run ID
            **defaults: Fields to set if creating
            
        Returns:
            tuple: (PipelineRun instance, created: bool)
        """
        existing = self.find_by_run_id(run_id)
        if existing:
            logger.info(f"Found existing pipeline run: {run_id}")
            return existing, False
        
        logger.info(f"Creating new pipeline run: {run_id}")
        new_run = self.create(run_id=run_id, **defaults)
        return new_run, True
    
    def create_fetch_record(
        self,
        run_id: UUID,
        arxiv_id: str,
        status: str = "pending",
        paper_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
        paper_request: Optional[Dict[str, Any]] = None,
        paper_response: Optional[Dict[str, Any]] = None
    ) -> ArxivFetchHistory:
        """
        Create API fetch history record.
        
        Args:
            run_id: Ingestion run ID
            arxiv_id: arXiv paper ID
            status: API status (pending, processing, success, failed)
            paper_id: Link to papers table if successfully ingested
            error_message: Error details if failed
            paper_request: API request parameters
            paper_response: API response (raw + transformed)
        """
        fetch_record = ArxivFetchHistory(
            run_id=run_id,
            arxiv_id=arxiv_id,
            status=status,
            paper_id=paper_id,
            error_message=error_message,
            paper_request=paper_request,
            paper_response=paper_response
        )
        self.session.add(fetch_record)
        self.session.flush()
        return fetch_record
    
    def update_fetch_status(
        self,
        fetch_record: ArxivFetchHistory,
        status: str,
        paper_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
        paper_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update fetch history record with results."""
        fetch_record.status = status
        if paper_id:
            fetch_record.paper_id = paper_id
        if error_message:
            fetch_record.error_message = error_message
        if paper_response:
            fetch_record.paper_response = paper_response
        self.session.flush()
    
    def get_run_fetch_history(self, run_id: UUID) -> List[ArxivFetchHistory]:
        """Get all fetch history records for a run."""
        return self.session.query(ArxivFetchHistory).filter(
            ArxivFetchHistory.run_id == run_id
        ).all()

