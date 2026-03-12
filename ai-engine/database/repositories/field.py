"""
Field Repository
================
Repository for Field model with caching support.
"""

import logging
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models.fields import Field
from .base import BaseRepository

logger = logging.getLogger(__name__)


class FieldRepository(BaseRepository):
    """Repository for Field model with caching."""
    
    def __init__(self, session: Session):
        super().__init__(session, Field)
        self._cache: Dict[str, Field] = {}
        self._cache_initialized = False
    
    def get_all_cached(self, force_reload: bool = False) -> List[Field]:
        """Get all fields with caching."""
        if force_reload or not self._cache_initialized:
            self._initialize_cache()
        
        return list(self._cache.values())
    
    def find_by_code(self, code: str, parent_id: Optional[UUID] = None) -> Optional[Field]:
        """Find field by code (case-insensitive), with optional parent filter."""
        if self._cache_initialized:
            field = self._cache.get(code.lower())
            if field and (parent_id is None or field.parent_id == parent_id):
                return field
        
        query = self.session.query(Field).filter(
            func.lower(Field.code) == func.lower(code.strip())
        )
        
        if parent_id is not None:
            query = query.filter(Field.parent_id == parent_id)
        
        field = query.first()
        
        if field and self._cache_initialized:
            self._cache[field.code.lower()] = field
        
        return field
    
    def find_children(self, parent_id: UUID) -> List[Field]:
        """Find all child fields of a parent."""
        return self.find_all(parent_id=parent_id)
    
    def find_by_name(self, name: str) -> Optional[Field]:
        """Find field by name."""
        return self.find_one(name=name)
    
    def _initialize_cache(self) -> None:
        """Initialize field cache from database."""
        logger.info("Initializing field cache...")
        all_fields = self.session.query(Field).all()
        self._cache = {field.code.lower(): field for field in all_fields}
        self._cache_initialized = True
        logger.info(f"Cached {len(all_fields)} fields")
    
    def clear_cache(self):
        """Clear the field cache."""
        self._cache.clear()
        self._cache_initialized = False
        logger.debug("Field cache cleared")

