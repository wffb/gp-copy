"""ArXiv API Service - Fetches papers with rate limiting, retry, and audit tracking."""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from urllib.parse import urlencode
import feedparser
import re
        

from database.repositories.arxiv_ingestion import PipelineRunRepository

logger = logging.getLogger(__name__)


class ArxivAPIError(Exception):
    """Base exception for arXiv API errors."""
    pass


class ArxivAPIService:
    """
    Service for fetching papers from arXiv API.

    Configurable with Airflow variables:
    - ARXIV_RATE_LIMIT_SECONDS: Seconds between requests (default: 3)
    - ARXIV_MAX_RETRIES: Max retry attempts (default: 3)
    - ARXIV_MAX_RESULTS_PER_REQUEST: Max results per request (default: 2000)
    """

    BASE_URL = "http://export.arxiv.org/api/query"
    VALID_SORT_BY = ['relevance', 'lastUpdatedDate', 'submittedDate']
    VALID_SORT_ORDER = ['ascending', 'descending']

    def __init__(
            self,
            rate_limit_seconds: int = 3,
            max_retries: int = 3,
            max_results_per_request: int = 2000
    ):
        """
        Initialize service with configuration parameters.

        Args:
            rate_limit_seconds: Seconds to wait between API calls
            max_retries: Number of retry attempts on failure
            max_results_per_request: Maximum results allowed per request (batch size)
        """
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        self.max_results_per_request = max_results_per_request

        self._last_request_time = 0.0
        self._query_params = {}

    def set_query_params(
            self,
            categories: Optional[List[str]] = None,
            search_query: Optional[str] = None,
            id_list: Optional[List[str]] = None,
            start: int = 0,
            sort_by: str = 'relevance',
            sort_order: str = 'descending',
            date_from: Optional[str] = None,
            date_to: Optional[str] = None
    ) -> None:
        """
        Set query parameters for fetch operations.

        Args:
            categories: arXiv categories (e.g., ['cs.AI', 'cs.LG'])
            search_query: Custom search query (overrides categories)
            id_list: Specific arXiv IDs (overrides search_query)
            start: Starting index for pagination (used by fetch() only)
            sort_by: Sort criterion ('relevance', 'lastUpdatedDate', 'submittedDate')
            sort_order: Sort order ('ascending', 'descending')
            date_from: Start date (YYYYMMDD or YYYYMMDDHHMM)
            date_to: End date (YYYYMMDD or YYYYMMDDHHMM)

        Note:
            Priority: id_list > search_query > categories
            Specify max_results in fetch(max_results) or fetch_all(max_results) calls
        """
        if sort_by not in self.VALID_SORT_BY:
            raise ValueError(f"sort_by must be one of {self.VALID_SORT_BY}")
        if sort_order not in self.VALID_SORT_ORDER:
            raise ValueError(f"sort_order must be one of {self.VALID_SORT_ORDER}")

        self._query_params = {
            'start': start,
            'sort_by': sort_by,
            'sort_order': sort_order
        }

        if id_list:
            self._query_params['id_list'] = id_list
            self._query_params['search_query'] = ''
            return f"id_list[{len(id_list)} IDs]"
        elif search_query:
            self._query_params['search_query'] = search_query
            return search_query
        elif categories:
            query = self._build_category_query(categories, date_from, date_to)
            self._query_params['search_query'] = query
            return query
        else:
            self._query_params['search_query'] = 'all:*'
            return 'all:*'

    def fetch(self, max_results: int = 100, session=None, run_id: Optional[UUID] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch a single page of papers with optional audit tracking.
        
        Returns:
            Tuple of (papers_list, api_returned_count) to handle parsing failures
        """
        if not self._query_params:
            raise ValueError("Query parameters not set. Call set_query_params() first.")

        batch_size = min(max_results, self.max_results_per_request)
        self._enforce_rate_limit()
        url = self._build_url(batch_size)

        logger.info(
            f"Fetching papers: query='{self._query_params.get('search_query', 'id_list')}', "
            f"start={self._query_params['start']}, max={batch_size}"
        )

        try:
            feed = self._request_with_retry(url)
            papers, api_count = self._parse_feed(feed, session=session, run_id=run_id)
            
            if api_count > len(papers):
                logger.warning(f"API returned {api_count} entries, but only {len(papers)} parsed successfully ({api_count - len(papers)} failed)")
            
            if api_count > 0 and len(papers) == 0:
                logger.error(f"CRITICAL: API returned {api_count} entries but ALL parsing failed or were filtered!")
            
            logger.info(f"Successfully fetched {len(papers)} papers from {api_count} API entries")
            return papers, api_count
        except Exception as e:
            self._log_api_failure(session, run_id, str(e))
            raise

    def fetch_all(self, max_results: int = 1000, session=None, run_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Fetch papers with automatic pagination and optional audit tracking."""
        if not self._query_params:
            raise ValueError("Query parameters not set. Call set_query_params() first.")

        all_papers = []
        seen_arxiv_ids = set()
        total_duplicates = 0
        total_parse_failures = 0
        start = self._query_params.get('start', 0)
        batch_size = self.max_results_per_request

        logger.info(f"Starting fetch_all: target={max_results} papers, batch_size={batch_size}")

        while len(all_papers) < max_results:
            remaining = max_results - len(all_papers)
            current_batch = min(batch_size, remaining)
            self._query_params['start'] = start

            logger.info(
                f"Fetching batch: start={start}, size={current_batch}, "
                f"progress={len(all_papers)}/{max_results}"
            )

            papers, api_count = self.fetch(max_results=current_batch, session=session, run_id=run_id)
            
            parse_failures = api_count - len(papers)
            if parse_failures > 0:
                total_parse_failures += parse_failures

            if not papers and api_count == 0:
                logger.info(f"No more papers available. Stopped at {len(all_papers)} papers")
                break

            # Deduplicate papers by arxiv_id
            batch_duplicates = 0
            for paper in papers:
                arxiv_id = paper.get('arxiv_id')
                if arxiv_id and arxiv_id not in seen_arxiv_ids:
                    all_papers.append(paper)
                    seen_arxiv_ids.add(arxiv_id)
                else:
                    batch_duplicates += 1
                    total_duplicates += 1
                    logger.debug(f"Duplicate paper filtered: {arxiv_id}")

            if batch_duplicates > 0:
                logger.warning(f"Skipped {batch_duplicates} duplicate papers in batch")

            start += api_count

            if api_count < current_batch:
                logger.info(
                    f"Received {api_count} entries < {current_batch} requested. "
                    f"Reached end at {len(all_papers)} unique papers"
                )
                break

        summary_parts = [f"retrieved {len(all_papers)} unique papers"]
        if total_duplicates > 0:
            summary_parts.append(f"{total_duplicates} duplicates filtered")
        if total_parse_failures > 0:
            summary_parts.append(f"{total_parse_failures} failed to parse")
        
        logger.info(f"Completed fetch_all: {', '.join(summary_parts)}")
        return all_papers

    def _build_category_query(
            self,
            categories: List[str],
            date_from: Optional[str],
            date_to: Optional[str]
    ) -> str:
        """Build search query from categories and optional date range."""
        cat_parts = [f"cat:{cat.strip()}" for cat in categories if cat and cat.strip()]

        if not cat_parts:
            query = "all:*"
        elif len(cat_parts) == 1:
            query = cat_parts[0]
        else:
            query = f"({' OR '.join(cat_parts)})"

        if date_from or date_to:
            from_date = self._format_date(date_from) if date_from else "190001010000"
            to_date = self._format_date(date_to) if date_to else "209912312359"
            query = f"{query} AND submittedDate:[{from_date} TO {to_date}]"

        return query

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format date to arXiv format (YYYYMMDDHHMM)."""
        date_str = date_str.strip()
        if len(date_str) == 8:
            return date_str + "0000"
        elif len(date_str) == 12:
            return date_str
        else:
            raise ValueError(f"Date must be YYYYMMDD or YYYYMMDDHHMM, got '{date_str}'")

    def _build_url(self, max_results: int) -> str:
        """Build API URL from query parameters."""
        params = {
            'start': self._query_params['start'],
            'max_results': max_results,
            'sortBy': self._query_params['sort_by'],
            'sortOrder': self._query_params['sort_order']
        }

        if 'id_list' in self._query_params:
            params['id_list'] = ','.join(self._query_params['id_list'])
            params['search_query'] = ''
        else:
            params['search_query'] = self._query_params['search_query']

        return f"{self.BASE_URL}?{urlencode(params)}"

    def _enforce_rate_limit(self) -> None:
        """Wait if necessary to enforce rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        self._last_request_time = time.time()

    def _request_with_retry(self, url: str) -> feedparser.FeedParserDict:
        """Make HTTP request with retry logic and exponential backoff."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request attempt {attempt + 1}/{self.max_retries}")
                feed = feedparser.parse(url)

                if feed.bozo and hasattr(feed, 'bozo_exception'):
                    logger.warning(f"Feed parsing warning: {feed.bozo_exception}")

                if hasattr(feed, 'status'):
                    if feed.status == 503:
                        raise ArxivAPIError("arXiv API unavailable (503)")
                    elif feed.status >= 400:
                        raise ArxivAPIError(f"HTTP error {feed.status}")

                if feed.entries and len(feed.entries) == 1:
                    entry = feed.entries[0]
                    if entry.get('title', '').lower() == 'error':
                        error_msg = entry.get('summary', 'Unknown error')
                        raise ArxivAPIError(f"arXiv API error: {error_msg}")

                return feed

            except ArxivAPIError:
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.rate_limit_seconds * (2 ** attempt)
                    logger.warning(f"Request failed: {e}. Retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")

        raise ArxivAPIError(
            f"Failed after {self.max_retries} retries. Last error: {last_exception}"
        ) from last_exception

    def _parse_feed(self, feed: feedparser.FeedParserDict, session=None, run_id: Optional[UUID] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Parse feed and extract paper metadata with optional audit tracking.
        
        Returns:
            Tuple of (papers_list, api_entry_count) where api_entry_count is the number
            of entries the API returned (before parsing failures)
        """
        total_results = int(feed.feed.get('opensearch_totalresults', 0))
        items_returned = int(feed.feed.get('opensearch_itemsperpage', 0))
        api_entry_count = len(feed.entries)

        logger.info(f"API response: {items_returned} papers (total available: {total_results})")

        pipeline_repo = PipelineRunRepository(session) if session and run_id else None

        papers = []
        for entry in feed.entries:
            raw_entry = dict(entry)
            arxiv_id = self._extract_id(entry.get('id', ''))
            
            fetch_record = None
            if pipeline_repo:
                try:
                    fetch_record = pipeline_repo.create_fetch_record(
                        run_id=run_id,
                        arxiv_id=arxiv_id,
                        status="processing",
                        paper_request=self._query_params,
                        paper_response=None
                    )
                except Exception as e:
                    logger.warning(f"Failed to create fetch record for {arxiv_id}: {e}")
            
            try:
                paper = self._parse_entry(entry)
                
                if fetch_record:
                    try:
                        pipeline_repo.update_fetch_status(
                            fetch_record=fetch_record,
                            status="processing",
                            paper_response={
                                'raw': raw_entry,
                                'transformed': paper
                            }
                        )
                        paper['_fetch_record_id'] = fetch_record.id
                    except Exception as e:
                        logger.warning(f"Failed to update fetch record for {arxiv_id}: {e}")
                
                papers.append(paper)
                
            except Exception as e:
                entry_id = entry.get('id', 'unknown')
                logger.error(f"Failed to parse entry {entry_id}: {e}", exc_info=True)
                
                if fetch_record:
                    try:
                        pipeline_repo.update_fetch_status(
                            fetch_record=fetch_record,
                            status="failed",
                            error_message=str(e)[:1000],
                            paper_response={'raw': raw_entry}
                        )
                    except Exception as e2:
                        logger.warning(f"Failed to update fetch record for {entry_id}: {e2}")
                
                continue

        return papers, api_entry_count

    def _parse_entry(self, entry: feedparser.FeedParserDict) -> Dict[str, Any]:
        """Parse single entry and extract all metadata."""
        arxiv_id = self._extract_id(entry.get('id', ''))

        title = entry.get('title', '').strip()
        title = ' '.join(title.split())

        abstract = entry.get('summary', '').strip()
        abstract = ' '.join(abstract.split())

        authors = [
            {
                'name': author.get('name', '').strip(),
                **({'affiliation': author['arxiv_affiliation'].strip()}
                   if author.get('arxiv_affiliation') else {})
            }
            for author in entry.get('authors', [])
            if author.get('name', '').strip()
        ]

        categories = [
            tag.get('term', '')
            for tag in entry.get('tags', [])
            if 'arxiv.org' in tag.get('scheme', '') 
            and tag.get('term') 
            and self._is_valid_arxiv_category(tag.get('term', ''))
        ]

        primary_category = None
        if hasattr(entry, 'arxiv_primary_category'):
            candidate = entry.arxiv_primary_category.get('term')
            if candidate and self._is_valid_arxiv_category(candidate):
                primary_category = candidate
        
        if not primary_category and categories:
            primary_category = categories[0]

        pdf_url = None
        doi_url = None
        for link in entry.get('links', []):
            if link.get('type') == 'application/pdf':
                pdf_url = link.get('href')
            elif link.get('title') == 'doi' or 'doi' in link.get('href', ''):
                doi_url = link.get('href')

        doi = getattr(entry, 'arxiv_doi', None)
        if not doi and doi_url and 'doi.org/' in doi_url:
            doi = doi_url.split('doi.org/')[-1]

        return {
            'arxiv_id': arxiv_id,
            'title': title,
            'abstract': abstract,
            'published_date': entry.get('published'),
            'updated_date': entry.get('updated'),
            'authors': authors,
            'categories': categories,
            'primary_category': primary_category,
            'pdf_url': pdf_url,
            'abstract_url': entry.get('id'),
            'doi': doi,
            'doi_url': doi_url,
            'comment': getattr(entry, 'arxiv_comment', None),
            'journal_ref': getattr(entry, 'arxiv_journal_ref', None)
        }

    def _log_api_failure(self, session, run_id: Optional[UUID], error_message: str) -> None:
        """Create a failure record when the entire API request fails."""
        if not session or not run_id:
            return
        
        try:
            pipeline_repo = PipelineRunRepository(session)
            pipeline_repo.create_fetch_record(
                run_id=run_id,
                arxiv_id=f"API_FAILURE_{self._query_params.get('start', 0)}",
                status="failed",
                paper_request=self._query_params,
                error_message=f"API request failed: {error_message[:900]}"
            )
            session.flush()
            logger.info(f"Logged API-level failure for run {run_id}")
        except Exception as e:
            logger.error(f"Failed to log API failure: {e}")

    @staticmethod
    def _is_valid_arxiv_category(category: str) -> bool:
        """
        Validate if a category string is a valid arXiv category.
        
        Valid arXiv categories:
        - Start with lowercase letters or 'q-'
        - May contain hyphens
        - Optionally have a dot followed by uppercase letters
        - Examples: cs.AI, astro-ph, q-bio.NC, math.AG
        
        Invalid (ACM classification codes):
        - Contain semicolons: "I.2.7; I.2.6"
        - Uppercase letter + dots + digits: "I.2.7", "G.2.2"
        """
        if not category or ';' in category:
            return False
        
        # arXiv category pattern: starts with lowercase/hyphen, optional dot + uppercase
        arxiv_pattern = re.compile(r'^[a-z][a-z\-]*(\.[A-Z]{2,})?$')
        
        is_valid = bool(arxiv_pattern.match(category))
        if not is_valid:
            logger.debug(f"Skipping non-arXiv classification code: {category}")
        
        return is_valid
    
    @staticmethod
    def _extract_id(id_url: str) -> str:
        """Extract arXiv ID from URL."""
        return id_url.split('/abs/')[-1] if '/abs/' in id_url else id_url

