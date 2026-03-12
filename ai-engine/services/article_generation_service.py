"""
Article Generation Service
==========================
Orchestrates complete paper-to-article generation workflow using DocETL.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from uuid import UUID

from database.models.articles import Article, ArticleBlock, BlockType
from database.models.papers import Paper
from database.repositories.article import ArticleRepository, PromptRepository
from database.repositories.paper import PaperRepository
from services.docetl_service import DocETLService, ArticleComponents
from services.pdf_extraction_service import PDFExtractionService
from services.article_validation_service import ArticleValidationService, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Article generation configuration."""
    min_blocks: int = 5
    max_blocks: int = 20
    min_word_count: int = 500
    max_word_count: int = 2000
    enable_validation: bool = True
    max_retry_attempts: int = 2
    min_readability_score: float = 7.0
    min_engagement_score: float = 7.0
    min_accuracy_score: float = 9.0


@dataclass
class GenerationResult:
    """Result of article generation attempt."""
    success: bool
    article: Optional[Article] = None
    message: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    retry_count: int = 0


class ArticleGenerationService:
    """
    Service orchestrating complete paper-to-article generation.
    
    Workflow:
    1. Extract full PDF text and figures
    2. Process with DocETL to generate article components
    3. Validate generated content
    4. Create article and blocks in database
    5. Retry if validation fails (up to max_retry_attempts)
    """
    
    def __init__(
        self,
        config: GenerationConfig,
        paper_repo: PaperRepository,
        article_repo: ArticleRepository,
        prompt_repo: PromptRepository,
        pdf_service: PDFExtractionService,
        docetl_service: DocETLService,
        validation_service: Optional[ArticleValidationService] = None
    ):
        self.config = config
        self.paper_repo = paper_repo
        self.article_repo = article_repo
        self.prompt_repo = prompt_repo
        self.pdf_service = pdf_service
        self.docetl_service = docetl_service
        self.validation_service = validation_service
    
    def generate_article(self, paper: Paper) -> GenerationResult:
        """
        Generate article from paper with validation and retry logic.
        
        Args:
            paper: Paper instance (must have status='ready_to_process')
            
        Returns:
            GenerationResult with success status and created article or error message
        """
        if paper.status != 'ready_to_process':
            return GenerationResult(
                success=False,
                message=f"Paper status is '{paper.status}', expected 'ready_to_process'"
            )
        
        logger.info(f"Generating article for paper {paper.arxiv_id}")
        
        try:
            # Update paper status to 'processing'
            self.paper_repo.update_status(paper, 'processing', None)
            
            # Extract full PDF content
            pdf_content = self.pdf_service.extract_from_url(paper.pdf_url, paper.arxiv_id)
            paper.extracted_text = pdf_content.full_text
            paper.text_chunks = self.pdf_service.extract_text_chunks(pdf_content.full_text)
            
            # Prepare paper data for DocETL
            paper_data = self._prepare_paper_data(paper, pdf_content)
            
            # Generate article with retry logic
            for attempt in range(self.config.max_retry_attempts):
                logger.info(f"Generation attempt {attempt + 1}/{self.config.max_retry_attempts} for {paper.arxiv_id}")
                
                result = self._generate_and_validate(paper, paper_data, attempt)
                
                if result.success:
                    logger.info(f"Successfully generated article for {paper.arxiv_id}")
                    return result
                
                logger.warning(f"Generation attempt {attempt + 1} failed: {result.message}")
            
            # All retries exhausted
            self.paper_repo.update_status(paper, 'failed', result.message)
            return result
            
        except Exception as e:
            error_msg = f"Article generation error: {str(e)[:200]}"
            logger.error(f"Failed to generate article for {paper.arxiv_id}: {error_msg}", exc_info=True)
            self.paper_repo.update_status(paper, 'failed', error_msg)
            return GenerationResult(success=False, message=error_msg)
    
    def _generate_and_validate(
        self, 
        paper: Paper, 
        paper_data: Dict[str, Any], 
        attempt: int
    ) -> GenerationResult:
        """Single generation and validation attempt."""
        
        try:
            # Generate article components using DocETL
            components = self.docetl_service.process_paper_to_article(paper_data)
            
            # Validate structure
            structure_valid, structure_msg = self._validate_structure(components)
            if not structure_valid:
                return GenerationResult(
                    success=False,
                    message=f"Structure validation failed: {structure_msg}",
                    retry_count=attempt + 1
                )
            
            # Validate content quality (if validation service enabled)
            validation_result = None
            if self.config.enable_validation and self.validation_service:
                validation_result = self._validate_content(components, paper_data)
                
                if not validation_result.passed:
                    return GenerationResult(
                        success=False,
                        message=f"Content validation failed: {validation_result.summary}",
                        validation_result=validation_result,
                        retry_count=attempt + 1
                    )
            
            # Create article in database
            article = self._create_article_in_db(paper, components)
            
            # Update paper status to 'completed'
            self.paper_repo.update_status(paper, 'completed', None)
            
            return GenerationResult(
                success=True,
                article=article,
                validation_result=validation_result,
                retry_count=attempt + 1
            )
            
        except Exception as e:
            error_msg = f"Generation attempt failed: {str(e)[:200]}"
            logger.error(error_msg, exc_info=True)
            return GenerationResult(
                success=False,
                message=error_msg,
                retry_count=attempt + 1
            )
    
    @staticmethod
    def _sanitize_string(text: str) -> str:
        """
        Sanitize string by removing NUL bytes that PostgreSQL cannot store.

        This is a defensive check - the PDF service should already sanitize,
        but we ensure safety at the database boundary as well.
        """
        if not text:
            return text
        return text.replace('\x00', '')

    def _prepare_paper_data(self, paper: Paper, pdf_content: Any) -> Dict[str, Any]:
        """Prepare paper data dict for DocETL processing."""
        return {
            'arxiv_id': paper.arxiv_id,
            'title': self._sanitize_string(paper.title) if paper.title else paper.title,
            'abstract': self._sanitize_string(paper.abstract) if paper.abstract else '',
            'extracted_text': pdf_content.full_text,  # Already sanitized by PDF service
            'page_count': pdf_content.page_count,
            'figure_count': len(pdf_content.figures),
            'authors': paper.author_names,
            'published_date': paper.published_date.isoformat() if paper.published_date else None,
            'categories': paper.categories or [],
        }
    
    def _validate_structure(self, components: ArticleComponents) -> Tuple[bool, Optional[str]]:
        """Validate article structure meets basic requirements."""
        
        # Check blocks count
        if not components.blocks:
            return False, "No blocks generated"
        
        if len(components.blocks) < self.config.min_blocks:
            return False, f"Too few blocks: {len(components.blocks)} (min: {self.config.min_blocks})"
        
        if len(components.blocks) > self.config.max_blocks:
            return False, f"Too many blocks: {len(components.blocks)} (max: {self.config.max_blocks})"
        
        # Check required block types
        block_types = [b.get('block_type') for b in components.blocks]
        
        if 'title' not in block_types:
            return False, "Missing title block"
        
        if 'paragraph' not in block_types:
            return False, "Missing paragraph blocks"
        
        # Check word count
        total_words = sum(
            len(b.get('content', '').split())
            for b in components.blocks
            if b.get('block_type') in ['paragraph', 'quote']
        )
        
        if total_words < self.config.min_word_count:
            return False, f"Article too short: {total_words} words (min: {self.config.min_word_count})"
        
        if total_words > self.config.max_word_count:
            return False, f"Article too long: {total_words} words (max: {self.config.max_word_count})"
        
        # Check slug
        if not components.slug or len(components.slug) < 10:
            return False, "Invalid or missing slug"
        
        return True, None
    
    def _validate_content(
        self, 
        components: ArticleComponents, 
        paper_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate article content quality using validation service."""
        
        # Use validation results from DocETL if available
        if components.validation_results:
            readability = components.validation_results.get('readability_score', 0.0)
            engagement = components.validation_results.get('engagement_score', 0.0)
            accuracy = components.validation_results.get('accuracy_score', 0.0)
            
            passed = (
                readability >= self.config.min_readability_score and
                engagement >= self.config.min_engagement_score and
                accuracy >= self.config.min_accuracy_score
            )
            
            issues = []
            if readability < self.config.min_readability_score:
                issues.append(f"Readability: {readability:.1f}/{self.config.min_readability_score}")
            if engagement < self.config.min_engagement_score:
                issues.append(f"Engagement: {engagement:.1f}/{self.config.min_engagement_score}")
            if accuracy < self.config.min_accuracy_score:
                issues.append(f"Accuracy: {accuracy:.1f}/{self.config.min_accuracy_score}")
            
            return ValidationResult(
                passed=passed,
                readability_score=readability,
                engagement_score=engagement,
                accuracy_score=accuracy,
                issues=issues,
                summary="; ".join(issues) if issues else "All validations passed"
            )
        
        # Fallback: call validation service directly
        return self.validation_service.validate_article(components, paper_data)
    
    def _create_article_in_db(self, paper: Paper, components: ArticleComponents) -> Article:
        """Create article with blocks in database."""

        # Prepare article data (sanitize all string fields)
        article_data = {
            'paper_id': paper.id,
            'title': self._sanitize_string(components.engaging_title),
            'description': self._sanitize_string(components.description),
            'keywords': components.keywords,  # List of strings
            'slug': self._ensure_unique_slug(self._sanitize_string(components.slug)),
            'status': 'draft',
        }
        
        # Prepare blocks data
        blocks_data = []
        for idx, block_dict in enumerate(components.blocks):
            block_type_str = block_dict.get('block_type', 'paragraph').lower()

            try:
                block_type = BlockType(block_type_str)
            except ValueError:
                logger.warning(f"Unknown block type '{block_type_str}', defaulting to PARAGRAPH")
                block_type = BlockType.PARAGRAPH

            # Sanitize block content to prevent NUL byte errors
            content = self._sanitize_string(block_dict.get('content', ''))

            blocks_data.append({
                'block_type': block_type,
                'content': content,
                'order_index': idx,
            })
        
        # Create article with blocks
        article = self.article_repo.create_with_blocks(article_data, blocks_data)
        
        logger.info(f"Created article {article.slug} with {len(blocks_data)} blocks")
        return article
    
    def _ensure_unique_slug(self, base_slug: str) -> str:
        """Ensure slug is unique, append counter if needed."""
        slug = base_slug
        counter = 1
        
        while self.article_repo.find_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


def create_generation_service_from_env(
    env_vars: Dict[str, Any],
    paper_repo: PaperRepository,
    article_repo: ArticleRepository,
    prompt_repo: PromptRepository,
    pdf_service: PDFExtractionService,
    docetl_service: DocETLService,
    validation_service: Optional[ArticleValidationService] = None
) -> ArticleGenerationService:
    """Create ArticleGenerationService from environment variables."""
    config = GenerationConfig(
        min_blocks=int(env_vars.get('min_blocks', 5)),
        max_blocks=int(env_vars.get('max_blocks', 20)),
        min_word_count=int(env_vars.get('min_word_count', 500)),
        max_word_count=int(env_vars.get('max_word_count', 2000)),
        enable_validation=env_vars.get('enable_validation', True),
        max_retry_attempts=int(env_vars.get('max_retries', 2)),
        min_readability_score=float(env_vars.get('min_readability_score', 7.0)),
        min_engagement_score=float(env_vars.get('min_engagement_score', 7.0)),
        min_accuracy_score=float(env_vars.get('min_accuracy_score', 9.0)),
    )
    
    return ArticleGenerationService(
        config=config,
        paper_repo=paper_repo,
        article_repo=article_repo,
        prompt_repo=prompt_repo,
        pdf_service=pdf_service,
        docetl_service=docetl_service,
        validation_service=validation_service
    )

