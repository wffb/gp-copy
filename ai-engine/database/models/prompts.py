"""
Prompt Models
=============
Database models for AI prompt templates and versioning.
"""

import enum
from typing import Optional, Dict, Any

from sqlalchemy import String, Text, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PromptType(enum.Enum):
    """AI prompt types used in the content generation pipeline."""
    ARTICLE = "article"
    IMAGE = "image"
    VIDEO = "video"
    TEXT_TO_SPEECH = "text-to-speech"


class Prompt(Base):
    """
    AI prompt template with versioning support.
    Links to articles through ArticlePrompt junction table.
    """

    __tablename__ = "prompts"

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="Human-readable prompt name")
    type: Mapped[PromptType] = mapped_column(
        Enum(PromptType, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="Prompt type"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Prompt description")

    # Prompt content (Jinja2 template)
    template_content: Mapped[str] = mapped_column(Text, nullable=False, default="", 
                                                  comment="Jinja2 template content for prompt rendering")

    # Versioning and configuration
    version: Mapped[int] = mapped_column(nullable=False, default=1, comment="Version number for A/B testing and rollback")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, comment="Whether this prompt version is currently active")
    prompt_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True, 
                                                                       comment="Prompt configuration (temperature, max_tokens, model preferences)")

    # Relationships
    article_prompts = relationship("ArticlePrompt", back_populates="prompt", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_prompts_name', 'name'),
        Index('ix_prompts_type', 'type'),
        Index('ix_prompts_type_active', 'type', 'is_active', postgresql_where=is_active),
        Index('ix_prompts_name_version', 'name', 'version'),
    )

    @property
    def articles(self):
        """Get all articles that used this prompt."""
        return [ap.article for ap in self.article_prompts]

    @property
    def article_count(self) -> int:
        """Get count of articles using this prompt."""
        return len(self.article_prompts)

    def __repr__(self) -> str:
        return f"<Prompt(name='{self.name}', type='{self.type.value}')>"