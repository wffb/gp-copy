"""
Paper Models
============
Database models for research papers and related entities.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Index, UniqueConstraint, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Paper(Base):
    """
    Research paper with bibliographic info, content, categorization, and processing status.
    Links to authors, fields, and generated articles.
    """

    __tablename__ = "papers"

    # Basic bibliographic information
    title: Mapped[str] = mapped_column(Text, nullable=False, comment="Paper title")
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Paper abstract")

    # Identifiers
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Digital Object Identifier")
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True,
                                                    comment="arXiv identifier (e.g., 2301.12345v1)")

    # Categories and subjects from arXiv
    subjects: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True, comment="arXiv subjects")
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True, comment="arXiv categories")

    # Hierarchical field classification
    primary_field_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("fields.id"),
                                                             nullable=True, comment="Primary top-level field")
    primary_subfield_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("fields.id"),
                                                                nullable=True, comment="Primary subfield")

    # URLs and external references
    pdf_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="PDF URL")

    # Publication dates
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                               comment="Publication date")
    submitted_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                               comment="arXiv submission date")
    updated_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                             comment="arXiv last update date")

    # Processing status (pending, ready_to_process, processing, completed, rejected, failed)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="pending",
                                                  comment="Processing status")
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True,
                                                   comment="Quality filter rejection reason or processing message")

    # Extracted content
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True,
                                                          comment="Full extracted text from PDF")
    text_chunks: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True,
                                                                  comment="Chunked text for LLM processing")

    # Field relationships
    primary_field = relationship("Field", foreign_keys=[primary_field_id],
                                 back_populates="papers_primary_field")
    primary_subfield = relationship("Field", foreign_keys=[primary_subfield_id],
                                    back_populates="papers_primary_subfield")

    # Many-to-many relationships
    paper_authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan",
                                 order_by="PaperAuthor.author_order")
    paper_fields = relationship("PaperField", back_populates="paper", cascade="all, delete-orphan")

    # One-to-many relationships
    articles = relationship("Article", back_populates="paper", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_papers_title', 'title'),
        Index('ix_papers_arxiv_id', 'arxiv_id'),
        Index('ix_papers_doi', 'doi'),
        Index('ix_papers_status', 'status'),
        Index('ix_papers_published_date', 'published_date'),
        Index('ix_papers_submitted_date', 'submitted_date'),
        Index('ix_papers_primary_field_id', 'primary_field_id'),
        Index('ix_papers_primary_subfield_id', 'primary_subfield_id'),
        Index('ix_papers_status_submitted', 'status', 'submitted_date'),
        Index('ix_papers_field_submitted', 'primary_field_id', 'submitted_date'),
    )

    @property
    def authors(self) -> List['AuthorProfile']:
        """Get ordered list of authors."""
        return [pa.author for pa in sorted(self.paper_authors, key=lambda x: x.author_order or 0)]

    @property
    def author_names(self) -> List[str]:
        """Get list of author names in order."""
        return [author.name for author in self.authors]

    @property
    def fields(self) -> List['Field']:
        """Get all associated fields."""
        return [pf.field for pf in self.paper_fields]

    @property
    def field_codes(self) -> List[str]:
        """Get list of field codes."""
        return [field.code for field in self.fields]

    @property
    def corresponding_authors(self) -> List['AuthorProfile']:
        """Get list of corresponding authors."""
        return [pa.author for pa in self.paper_authors if pa.corresponding]

    @property
    def has_articles(self) -> bool:
        """Check if paper has generated articles."""
        return len(self.articles) > 0

    def __repr__(self) -> str:
        return f"<Paper(arxiv_id='{self.arxiv_id}', title='{self.title[:50]}...')>"


class PaperAuthor(Base):
    """Junction table linking papers to authors with order and corresponding status."""

    __tablename__ = "paper_authors"

    # Override Base id
    id = None

    # Composite primary key
    paper_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("papers.id"),
                                           primary_key=True, nullable=False, comment="Paper reference")
    author_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("author_profiles.id"),
                                            primary_key=True, nullable=False, comment="Author reference")

    # Additional fields
    author_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True,
                                                        comment="Author order (1-based)")
    corresponding: Mapped[bool] = mapped_column(nullable=False, default=False,
                                                comment="Corresponding author flag")

    # Relationships
    paper = relationship("Paper", back_populates="paper_authors")
    author = relationship("AuthorProfile", back_populates="paper_authors")

    # Constraints
    __table_args__ = (
        UniqueConstraint('paper_id', 'author_order', name='uq_paper_authors_paper_order'),
        Index('ix_paper_authors_paper_id', 'paper_id'),
        Index('ix_paper_authors_author_id', 'author_id'),
        Index('ix_paper_authors_order', 'author_order'),
        Index('ix_paper_authors_corresponding', 'corresponding'),
    )

    def __repr__(self) -> str:
        return f"<PaperAuthor(paper_id={self.paper_id}, author_id={self.author_id}, order={self.author_order})>"


class PaperField(Base):
    """Junction table linking papers to additional fields beyond primary field/subfield."""

    __tablename__ = "paper_fields"

    # Override Base id
    id = None

    # Composite primary key
    paper_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("papers.id"),
                                           primary_key=True, nullable=False, comment="Paper reference")
    field_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("fields.id"),
                                           primary_key=True, nullable=False, comment="Field reference")

    # Relationships
    paper = relationship("Paper", back_populates="paper_fields")
    field = relationship("Field", back_populates="paper_fields")

    # Constraints
    __table_args__ = (
        Index('ix_paper_fields_paper_id', 'paper_id'),
        Index('ix_paper_fields_field_id', 'field_id'),
    )

    def __repr__(self) -> str:
        return f"<PaperField(paper_id={self.paper_id}, field_id={self.field_id})>"