"""
Field Models
============
Database models for hierarchical field/taxonomy system supporting arXiv classifications.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Field(Base):
    """
    Hierarchical field/taxonomy model for paper categorization.
    Implements tree structure: physics/cs/math (top) -> cs.AI/cs.LG (sub).
    """

    __tablename__ = "fields"

    # Core identification
    code: Mapped[str] = mapped_column(String(50), nullable=False,
                                      comment="Field code (e.g., 'physics', 'cs.AI')")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="Human-readable name")

    # Hierarchy support
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("fields.id"),
                                                      nullable=True, comment="Parent field for hierarchy")
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0,
                                                      comment="Sort order within parent")

    # Self-referential hierarchy
    parent = relationship("Field", remote_side="Field.id", back_populates="children")
    children = relationship("Field", back_populates="parent", cascade="all, delete-orphan")

    # Paper relationships
    papers_primary_field = relationship("Paper", foreign_keys="Paper.primary_field_id",
                                        back_populates="primary_field")
    papers_primary_subfield = relationship("Paper", foreign_keys="Paper.primary_subfield_id",
                                           back_populates="primary_subfield")
    paper_fields = relationship("PaperField", back_populates="field", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('parent_id', 'code', name='uq_fields_parent_code'),
        Index('ix_fields_code', 'code'),
        Index('ix_fields_parent_id', 'parent_id'),
        Index('ix_fields_sort_order', 'sort_order'),
        Index('ix_fields_parent_sort', 'parent_id', 'sort_order'),
    )

    @property
    def full_path(self) -> str:
        """Get full hierarchical path (e.g., 'physics.astro-ph' or 'cs.AI')."""
        return f"{self.parent.full_path}.{self.code}" if self.parent else self.code

    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level field."""
        return self.parent_id is None

    @property
    def depth(self) -> int:
        """Get depth level in hierarchy."""
        return 0 if self.parent_id is None else self.parent.depth + 1

    @property
    def descendant_count(self) -> int:
        """Get total count of all descendants."""
        return len(self.children) + sum(child.descendant_count for child in self.children)

    def __repr__(self) -> str:
        return f"<Field(code='{self.code}', name='{self.name}', parent_id={self.parent_id})>"