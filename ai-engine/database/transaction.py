"""
Transaction Manager
===================
Handles database transactions with automatic commit/rollback and batch operations.
"""

import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TransactionManager:
    """
    Manages database transactions with automatic commit/rollback.
    
    Usage:
        with transaction_manager.transaction():
            # Single transaction with auto-commit
        
        with transaction_manager.batch():
            # Batch operations, commits at end
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    @contextmanager
    def transaction(self, auto_commit: bool = True):
        """Transaction context with automatic commit/rollback."""
        try:
            yield self.session
            if auto_commit:
                self.session.commit()
                logger.debug("Transaction committed")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    @contextmanager
    def batch(self):
        """Batch transaction for bulk operations. Commits once at end."""
        try:
            yield self.session
            self.session.commit()
            logger.debug("Batch transaction committed")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Batch transaction rolled back: {e}")
            raise
    
    def commit(self):
        """Manually commit current transaction."""
        try:
            self.session.commit()
            logger.debug("Manual commit successful")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Manual commit failed: {e}")
            raise
    
    def rollback(self):
        """Manually rollback current transaction."""
        self.session.rollback()
        logger.debug("Manual rollback executed")
    
    def flush(self):
        """Flush pending changes without committing."""
        self.session.flush()