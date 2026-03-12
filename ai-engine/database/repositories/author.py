"""
Author Repository
=================
Repository for AuthorProfile model.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models.authors import AuthorProfile
from .base import BaseRepository

logger = logging.getLogger(__name__)


class AuthorRepository(BaseRepository):
    """Repository for AuthorProfile model with custom queries."""
    
    def __init__(self, session: Session):
        super().__init__(session, AuthorProfile)
    
    def find_by_name(self, name: str, case_insensitive: bool = True) -> Optional[AuthorProfile]:
        """Find author by name (case-insensitive by default)."""
        if case_insensitive:
            return self.session.query(AuthorProfile).filter(
                func.lower(AuthorProfile.name) == func.lower(name.strip())
            ).first()
        else:
            return self.find_one(name=name.strip())
    
    def find_by_orcid(self, orcid: str) -> Optional[AuthorProfile]:
        """Find author by ORCID identifier."""
        return self.find_one(orcid=orcid)
    
    def find_by_email(self, email: str) -> Optional[AuthorProfile]:
        """Find author by email address."""
        return self.find_one(email=email)

