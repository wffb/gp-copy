"""
Article Models
==============
Database models for generated articles and related entities.
"""

import enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import String, Text, Boolean, BigInteger, Integer, ForeignKey, Index, UniqueConstraint, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BlockType(enum.Enum):
    """Article content block types."""
    TITLE = "title"
    PARAGRAPH = "paragraph"
    SUBHEADING = "subheading"
    QUOTE = "quote"
    IMAGE = "image"


class Article(Base):
    """
    Generated article with metadata, content blocks, and performance metrics.
    Linked to source paper and associated prompts.
    """

    __tablename__ = "articles"

    # Foreign key to source paper
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id"),
        nullable=False,
        comment="Reference to source paper"
    )

    # Basic article information
    title: Mapped[str] = mapped_column(Text, nullable=False, comment="Article title")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="Article summary")
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True, comment="Article keywords")
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="URL-friendly slug")

    # Publishing status (draft, review, published, archived)
    status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="draft", comment="Publication status"
    )

    # Visual elements
    featured_image_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="Featured image URL"
    )

    # Editorial information
    is_edited: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Manual edit flag"
    )

    # Performance metrics
    view_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="Page views")
    engagement_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="Engagement data (time on page, shares, etc.)"
    )

    # Relationships
    paper = relationship("Paper", back_populates="articles")
    blocks = relationship("ArticleBlock", back_populates="article", cascade="all, delete-orphan",
                          order_by="ArticleBlock.order_index")
    article_prompts = relationship("ArticlePrompt", back_populates="article", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_articles_paper_id', 'paper_id'),
        Index('ix_articles_slug', 'slug'),
        Index('ix_articles_status', 'status'),
        Index('ix_articles_title', 'title'),
        Index('ix_articles_description', 'description'),
        Index('ix_articles_view_count', 'view_count'),
        Index('ix_articles_created_at', 'created_at'),
        Index('ix_articles_is_edited', 'is_edited'),
        Index('ix_articles_status_created', 'status', 'created_at'),
        Index('ix_articles_paper_status', 'paper_id', 'status'),
    )

    @property
    def prompts(self) -> List['Prompt']:
        """Get all prompts used for this article."""
        return [ap.prompt for ap in self.article_prompts]

    @property
    def word_count(self) -> int:
        """Calculate word count from text blocks."""
        return sum(len(block.content.split()) for block in self.blocks
                   if block.content and block.block_type in [BlockType.PARAGRAPH, BlockType.QUOTE])

    @property
    def is_published(self) -> bool:
        """Check if article is published."""
        return self.status == "published"

    def __repr__(self) -> str:
        return f"<Article(slug='{self.slug}', title='{self.title[:50]}...')>"


class ArticleBlock(Base):
    """Individual content block within an article (paragraph, heading, quote, etc.)."""

    __tablename__ = "article_blocks"

    # Foreign key to parent article
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id"), nullable=False, comment="Parent article reference"
    )

    # Block information
    block_type: Mapped[BlockType] = mapped_column(
        Enum(BlockType, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="Content block type"
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Block content")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="Position within article")
    block_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="Block-specific metadata"
    )

    # Relationships
    article = relationship("Article", back_populates="blocks")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('article_id', 'order_index', name='uq_article_blocks_article_order'),
        Index('ix_article_blocks_article_id', 'article_id'),
        Index('ix_article_blocks_type', 'block_type'),
        Index('ix_article_blocks_order', 'order_index'),
        Index('ix_article_blocks_article_order', 'article_id', 'order_index'),
    )

    @property
    def word_count(self) -> int:
        """Get word count for this block."""
        return len(self.content.split()) if self.content else 0

    def __repr__(self) -> str:
        content_preview = (self.content[:50] + "...") if self.content else "None"
        return f"<ArticleBlock(type={self.block_type.value}, order={self.order_index}, content='{content_preview}')>"


class ArticlePrompt(Base):
    """Junction table linking articles to prompts used for generation."""

    __tablename__ = "article_prompts"

    # Foreign keys
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id"), nullable=False, comment="Article reference"
    )
    prompt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, comment="Prompt reference"
    )

    # Relationships
    article = relationship("Article", back_populates="article_prompts")
    prompt = relationship("Prompt", back_populates="article_prompts")

    # Constraints
    __table_args__ = (
        UniqueConstraint('article_id', 'prompt_id', name='uq_article_prompts_article_prompt'),
        Index('ix_article_prompts_article_id', 'article_id'),
        Index('ix_article_prompts_prompt_id', 'prompt_id'),
    )

    def __repr__(self) -> str:
        return f"<ArticlePrompt(article_id={self.article_id}, prompt_id={self.prompt_id})>"