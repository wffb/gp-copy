"""
Article Repository
==================
Repository for Article, ArticleBlock, and ArticlePrompt models.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models.articles import Article, ArticleBlock, BlockType, ArticlePrompt
from .base import BaseRepository

logger = logging.getLogger(__name__)


class ArticleRepository(BaseRepository):
    """Repository for Article model with custom queries."""
    
    def __init__(self, session: Session):
        super().__init__(session, Article)
    
    def find_by_paper_id(self, paper_id: UUID) -> Optional[Article]:
        """Find article by paper ID."""
        return self.find_one(paper_id=paper_id)
    
    def find_by_slug(self, slug: str) -> Optional[Article]:
        """Find article by URL slug."""
        return self.find_one(slug=slug)
    
    def find_by_status_batch(self, status: str, limit: int = 50) -> List[Article]:
        """Find articles by status with limit."""
        return self.session.query(Article).filter(
            Article.status == status
        ).limit(limit).all()
    
    def update_status(self, article: Article, status: str) -> Article:
        """Update article status."""
        article.status = status
        self.session.flush()
        logger.debug(f"Updated article {article.slug} status to {status}")
        return article
    
    def create_with_blocks(self, article_data: Dict[str, Any], 
                          blocks_data: List[Dict[str, Any]]) -> Article:
        """
        Create article with blocks in a single transaction.
        
        Args:
            article_data: Article attributes (title, description, etc.)
            blocks_data: List of block dicts with block_type, content, order_index
            
        Returns:
            Created Article with blocks
        """
        article = self.create(**article_data)
        
        for block_data in blocks_data:
            block_data['article_id'] = article.id
            block = ArticleBlock(**block_data)
            self.session.add(block)
        
        self.session.flush()
        logger.info(f"Created article {article.slug} with {len(blocks_data)} blocks")
        return article
    
    def delete_blocks(self, article_id: UUID) -> int:
        """Delete all blocks for an article."""
        deleted = self.session.query(ArticleBlock).filter(
            ArticleBlock.article_id == article_id
        ).delete()
        self.session.flush()
        logger.debug(f"Deleted {deleted} blocks for article {article_id}")
        return deleted
    
    def add_block(self, article_id: UUID, block_type: BlockType, content: str, 
                  order_index: int, metadata: Optional[Dict[str, Any]] = None) -> ArticleBlock:
        """Add a block to an article."""
        block = ArticleBlock(
            article_id=article_id,
            block_type=block_type,
            content=content,
            order_index=order_index,
            block_metadata=metadata
        )
        self.session.add(block)
        self.session.flush()
        return block
    
    def get_blocks(self, article_id: UUID) -> List[ArticleBlock]:
        """Get all blocks for an article, ordered by order_index."""
        return self.session.query(ArticleBlock).filter(
            ArticleBlock.article_id == article_id
        ).order_by(ArticleBlock.order_index).all()
    
    def link_prompt(self, article_id: UUID, prompt_id: UUID) -> Optional[ArticlePrompt]:
        """Link prompt to article, returns None if already linked."""
        existing = self.session.query(ArticlePrompt).filter(
            ArticlePrompt.article_id == article_id,
            ArticlePrompt.prompt_id == prompt_id
        ).first()
        
        if existing:
            return None
        
        article_prompt = ArticlePrompt(article_id=article_id, prompt_id=prompt_id)
        self.session.add(article_prompt)
        self.session.flush()
        return article_prompt
    
    def increment_view_count(self, article_id: UUID) -> int:
        """Increment view count for article, returns new count."""
        article = self.get_by_id(article_id)
        if article:
            article.view_count += 1
            self.session.flush()
            return article.view_count
        return 0
    
    def update_engagement_metrics(self, article_id: UUID, 
                                  metrics: Dict[str, Any]) -> Optional[Article]:
        """Update engagement metrics for article."""
        article = self.get_by_id(article_id)
        if article:
            article.engagement_metrics = metrics
            self.session.flush()
            logger.debug(f"Updated engagement metrics for article {article.slug}")
        return article
    
    def get_published_articles(self, limit: int = 100, offset: int = 0) -> List[Article]:
        """Get published articles ordered by created_at descending."""
        return self.session.query(Article).filter(
            Article.status == 'published'
        ).order_by(Article.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_popular_articles(self, limit: int = 10) -> List[Article]:
        """Get most popular articles by view count."""
        return self.session.query(Article).filter(
            Article.status == 'published'
        ).order_by(Article.view_count.desc()).limit(limit).all()
    
    def search_by_keywords(self, keywords: List[str], limit: int = 50) -> List[Article]:
        """Search articles by keywords."""
        return self.session.query(Article).filter(
            Article.keywords.overlap(keywords),
            Article.status == 'published'
        ).limit(limit).all()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get article statistics."""
        return {
            'total': self.count(),
            'published': self.count(status='published'),
            'draft': self.count(status='draft'),
            'total_views': self.session.query(func.sum(Article.view_count)).scalar() or 0,
        }


class PromptRepository(BaseRepository):
    """Repository for Prompt model with versioning support."""
    
    def __init__(self, session: Session):
        from database.models.prompts import Prompt
        super().__init__(session, Prompt)
    
    def find_active_by_name(self, name: str) -> Optional[Any]:
        """Find active prompt by name."""
        from database.models.prompts import Prompt
        return self.session.query(Prompt).filter(
            Prompt.name == name,
            Prompt.is_active == True
        ).first()
    
    def find_by_name_and_version(self, name: str, version: int) -> Optional[Any]:
        """Find prompt by name and version."""
        from database.models.prompts import Prompt
        return self.session.query(Prompt).filter(
            Prompt.name == name,
            Prompt.version == version
        ).first()
    
    def get_active_prompts_by_type(self, prompt_type: str) -> List[Any]:
        """Get all active prompts of a specific type."""
        from database.models.prompts import Prompt, PromptType
        return self.session.query(Prompt).filter(
            Prompt.type == PromptType(prompt_type),
            Prompt.is_active == True
        ).all()
    
    def deactivate_version(self, prompt_id: UUID) -> bool:
        """Deactivate a prompt version."""
        from database.models.prompts import Prompt
        prompt = self.session.query(Prompt).filter(Prompt.id == prompt_id).first()
        if prompt:
            prompt.is_active = False
            self.session.flush()
            logger.info(f"Deactivated prompt {prompt.name} version {prompt.version}")
            return True
        return False

