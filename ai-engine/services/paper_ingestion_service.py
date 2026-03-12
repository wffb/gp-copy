"""
Paper Ingestion Service
========================
Service for ingesting fetched papers into the database.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session

from database.repositories.paper import PaperRepository
from database.repositories.author import AuthorRepository
from database.repositories.arxiv_ingestion import PipelineRunRepository
from database.transaction import TransactionManager
from utils.field_mapping import get_field_and_subfield_ids

logger = logging.getLogger(__name__)


class PaperIngestionError(Exception):
    """Base exception for paper ingestion errors."""
    pass


class PaperIngestionService:
    """
    Service for bulk ingestion of arXiv papers into database.
    
    Handles deduplication, author creation/linking, field mapping, and version tracking.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.paper_repo = PaperRepository(session)
        self.author_repo = AuthorRepository(session)
        self.pipeline_repo = PipelineRunRepository(session)
        self.transaction = TransactionManager(session)
    
    def ingest_papers(
        self,
        papers_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Ingest multiple papers, each in its own transaction.
        
        Isolating transactions ensures one paper's failure doesn't block others.
        """
        counts = {'new': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        
        for idx, paper_data in enumerate(papers_data):
            try:
                with self.transaction.transaction():
                    _, status = self._ingest_single(paper_data)
                    counts[status] += 1
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"Progress: {idx + 1}/{len(papers_data)} papers processed")
            
            except Exception as e:
                arxiv_id = paper_data.get('arxiv_id', 'unknown')
                logger.error(f"Transaction failed for paper {arxiv_id}: {e}")
                counts['failed'] += 1
                try:
                    self.session.rollback()
                except Exception:
                    pass
        
        logger.info(f"Batch ingestion complete: {counts}")
        return counts
    
    def _ingest_single(self, paper_data: Dict[str, Any]) -> Tuple[Optional[Any], str]:
        """
        Ingest single paper with deduplication and update logic.
        Updates fetch history with outcome and reason.
        
        Returns:
            Tuple of (Paper or None, status: 'new'|'updated'|'skipped'|'failed')
        """
        arxiv_id = paper_data.get('arxiv_id')
        fetch_record_id = paper_data.get('_fetch_record_id')
        
        if not arxiv_id:
            logger.error("Paper data missing arxiv_id")
            self._update_fetch_record(fetch_record_id, 'failed', None, "Missing arXiv ID")
            return (None, 'failed')
        
        try:
            existing = self.paper_repo.find_by_arxiv_id(arxiv_id)
            status, reason = self._determine_status_and_reason(existing, paper_data.get('updated_date', ''))
            
            if status == 'skipped':
                logger.debug(f"Skipping {arxiv_id}: {reason}")
                self._update_fetch_record(fetch_record_id, 'skipped', existing.id if existing else None, reason)
                return (existing, 'skipped')
            
            # Validate field mapping BEFORE creating/updating paper
            primary_category = paper_data.get('primary_category')
            if primary_category:
                field_mapping = get_field_and_subfield_ids(primary_category, self.session)
                if not field_mapping:
                    skip_reason = f"Field mapping failed: category '{primary_category}' not found in database"
                    logger.warning(f"Skipping {arxiv_id}: {skip_reason}")
                    self._update_fetch_record(fetch_record_id, 'skipped', existing.id if existing else None, skip_reason)
                    return (existing, 'skipped')
            
            paper = self._create_or_update_paper(existing, paper_data, status)
            
            self._process_and_link_authors(paper, paper_data.get('authors', []), status)
            self._process_and_link_fields(paper, paper_data.get('categories', []), status)
            
            self._update_fetch_record(fetch_record_id, status, paper.id, None)
            return (paper, status)
            
        except Exception as e:
            error_msg = str(e)[:1000]
            logger.error(f"Failed to ingest paper {arxiv_id}: {error_msg}", exc_info=True)
            self._update_fetch_record(fetch_record_id, 'failed', None, error_msg)
            return (None, 'failed')
    
    def _update_fetch_record(
        self,
        fetch_record_id: Optional[int],
        status: str,
        paper_id: Optional[int],
        error_message: Optional[str]
    ) -> None:
        """Update fetch history record with ingestion outcome."""
        if not fetch_record_id:
            return
        
        try:
            from database.models.arxiv_ingestion import ArxivFetchHistory
            fetch_record = self.session.query(ArxivFetchHistory).filter_by(id=fetch_record_id).first()
            
            if fetch_record:
                fetch_record.status = status
                if paper_id:
                    fetch_record.paper_id = paper_id
                if error_message:
                    fetch_record.error_message = error_message
                self.session.flush()
        except Exception as e:
            logger.warning(f"Failed to update fetch record {fetch_record_id}: {e}")
    
    def _determine_status_and_reason(
        self,
        existing: Optional[Any],
        new_updated_date: str
    ) -> Tuple[str, Optional[str]]:
        """Determine if paper is new, needs update, or should be skipped with reason."""
        if not existing:
            return ('new', None)
        
        try:
            new_date = datetime.fromisoformat(new_updated_date.replace('Z', '+00:00'))
        except Exception as e:
            reason = f"Could not parse date {new_updated_date}: {e}"
            logger.warning(reason)
            return ('skipped', reason)
        
        if existing.updated_date and new_date > existing.updated_date:
            return ('updated', None)
        
        return ('skipped', f"Already up-to-date (existing: {existing.updated_date}, new: {new_date})")
    
    def _create_or_update_paper(
        self,
        existing: Optional[Any],
        paper_data: Dict[str, Any],
        status: str
    ) -> Any:
        """Create new paper or update existing one."""
        if status == 'new':
            return self._create_paper(paper_data)
        else:
            return self._update_paper(existing, paper_data)
    
    def _create_paper(self, data: Dict[str, Any]) -> Any:
        """Create new paper from arXiv data."""
        published_date, updated_date = self._parse_dates(data)
        primary_field_id, primary_subfield_id = self._get_field_mapping(
            data.get('primary_category')
        )
        
        paper = self.paper_repo.create(
            arxiv_id=data['arxiv_id'],
            title=data['title'],
            abstract=data.get('abstract'),
            doi=data.get('doi'),
            subjects=data.get('subjects', []),
            categories=data.get('categories', []),
            primary_field_id=primary_field_id,
            primary_subfield_id=primary_subfield_id,
            pdf_url=data.get('pdf_url'),
            published_date=published_date,
            submitted_date=published_date,
            updated_date=updated_date,
            status='pending',
            extracted_text=None,
            text_chunks=None
        )
        
        logger.info(f"Created paper: {paper.arxiv_id} - {paper.title[:50]}...")
        return paper
    
    def _update_paper(self, existing: Any, data: Dict[str, Any]) -> Any:
        """Update existing paper with new arXiv data."""
        _, updated_date = self._parse_dates(data)
        primary_field_id, primary_subfield_id = self._get_field_mapping(
            data.get('primary_category')
        )
        
        self.paper_repo.update(
            existing,
            title=data['title'],
            abstract=data.get('abstract'),
            doi=data.get('doi'),
            subjects=data.get('subjects', []),
            categories=data.get('categories', []),
            pdf_url=data.get('pdf_url'),
            updated_date=updated_date,
            primary_field_id=primary_field_id,
            primary_subfield_id=primary_subfield_id
        )
        
        logger.info(f"Updated paper: {existing.arxiv_id}")
        return existing
    
    def _parse_dates(self, data: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse published and updated dates from arXiv data."""
        published_date = None
        updated_date = None
        
        if data.get('published_date'):
            try:
                published_date = datetime.fromisoformat(
                    data['published_date'].replace('Z', '+00:00')
                )
            except Exception as e:
                logger.warning(f"Could not parse published_date: {e}")
        
        if data.get('updated_date'):
            try:
                updated_date = datetime.fromisoformat(
                    data['updated_date'].replace('Z', '+00:00')
                )
            except Exception as e:
                logger.warning(f"Could not parse updated_date: {e}")
        
        return published_date, updated_date
    
    def _get_field_mapping(self, category: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """Get field and subfield IDs from arXiv category (or None if invalid/not found)."""
        if not category:
            return None, None
        
        mapping = get_field_and_subfield_ids(category, self.session)
        return mapping if mapping else (None, None)
    
    def _process_and_link_authors(
        self,
        paper: Any,
        authors_data: List[Dict[str, Any]],
        status: str
    ) -> None:
        """Process authors and link them to paper."""
        if not authors_data:
            return
        
        if status == 'updated':
            self.paper_repo.delete_authors(paper.id)
        
        authors_with_order = self._process_authors(authors_data)
        self._link_authors(paper, authors_with_order)
    
    def _process_authors(
        self,
        authors_data: List[Dict[str, Any]]
    ) -> List[Tuple[Any, int]]:
        """Create or find authors and return with their order (deduplicated)."""
        results = []
        seen_author_ids = set()
        
        for idx, author_data in enumerate(authors_data):
            name = author_data.get('name')
            if not name:
                logger.warning(f"Skipping author with no name at position {idx}")
                continue
            
            normalized_name = self._normalize_name(name)
            author = self._get_or_create_author(
                normalized_name,
                author_data.get('affiliation')
            )
            
            if author.id in seen_author_ids:
                logger.warning(f"Duplicate author {author.name} at position {idx}, skipping")
                continue
            
            seen_author_ids.add(author.id)
            results.append((author, idx))
        
        return results
    
    def _get_or_create_author(self, name: str, affiliation: Optional[str]) -> Any:
        """Find existing author or create new one."""
        author = self.author_repo.find_by_name(name)
        
        if author:
            if affiliation and (not author.affiliation or len(affiliation) > len(author.affiliation)):
                author.affiliation = affiliation
                logger.debug(f"Updated affiliation for {author.name}")
        else:
            author = self.author_repo.create(
                name=name,
                affiliation=affiliation,
                email=None,
                orcid=None,
                bio=None,
                website=None
            )
            logger.debug(f"Created new author: {author.name}")
        
        return author
    
    def _link_authors(self, paper: Any, authors_with_order: List[Tuple[Any, int]]) -> None:
        """Link authors to paper with their order."""
        for author, order in authors_with_order:
            self.paper_repo.link_author(
                paper_id=paper.id,
                author_id=author.id,
                order=order,
                corresponding=False
            )
    
    def _process_and_link_fields(
        self,
        paper: Any,
        categories: List[str],
        status: str
    ) -> None:
        """Process field categories and link them to paper (deduplicated)."""
        if not categories:
            return
        
        if status == 'updated':
            self.paper_repo.delete_fields(paper.id)
        
        seen_field_ids = set()
        for category in categories:
            _, subfield_id = self._get_field_mapping(category)
            if subfield_id and subfield_id not in seen_field_ids:
                self.paper_repo.link_field(paper_id=paper.id, field_id=subfield_id)
                seen_field_ids.add(subfield_id)
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize author name for consistent matching."""
        return ' '.join(name.strip().split()).title()