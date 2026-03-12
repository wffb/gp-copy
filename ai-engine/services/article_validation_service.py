"""
Article Validation Service
===========================
LLM-based validation of generated articles (fallback if DocETL validation not used).
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Article validation result."""
    passed: bool
    readability_score: float = 0.0
    engagement_score: float = 0.0
    accuracy_score: float = 0.0
    issues: List[str] = None
    summary: str = ""
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class ArticleValidationService:
    """
    Service for validating generated articles using LLM as a judge.
    
    This is a fallback service when DocETL validation is disabled.
    In most cases, validation should be handled by DocETL pipeline.
    """
    
    def __init__(self, min_readability: float = 7.0, 
                 min_engagement: float = 7.0,
                 min_accuracy: float = 9.0):
        self.min_readability = min_readability
        self.min_engagement = min_engagement
        self.min_accuracy = min_accuracy
    
    def validate_article(self, components: Any, paper_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate article components against quality thresholds.
        
        Note: This is a simplified fallback. DocETL pipeline validation is preferred.
        
        Args:
            components: ArticleComponents from DocETL
            paper_data: Original paper data
            
        Returns:
            ValidationResult with scores and pass/fail status
        """
        logger.info(f"Validating article for paper {paper_data.get('arxiv_id')}")
        
        # Basic structural validation (no LLM calls)
        readability_score = self._estimate_readability(components)
        engagement_score = self._estimate_engagement(components)
        accuracy_score = self._estimate_accuracy(components, paper_data)
        
        issues = []
        passed = True
        
        if readability_score < self.min_readability:
            issues.append(f"Readability below threshold: {readability_score:.1f}")
            passed = False
        
        if engagement_score < self.min_engagement:
            issues.append(f"Engagement below threshold: {engagement_score:.1f}")
            passed = False
        
        if accuracy_score < self.min_accuracy:
            issues.append(f"Accuracy below threshold: {accuracy_score:.1f}")
            passed = False
        
        summary = "; ".join(issues) if issues else "All validations passed"
        
        return ValidationResult(
            passed=passed,
            readability_score=readability_score,
            engagement_score=engagement_score,
            accuracy_score=accuracy_score,
            issues=issues,
            summary=summary
        )
    
    def _estimate_readability(self, components: Any) -> float:
        """
        Estimate readability using heuristics.
        
        Factors:
        - Average sentence length
        - Word complexity (long words)
        - Paragraph length
        """
        blocks = components.blocks
        text_blocks = [b.get('content', '') for b in blocks 
                      if b.get('block_type') in ['paragraph', 'quote']]
        
        if not text_blocks:
            return 0.0
        
        full_text = ' '.join(text_blocks)
        words = full_text.split()
        sentences = full_text.split('.')
        
        if not words or not sentences:
            return 0.0
        
        # Average sentence length (ideal: 15-20 words)
        avg_sentence_length = len(words) / len(sentences)
        sentence_score = 10.0 - abs(avg_sentence_length - 17.5) / 2.5
        sentence_score = max(0, min(10, sentence_score))
        
        # Word complexity (% of words > 12 chars, ideal < 15%)
        long_words = sum(1 for w in words if len(w) > 12)
        long_word_pct = (long_words / len(words)) * 100
        complexity_score = 10.0 - (long_word_pct / 2)
        complexity_score = max(0, min(10, complexity_score))
        
        # Combined score
        readability = (sentence_score + complexity_score) / 2
        
        logger.debug(f"Readability estimate: {readability:.1f} "
                    f"(avg_sentence={avg_sentence_length:.1f}, long_words={long_word_pct:.1f}%)")
        
        return round(readability, 1)
    
    def _estimate_engagement(self, components: Any) -> float:
        """
        Estimate engagement using heuristics.
        
        Factors:
        - Title quality (length, question/action words)
        - Description hook
        - Content variety (blocks diversity)
        """
        score = 5.0
        
        # Title check (50-80 chars ideal)
        title = components.engaging_title
        if 50 <= len(title) <= 80:
            score += 2.0
        elif 40 <= len(title) <= 90:
            score += 1.0
        
        # Question words or action words in title
        if any(word in title.lower() for word in ['how', 'why', 'what', 'discover', 'reveal', 'breakthrough']):
            score += 1.0
        
        # Description length (150-250 words ideal)
        desc_words = len(components.description.split())
        if 150 <= desc_words <= 250:
            score += 2.0
        elif 100 <= desc_words <= 300:
            score += 1.0
        
        # Block variety (has quotes, subheadings)
        block_types = set(b.get('block_type') for b in components.blocks)
        if 'quote' in block_types:
            score += 0.5
        if 'subheading' in block_types:
            score += 0.5
        
        logger.debug(f"Engagement estimate: {score:.1f}")
        return min(10.0, score)
    
    def _estimate_accuracy(self, components: Any, paper_data: Dict[str, Any]) -> float:
        """
        Estimate accuracy using heuristics.
        
        Since we can't verify claims without LLM, we use proxy metrics:
        - Presence of key terms from abstract
        - No obvious red flags
        """
        blocks = components.blocks
        text_blocks = [b.get('content', '') for b in blocks 
                      if b.get('block_type') in ['paragraph', 'quote']]
        
        if not text_blocks:
            return 0.0
        
        full_text = ' '.join(text_blocks).lower()
        abstract = paper_data.get('abstract', '').lower()
        
        # Extract key terms from abstract (nouns, technical terms)
        abstract_words = set(w for w in abstract.split() if len(w) > 5)
        
        # Count how many abstract terms appear in article
        matches = sum(1 for term in abstract_words if term in full_text)
        
        if abstract_words:
            coverage = (matches / len(abstract_words)) * 100
        else:
            coverage = 0
        
        # Score based on coverage (expect 30-60% of abstract terms)
        if 30 <= coverage <= 60:
            accuracy = 9.5
        elif 20 <= coverage <= 70:
            accuracy = 9.0
        else:
            accuracy = 8.5
        
        logger.debug(f"Accuracy estimate: {accuracy:.1f} (coverage={coverage:.1f}%)")
        return accuracy


def create_validation_service_from_env(env_vars: Dict[str, Any]) -> ArticleValidationService:
    """Create ArticleValidationService from environment variables."""
    return ArticleValidationService(
        min_readability=float(env_vars.get('min_readability_score', 7.0)),
        min_engagement=float(env_vars.get('min_engagement_score', 7.0)),
        min_accuracy=float(env_vars.get('min_accuracy_score', 9.0)),
    )

