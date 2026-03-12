"""
Paper Repository
================
Repository for Paper, PaperAuthor, and PaperField models.
"""

import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from database.models.papers import Paper, PaperAuthor, PaperField
from .base import BaseRepository

logger = logging.getLogger(__name__)


class PaperRepository(BaseRepository):
    """Repository for Paper model with custom queries."""
    
    def __init__(self, session: Session):
        super().__init__(session, Paper)
    
    def find_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        """Find paper by arXiv ID."""
        return self.find_one(arxiv_id=arxiv_id)
    
    def find_by_doi(self, doi: str) -> Optional[Paper]:
        """Find paper by DOI."""
        return self.find_one(doi=doi)
    
    def find_by_status_batch(self, status: str, limit: int = 50) -> List[Paper]:
        """Find papers by status with limit."""
        return self.session.query(Paper).filter(
            Paper.status == status
        ).limit(limit).all()
    
    def update_status(self, paper: Paper, status: str, message: Optional[str] = None) -> Paper:
        """Update paper status and message."""
        paper.status = status
        paper.message = message
        self.session.flush()
        logger.debug(f"Updated paper {paper.arxiv_id} status to {status}")
        return paper
    
    def delete_authors(self, paper_id: UUID) -> int:
        """Delete all author associations for a paper."""
        deleted = self.session.query(PaperAuthor).filter(
            PaperAuthor.paper_id == paper_id
        ).delete()
        self.session.flush()
        logger.debug(f"Deleted {deleted} author associations for paper {paper_id}")
        return deleted
    
    def delete_fields(self, paper_id: UUID) -> int:
        """Delete all field associations for a paper."""
        deleted = self.session.query(PaperField).filter(
            PaperField.paper_id == paper_id
        ).delete()
        self.session.flush()
        logger.debug(f"Deleted {deleted} field associations for paper {paper_id}")
        return deleted
    
    def link_author(self, paper_id: UUID, author_id: UUID, order: int, 
                    corresponding: bool = False) -> PaperAuthor:
        """Link author to paper with order and corresponding flag."""
        paper_author = PaperAuthor(
            paper_id=paper_id,
            author_id=author_id,
            author_order=order,
            corresponding=corresponding
        )
        self.session.add(paper_author)
        self.session.flush()
        return paper_author
    
    def link_field(self, paper_id: UUID, field_id: UUID) -> Optional[PaperField]:
        """Link field to paper, returns None if already linked."""
        existing = self.session.query(PaperField).filter(
            PaperField.paper_id == paper_id,
            PaperField.field_id == field_id
        ).first()
        
        if existing:
            return None
        
        paper_field = PaperField(paper_id=paper_id, field_id=field_id)
        self.session.add(paper_field)
        self.session.flush()
        return paper_field

