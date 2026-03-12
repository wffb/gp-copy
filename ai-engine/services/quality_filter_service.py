"""
Quality Filter Service
======================
Early quality filtering for arXiv papers to skip bad PDFs.
"""

import logging
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

import fitz
import requests
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


@dataclass
class QualityConfig:
    """Quality filter configuration parameters."""
    pdf_min_pages: int = 4
    pdf_max_pages: int = 50
    pdf_min_size_kb: int = 100
    pdf_max_size_mb: int = 25
    text_min_chars: int = 1000
    language: str = "en"
    abstract_min_words: int = 100
    abstract_max_words: int = 500
    priority_categories: List[str] = None
    exclude_categories: List[str] = None
    recency_years: int = 5
    min_sections: int = 3
    min_figures: int = 1
    max_figures: int = 10
    enable_pdf_download: bool = True

    def __post_init__(self):
        if self.priority_categories is None:
            self.priority_categories = ["astro-ph", "physics", "cs.AI", "cs.LG", "q-bio"]
        if self.exclude_categories is None:
            self.exclude_categories = ["cs.CR"]


class QualityFilterService:
    """
    Service for quality filtering of arXiv papers.
    
    Runs multiple quality checks (metadata, PDF structure, content) to determine
    if papers should be processed or rejected early.
    """
    
    SECTION_PATTERN = re.compile(
        r'\b('
        # Opening sections
        r'Abstract|Introduction|Motivation|Background|Overview|'
        r'Problem Statement|Contribution|'
        # Literature & context
        r'Related Work|Literature Review|State of the Art|Prior Work|'
        r'Survey|Taxonomy|'
        # Theoretical foundations
        r'Preliminaries|Definitions?|Notation|Theorems?|Proofs?|Lemmas?|Corollaries?|'
        r'Theoretical Framework|'
        # Methodology & approach
        r'Methods?|Methodology|Approach|Design|Architecture|'
        r'System (Overview|Design|Architecture)?|Framework|'
        r'Materials( and Methods)?|'
        # Data & collection
        r'Data(set)?( Collection| Description| Analysis)?|'
        r'Annotation|Statistics|Validation|'
        # Implementation & experiments
        r'Implementation|Experiments?|Evaluation|'
        r'Results?|Findings?|Analysis|'
        r'Performance|Benchmarks?|'
        r'(Experimental|Empirical) (Setup|Results|Analysis)|'
        r'Preliminary Results|'
        # Applications & case studies
        r'Applications?|Case Stud(y|ies)|Use Cases?|'
        # Discussion & interpretation
        r'Discussion|Interpretation|Implications?|'
        # Challenges & limitations
        r'Challenges?|Limitations?|Threats to Validity|'
        # Conclusion & future work
        r'Conclusion|Summary|'
        r'Future (Work|Directions?|Research)|'
        r'Recommendations?|'
        # Supporting sections
        r'Acknowledgments?|References?|Bibliography|'
        r'Append(ix|ices)|Supplementary Materials?'
        r')\b',
        re.IGNORECASE
    )
    FIGURE_PATTERN = re.compile(r'\b(?:Figure|Fig\.?|Table)\s+(\d+)', re.IGNORECASE)
    
    def __init__(self, config: QualityConfig):
        self.config = config
    
    def filter_paper(self, paper_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Run all quality checks on a paper.
        
        Returns:
            Tuple of (status, message) where status is 'ready_to_process' or 'rejected'
        """
        arxiv_id = paper_data.get('arxiv_id', 'unknown')
        logger.info(f"Filtering paper: {arxiv_id}")
        
        try:
            checks = [
                ('metadata', self._check_metadata),
                ('abstract', self._check_abstract),
            ]
            
            if self.config.enable_pdf_download:
                checks.append(('pdf', self._check_pdf))
            else:
                logger.debug(f"PDF download disabled, skipping PDF checks for {arxiv_id}")
            
            for check_name, check_func in checks:
                status, message = check_func(paper_data)
                if status == 'rejected':
                    logger.info(f"Paper {arxiv_id} rejected at {check_name} check: {message}")
                    return status, message
            
            logger.info(f"Paper {arxiv_id} passed all quality checks")
            return 'ready_to_process', None
            
        except Exception as e:
            error_msg = f"Quality check error: {str(e)[:200]}"
            logger.error(f"Failed to filter {arxiv_id}: {error_msg}", exc_info=True)
            return 'rejected', error_msg
    
    def _check_metadata(self, paper_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Check metadata-based quality filters."""
        
        # Check recency
        published_date = paper_data.get('published_date')
        if published_date:
            try:
                pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.recency_years * 365)
                
                if pub_date < cutoff_date:
                    return 'rejected', f"Paper too old: published {pub_date.year}, cutoff {cutoff_date.year}"
            except Exception as e:
                logger.warning(f"Could not parse published_date: {e}")
        
        # Check categories
        primary_category = paper_data.get('primary_category', '')
        categories = paper_data.get('categories', [])
        all_categories = [primary_category] + categories
        
        # Check excluded categories
        for cat in all_categories:
            if any(cat.startswith(exc) for exc in self.config.exclude_categories):
                return 'rejected', f"Excluded category: {cat}"
        
        # Check if paper has withdrawn status (if available)
        if paper_data.get('withdrawn', False):
            return 'rejected', "Paper withdrawn by authors"
        
        return 'ready_to_process', None
    
    def _check_abstract(self, paper_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Check abstract presence and quality."""
        abstract = paper_data.get('abstract', '')
        
        if not abstract or len(abstract.strip()) == 0:
            return 'rejected', "Missing abstract"
        
        word_count = len(abstract.split())
        
        if word_count < self.config.abstract_min_words:
            return 'rejected', f"Abstract too short: {word_count} words (min: {self.config.abstract_min_words})"
        
        if word_count > self.config.abstract_max_words:
            return 'rejected', f"Abstract too long: {word_count} words (max: {self.config.abstract_max_words})"
        
        # Check language
        try:
            detected_lang = detect(abstract)
            if detected_lang != self.config.language:
                return 'rejected', f"Wrong language: detected {detected_lang}, expected {self.config.language}"
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
        
        return 'ready_to_process', None
    
    def _check_pdf(self, paper_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Check PDF structure and content quality."""
        pdf_url = paper_data.get('pdf_url')
        if not pdf_url:
            return 'rejected', "Missing PDF URL"
        
        arxiv_id = paper_data.get('arxiv_id', 'unknown')
        pdf_path = None
        doc = None
        
        try:
            pdf_path = self._download_pdf(pdf_url, arxiv_id)
            
            status, message = self._check_file_size(pdf_path)
            if status == 'rejected':
                return status, message
            
            doc = fitz.open(pdf_path)
            
            status, message = self._check_page_count(doc)
            if status == 'rejected':
                return status, message
            
            extracted_text = self._extract_text(doc)
            
            status, message = self._check_text_content(extracted_text)
            if status == 'rejected':
                return status, message
            
            status, message = self._check_structure(extracted_text)
            if status == 'rejected':
                return status, message
            
            logger.debug(f"PDF checks passed for {arxiv_id}")
            return 'ready_to_process', None
            
        except requests.RequestException as e:
            return 'rejected', f"PDF download failed: {str(e)[:100]}"
        except Exception as e:
            return 'rejected', f"PDF processing error: {str(e)[:100]}"
        finally:
            if doc:
                doc.close()
            if pdf_path:
                pdf_path.unlink(missing_ok=True)
    
    def _check_file_size(self, pdf_path: Path) -> Tuple[str, Optional[str]]:
        """Check PDF file size."""
        file_size_kb = pdf_path.stat().st_size / 1024
        file_size_mb = file_size_kb / 1024
        
        if file_size_kb < self.config.pdf_min_size_kb:
            return 'rejected', f"PDF too small: {file_size_kb:.1f}KB (min: {self.config.pdf_min_size_kb}KB)"
        
        if file_size_mb > self.config.pdf_max_size_mb:
            return 'rejected', f"PDF too large: {file_size_mb:.1f}MB (max: {self.config.pdf_max_size_mb}MB)"
        
        return 'ready_to_process', None
    
    def _check_page_count(self, doc: fitz.Document) -> Tuple[str, Optional[str]]:
        """Check PDF page count."""
        page_count = len(doc)
        
        if page_count < self.config.pdf_min_pages:
            return 'rejected', f"Too few pages: {page_count} (min: {self.config.pdf_min_pages})"
        
        if page_count > self.config.pdf_max_pages:
            return 'rejected', f"Too many pages: {page_count} (max: {self.config.pdf_max_pages})"
        
        return 'ready_to_process', None
    
    def _check_text_content(self, text: str) -> Tuple[str, Optional[str]]:
        """Check extracted text content."""
        if len(text) < self.config.text_min_chars:
            return 'rejected', f"Insufficient text: {len(text)} chars (min: {self.config.text_min_chars})"
        
        return 'ready_to_process', None
    
    def _check_structure(self, text: str) -> Tuple[str, Optional[str]]:
        """Check document structure (sections, figures)."""
        section_count = len(self.SECTION_PATTERN.findall(text))
        if section_count < self.config.min_sections:
            return 'rejected', f"Too few sections: {section_count} (min: {self.config.min_sections})"
        
        # Extract unique figure/table numbers (regex captures only the number)
        figure_numbers = self.FIGURE_PATTERN.findall(text)
        figure_count = len(set(figure_numbers))
        
        if figure_count < self.config.min_figures:
            return 'rejected', f"Too few figures: {figure_count} unique (min: {self.config.min_figures})"
        
        if figure_count > self.config.max_figures:
            return 'rejected', f"Too many figures: {figure_count} unique (max: {self.config.max_figures}), possibly slides"
        
        return 'ready_to_process', None
    
    def _download_pdf(self, pdf_url: str, arxiv_id: str) -> Path:
        """Download PDF to temporary file."""
        response = requests.get(pdf_url, timeout=30, stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix=f'arxiv_{arxiv_id}_')
        temp_path = Path(temp_file.name)
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_path
    
    def _extract_text(self, doc: fitz.Document) -> str:
        """Extract text from PDF using PyMuPDF."""
        text_parts = []
        
        if len(doc) > 3:
            pages_to_check = [0, 1, 2, len(doc) - 1]
        else:
            pages_to_check = list(range(len(doc)))
        
        for page_num in pages_to_check:
            page = doc[page_num]
            text_parts.append(page.get_text())
        
        return ' '.join(text_parts)


def create_quality_config_from_env(env_vars: Dict[str, Any]) -> QualityConfig:
    """Create QualityConfig from environment variables."""
    return QualityConfig(
        pdf_min_pages=int(env_vars.get('QF_PDF_MIN_PAGES', 4)),
        pdf_max_pages=int(env_vars.get('QF_PDF_MAX_PAGES', 50)),
        pdf_min_size_kb=int(env_vars.get('QF_PDF_MIN_SIZE_KB', 100)),
        pdf_max_size_mb=int(env_vars.get('QF_PDF_MAX_SIZE_MB', 25)),
        text_min_chars=int(env_vars.get('QF_TEXT_MIN_CHARS', 1000)),
        language=env_vars.get('QF_LANGUAGE', 'en'),
        abstract_min_words=int(env_vars.get('QF_ABSTRACT_MIN_WORDS', 100)),
        abstract_max_words=int(env_vars.get('QF_ABSTRACT_MAX_WORDS', 500)),
        priority_categories=[c.strip() for c in env_vars.get('QF_PRIORITY_CATEGORIES', '').split(',') if c.strip()] or None,
        exclude_categories=[c.strip() for c in env_vars.get('QF_EXCLUDE_CATEGORIES', 'cs.CR').split(',') if c.strip()],
        recency_years=int(env_vars.get('QF_RECENCY_YEARS', 5)),
        min_sections=int(env_vars.get('QF_MIN_SECTIONS', 3)),
        min_figures=int(env_vars.get('QF_MIN_FIGURES', 0)),
        max_figures=int(env_vars.get('QF_MAX_FIGURES', 10)),
        enable_pdf_download=env_vars.get('QF_ENABLE_PDF_DOWNLOAD', 'true').lower() == 'true',
    )

