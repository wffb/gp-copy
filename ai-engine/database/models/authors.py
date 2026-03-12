"""
Author Models
=============
Database models for author-related entities.
"""

from typing import Optional, List

from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AuthorProfile(Base):
    """Author profile with identification, affiliation, and professional details."""

    __tablename__ = "author_profiles"

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="Author full name")
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Email address")

    # Professional information
    affiliation: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Institutional affiliation")
    orcid: Mapped[Optional[str]] = mapped_column(String(19), nullable=True, unique=True,
                                                 comment="ORCID identifier (0000-0000-0000-0000)")

    # Additional information
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Author biography")
    website: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="Personal/professional website")

    # Relationships
    paper_authors = relationship("PaperAuthor", back_populates="author", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_author_profiles_name', 'name'),
        Index('ix_author_profiles_email', 'email'),
        Index('ix_author_profiles_orcid', 'orcid'),
        Index('ix_author_profiles_affiliation', 'affiliation'),
    )

    @property
    def papers(self) -> List['Paper']:
        """Get all papers by this author."""
        return [pa.paper for pa in self.paper_authors]

    @property
    def paper_count(self) -> int:
        """Get count of papers by this author."""
        return len(self.paper_authors)

    def __repr__(self) -> str:
        return f"<AuthorProfile(name='{self.name}', orcid='{self.orcid}')>"