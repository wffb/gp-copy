"""
arXiv Ingestion Models
======================
Database models for tracking arXiv paper ingestion runs and processing.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import String, Text, Integer, Float, ARRAY, Index, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PipelineRun(Base):
    """Generic pipeline/DAG run tracking for all pipeline types (ingestion, quality filter, etc.)."""

    __tablename__ = "pipeline_runs"

    # Airflow identification
    run_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="Airflow run_id")
    dag_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="DAG identifier")
    execution_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                     comment="DAG execution start time")

    # Pipeline type for filtering different pipeline runs
    pipeline_type: Mapped[str] = mapped_column(String(50), nullable=False, default="arxiv_ingestion",
                                               comment="Pipeline type: arxiv_ingestion, quality_filter, etc.")

    # Flexible metrics field for pipeline-specific data
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True,
                                                              comment="Pipeline-specific metrics and configuration")

    # Run status (running, completed, failed, partial)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running", comment="Run status")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Error details if failed")

    # Performance metrics
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                                     comment="Total processing time")

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 server_default='NOW()', comment="Run start time")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                             comment="Run completion time")

    # Relationships
    fetch_history = relationship("ArxivFetchHistory", back_populates="run", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_pipeline_runs_run_id', 'run_id'),
        Index('idx_pipeline_runs_dag_id', 'dag_id'),
        Index('idx_pipeline_runs_pipeline_type', 'pipeline_type'),
        Index('idx_pipeline_runs_execution_date', 'execution_date', postgresql_ops={'execution_date': 'DESC'}),
        Index('idx_pipeline_runs_status', 'status'),
        Index('idx_pipeline_runs_started_at', 'started_at', postgresql_ops={'started_at': 'DESC'}),
        Index('idx_pipeline_runs_completed_at', 'completed_at', postgresql_ops={'completed_at': 'DESC'}),
        Index('idx_pipeline_runs_status_started', 'status', 'started_at', postgresql_ops={'started_at': 'DESC'}),
        Index('idx_pipeline_runs_type_status', 'pipeline_type', 'status'),
    )

    @property
    def is_complete(self) -> bool:
        """Check if run is completed."""
        return self.status in ('completed', 'failed', 'partial')

    @property
    def is_successful(self) -> bool:
        """Check if run completed successfully."""
        return self.status == 'completed'

    def get_metric(self, key: str, default: Any = None) -> Any:
        """Get a specific metric value."""
        if not self.metrics:
            return default
        return self.metrics.get(key, default)

    def set_metric(self, key: str, value: Any) -> None:
        """Set a specific metric value."""
        if not self.metrics:
            self.metrics = {}
        self.metrics[key] = value

    def __repr__(self) -> str:
        return f"<PipelineRun(run_id='{self.run_id}', type='{self.pipeline_type}', status='{self.status}')>"


class ArxivFetchHistory(Base):
    """API audit trail: Track individual arXiv API fetch requests and responses."""

    __tablename__ = "arxiv_fetch_history"

    # Run reference
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),
                                         ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
                                         nullable=False, comment="Pipeline run reference")

    # Paper identification
    arxiv_id: Mapped[str] = mapped_column(String(50), nullable=False,
                                          comment="arXiv ID with version (e.g., '1903.12284v3')")
    paper_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True),
                                                     ForeignKey("papers.id", ondelete="SET NULL"),
                                                     nullable=True, comment="Link to papers table if ingested")

    # Ingestion status: processing → new/updated/skipped/failed
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="processing",
                                        comment="Ingestion status: processing, new, updated, skipped, failed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, 
                                                         comment="Error/reason: failure details or skip reason")

    # API request/response tracking
    paper_request: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True,
                                                                     comment="API request parameters sent")
    paper_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True,
                                                                      comment="API response (raw + transformed)")

    # Relationships
    run = relationship("PipelineRun", back_populates="fetch_history")
    paper = relationship("Paper", foreign_keys=[paper_id])

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('run_id', 'arxiv_id', name='uq_fetch_history_run_arxiv'),
        Index('idx_fetch_history_run_id', 'run_id'),
        Index('idx_fetch_history_arxiv_id', 'arxiv_id'),
        Index('idx_fetch_history_paper_id', 'paper_id'),
        Index('idx_fetch_history_status', 'status'),
        Index('idx_fetch_history_status_run', 'status', 'run_id'),
    )

    @property
    def is_successful(self) -> bool:
        """Check if paper was successfully ingested."""
        return self.status in ('new', 'updated', 'skipped')

    @property
    def is_failed(self) -> bool:
        """Check if ingestion failed."""
        return self.status == 'failed'

    @property
    def is_new(self) -> bool:
        """Check if paper is new."""
        return self.status == 'new'

    @property
    def is_updated(self) -> bool:
        """Check if paper was updated."""
        return self.status == 'updated'

    @property
    def is_skipped(self) -> bool:
        """Check if paper was skipped."""
        return self.status == 'skipped'

    @property
    def is_processing(self) -> bool:
        """Check if still processing."""
        return self.status == 'processing'

    def __repr__(self) -> str:
        return f"<ArxivFetchHistory(arxiv_id='{self.arxiv_id}', status='{self.status}')>"