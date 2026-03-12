"""
Base Repository
===============
Base repository with common CRUD operations for all models.
"""

import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models.base import Base

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class BaseRepository:
    """Base repository providing common CRUD operations."""
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    def create(self, **data) -> T:
        """Create new model instance."""
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.flush()
        logger.debug(f"Created {self.model_class.__name__}: {instance.id}")
        return instance
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple instances efficiently."""
        instances = [self.model_class(**item) for item in items]
        self.session.add_all(instances)
        self.session.flush()
        logger.debug(f"Bulk created {len(instances)} {self.model_class.__name__} instances")
        return instances
    
    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get model instance by ID."""
        return self.session.query(self.model_class).filter(
            self.model_class.id == id
        ).first()
    
    def find_one(self, **filters) -> Optional[T]:
        """Find single instance matching filters."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if not hasattr(self.model_class, key):
                raise ValueError(f"Model {self.model_class.__name__} has no attribute '{key}'")
            query = query.filter(getattr(self.model_class, key) == value)
        return query.first()
    
    def find_all(self, **filters) -> List[T]:
        """Find all instances matching filters."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if not hasattr(self.model_class, key):
                raise ValueError(f"Model {self.model_class.__name__} has no attribute '{key}'")
            query = query.filter(getattr(self.model_class, key) == value)
        return query.all()
    
    def update(self, instance: T, **data) -> T:
        """Update model instance."""
        instance.update_from_dict(data)
        self.session.flush()
        logger.debug(f"Updated {self.model_class.__name__}: {instance.id}")
        return instance
    
    def delete_by_id(self, id: UUID) -> bool:
        """Delete instance by ID, returns True if deleted."""
        deleted = self.session.query(self.model_class).filter(
            self.model_class.id == id
        ).delete(synchronize_session='fetch')
        self.session.flush()
        
        if deleted:
            logger.debug(f"Deleted {self.model_class.__name__}: {id}")
        return deleted > 0
    
    def delete_where(self, **filters) -> int:
        """Delete all instances matching filters, returns count."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if not hasattr(self.model_class, key):
                raise ValueError(f"Model {self.model_class.__name__} has no attribute '{key}'")
            query = query.filter(getattr(self.model_class, key) == value)
        
        deleted = query.delete(synchronize_session='fetch')
        self.session.flush()
        logger.debug(f"Deleted {deleted} {self.model_class.__name__} instances")
        return deleted
    
    def exists(self, **filters) -> bool:
        """Check if instance exists matching filters."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if not hasattr(self.model_class, key):
                raise ValueError(f"Model {self.model_class.__name__} has no attribute '{key}'")
            query = query.filter(getattr(self.model_class, key) == value)
        return self.session.query(query.exists()).scalar()
    
    def count(self, **filters) -> int:
        """Count instances matching filters."""
        query = self.session.query(func.count(self.model_class.id))
        for key, value in filters.items():
            if not hasattr(self.model_class, key):
                raise ValueError(f"Model {self.model_class.__name__} has no attribute '{key}'")
            query = query.filter(getattr(self.model_class, key) == value)
        return query.scalar()

