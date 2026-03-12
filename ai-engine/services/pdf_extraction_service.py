"""
PDF Extraction Service
======================
Full PDF text and figure metadata extraction for DocETL processing.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import fitz
import requests

logger = logging.getLogger(__name__)


@dataclass
class FigureMetadata:
    """Figure/image metadata extracted from PDF."""
    figure_number: int
    page_number: int
    bbox: tuple
    caption: Optional[str] = None


@dataclass
class PDFContent:
    """Complete PDF extraction results."""
    full_text: str
    page_count: int
    figures: List[FigureMetadata]
    metadata: Dict[str, Any]


class PDFExtractionService:
    """
    Service for extracting full text and figure metadata from research paper PDFs.
    
    Provides comprehensive extraction for DocETL article generation, including:
    - Full text extraction from all pages
    - Figure/table detection and metadata
    - PDF metadata (page count, file size, etc.)
    """
    
    def __init__(self, max_pdf_size_mb: int = 25, download_timeout: int = 60):
        self.max_pdf_size_mb = max_pdf_size_mb
        self.download_timeout = download_timeout
    
    def extract_from_url(self, pdf_url: str, arxiv_id: str) -> PDFContent:
        """
        Download PDF from URL and extract full content.
        
        Args:
            pdf_url: URL to PDF file
            arxiv_id: arXiv identifier for logging
            
        Returns:
            PDFContent with full text and metadata
            
        Raises:
            requests.RequestException: If PDF download fails
            Exception: If PDF processing fails
        """
        pdf_path = None
        doc = None
        
        try:
            logger.info(f"Downloading PDF for {arxiv_id} from {pdf_url}")
            pdf_path = self._download_pdf(pdf_url, arxiv_id)
            
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_pdf_size_mb:
                raise ValueError(f"PDF too large: {file_size_mb:.1f}MB (max: {self.max_pdf_size_mb}MB)")
            
            logger.info(f"Extracting content from PDF for {arxiv_id}")
            doc = fitz.open(pdf_path)
            
            full_text = self._extract_full_text(doc)
            figures = self._extract_figure_metadata(doc)
            
            content = PDFContent(
                full_text=full_text,
                page_count=len(doc),
                figures=figures,
                metadata={
                    'file_size_mb': round(file_size_mb, 2),
                    'page_count': len(doc),
                    'figure_count': len(figures),
                    'word_count': len(full_text.split()),
                    'char_count': len(full_text),
                }
            )
            
            logger.info(f"Extracted {content.metadata['word_count']} words and {len(figures)} figures from {arxiv_id}")
            return content
            
        finally:
            if doc:
                doc.close()
            if pdf_path:
                pdf_path.unlink(missing_ok=True)
    
    def _download_pdf(self, pdf_url: str, arxiv_id: str) -> Path:
        """Download PDF to temporary file."""
        response = requests.get(
            pdf_url,
            timeout=self.download_timeout,
            stream=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.pdf',
            prefix=f'arxiv_{arxiv_id.replace("/", "_")}_'
        )
        temp_path = Path(temp_file.name)
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_path
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing NUL bytes and other problematic characters.

        PostgreSQL cannot store NUL (0x00) characters in string fields,
        so we must remove them from extracted PDF text.
        """
        if not text:
            return text

        # Remove NUL bytes
        text = text.replace('\x00', '')

        # Remove other control characters except common whitespace (tab, newline, carriage return)
        text = ''.join(
            char for char in text
            if char >= ' ' or char in '\t\n\r'
        )

        return text

    def _extract_full_text(self, doc: fitz.Document) -> str:
        """Extract text from all pages."""
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            if text.strip():
                # Sanitize text to remove NUL bytes
                sanitized_text = self._sanitize_text(text)
                text_parts.append(f"--- Page {page_num + 1} ---\n{sanitized_text}")

        return "\n\n".join(text_parts)
    
    def _extract_figure_metadata(self, doc: fitz.Document) -> List[FigureMetadata]:
        """
        Extract figure/image metadata from PDF.
        
        Note: This extracts image positions and references, not the actual images.
        For article generation, we just need to know figures exist and their locations.
        """
        figures = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract images
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    bbox = page.get_image_bbox(xref)
                    
                    figures.append(FigureMetadata(
                        figure_number=len(figures) + 1,
                        page_number=page_num + 1,
                        bbox=(bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                        caption=None
                    ))
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
            
            # Try to find figure captions in text
            text = page.get_text("text")
            caption_patterns = [
                r'Figure\s+(\d+)[:\.]?\s*(.+)',
                r'Fig\.\s+(\d+)[:\.]?\s*(.+)',
                r'Table\s+(\d+)[:\.]?\s*(.+)',
            ]

            import re
            for pattern in caption_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    fig_num = int(match.group(1))
                    caption_text = self._sanitize_text(match.group(2).strip()[:200])

                    # Try to match with extracted figures
                    for fig in figures:
                        if fig.page_number == page_num + 1 and not fig.caption:
                            fig.caption = caption_text
                            break
        
        return figures
    
    def extract_text_chunks(self, full_text: str, chunk_size: int = 2000, overlap: int = 200) -> Dict[str, Any]:
        """
        Split full text into overlapping chunks for LLM processing.
        
        Args:
            full_text: Complete extracted text
            chunk_size: Target characters per chunk
            overlap: Overlap between consecutive chunks
            
        Returns:
            Dict with chunks and metadata
        """
        if not full_text or len(full_text) < chunk_size:
            return {
                'chunks': [full_text] if full_text else [],
                'chunk_count': 1 if full_text else 0,
                'total_chars': len(full_text) if full_text else 0,
            }
        
        chunks = []
        start = 0
        
        while start < len(full_text):
            end = start + chunk_size
            
            if end < len(full_text):
                # Try to break at sentence boundary
                last_period = full_text.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunks.append(full_text[start:end].strip())
            start = end - overlap
        
        return {
            'chunks': chunks,
            'chunk_count': len(chunks),
            'total_chars': len(full_text),
            'avg_chunk_size': len(full_text) // len(chunks) if chunks else 0,
        }


def create_extraction_service_from_env(env_vars: Dict[str, Any]) -> PDFExtractionService:
    """Create PDFExtractionService from environment variables."""
    return PDFExtractionService(
        max_pdf_size_mb=int(env_vars.get('max_pdf_size_mb', 25)),
        download_timeout=int(env_vars.get('pdf_download_timeout', 60)),
    )

