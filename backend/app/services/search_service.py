import logging
import math
from typing import Optional
from uuid import UUID

from fastapi.params import Depends

from app.repositories.bookmark_repository import BookmarkRepository, get_bookmark_repository
from app.repositories.search_repository import SearchRepository, get_search_repository
from app.models.user import User
from app.models.article import Article
from app.schemas import ArticleDTO, ArticleListDTO
from app.services.scoring_service import ScoringService, get_scoring_service


class SearchService:
    """
        Handles article search with personalized ranking.

        Search Behavior:
        - Dynamic search (is_dynamic=True): Max 8 results, no random injection
        - Full search (is_dynamic=False): Up to 250 results, random injection enabled
        - Guests: Basic keyword search without personalization
        - Logged-in: Uses pre-calculated scores from ArticleScore table
        """

    DYNAMIC_SEARCH_LIMIT = 8
    MAX_SEARCH_LIMIT = 250

    def __init__(self, search_repo: SearchRepository, bookmark_repo: BookmarkRepository, scoring_service: ScoringService):
        self._search_repo = search_repo
        self._bookmark_repo = bookmark_repo
        self._scoring_service = scoring_service

    def search_articles(
            self,
            page: int = 1,
            limit: int = 20,
            search_query: Optional[str] = None,
            current_user: Optional[User] = None,
            field_code: Optional[str] = None,
            is_dynamic: bool = False,
    ) -> ArticleListDTO:
        """
        Search articles with personalized ranking.

        Args:
            page: Page number (1-indexed)
            limit: Items per page
            search_query: Search query string
            current_user: Authenticated user (None for guests)
            field_code: Filter by field code
            is_dynamic: True for auto complete (typing), False for submitted search
        """
        # Enforce limits
        if is_dynamic:
            limit = min(limit, self.DYNAMIC_SEARCH_LIMIT)
        else:
            limit = min(limit, self.MAX_SEARCH_LIMIT)

        # Route to appropriate search strategy
        if current_user:
            return self.personalized_search(page, limit, search_query, current_user, field_code, is_dynamic)
        else:
            return self.basic_search(page, limit, search_query, field_code)

    def personalized_search(
            self,
            page: int,
            limit: int,
            search_query: Optional[str],
            current_user: User,
            field_code: Optional[str],
            is_dynamic: bool
    ) -> ArticleListDTO:
        """
        Personalized search with scoring

        Args:
            page: Page number (1-indexed)
            limit: Items per page
            search_query: Search query string
            current_user: Authenticated user (None for guests)
            field_code: Filter by field code
            is_dynamic: True for auto complete (typing), False for submitted search
        """
        logging.info("Personalized search")
        # Record non-dynamic searches
        if not is_dynamic and search_query:
            try:
                logging.info("saving search: %s", search_query)
                self._search_repo.record_search(
                    user_id=current_user.id,
                    query_text=search_query.strip().lower(),
                    is_saved=False
                )
            except Exception as e:
                logging.warning(f"Failed to record search: {e}")

        # Fetch matching articles
        articles, total = self._search_repo.list_articles(
            offset=0,
            limit= min(limit * 10, self.MAX_SEARCH_LIMIT) if not is_dynamic else limit,
            search_query=search_query,
            field_code=field_code,
            status="published"
        )

        if not articles:
            return self._empty_result(page, limit)

        # Get pre-calculated scores for these articles and filter to match search criteria
        article_scores = self._search_repo.get_article_scores_by_user(current_user.id)
        article_ids_set = {a.id for a in articles}
        relevant_scores = [
            score for score in article_scores
            if score.article_id in article_ids_set
        ]

        # If no pre-calculated scores exist, fall back to basic search
        if not relevant_scores:
            logging.warning(f"No pre-calculated scores found for user {current_user.id}.Falling back to basic search.")
            return self.basic_search(page, limit, search_query, field_code, current_user)

        # Rank articles by scores
        ranked_ids = self._scoring_service.rank_articles_by_scores(
            article_scores=relevant_scores,
            inject_random=not is_dynamic,
            all_articles=articles
        )

        # Build article lookup
        article_map = {a.id: a for a in articles}
        ranked_articles = [article_map[aid] for aid in ranked_ids if aid in article_map]
        if is_dynamic:
            ranked_articles = ranked_articles[:self.DYNAMIC_SEARCH_LIMIT]

        # Apply pagination
        offset = (page - 1) * limit
        paginated = ranked_articles[offset:offset + limit]

        # Convert to DTOs
        items = [self._to_dto(article, current_user) for article in paginated]

        # Calculate pagination metadata
        total_ranked = len(ranked_articles)
        total_pages = math.ceil(total_ranked / limit) if total_ranked > 0 else 0

        return ArticleListDTO(
            items=items,
            total=total_ranked,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

    def basic_search(
            self,
            page: int,
            limit: int,
            search_query: Optional[str],
            field_code: Optional[str],
            current_user: Optional[User] = None
    ) -> ArticleListDTO:
        """
        Basic search without personalization (for guests or fallback).
        Simply returns articles matching filters, sorted by date.
        """
        logging.info("Basic search")
        offset = (page - 1) * limit

        articles, total = self._search_repo.list_articles(
            offset=offset,
            limit=limit,
            search_query=search_query,
            field_code=field_code,
            status="published"
        )

        items = [self._to_dto(article, current_user) for article in articles]
        total_pages = math.ceil(total / limit) if total > 0 else 0

        return ArticleListDTO(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

    def save_search(self, user_id: UUID, query_text: str) -> dict:
        """
        Save a search query for future notifications and personalization.
        """
        query_text = query_text.strip().lower()
        self._search_repo.record_search(
            user_id=user_id,
            query_text=query_text,
            is_saved=True
        )
        return {"message": f"Successfully saved search query '{query_text}' for user {user_id}"}

    def remove_search(self, user_id: UUID, query_text: str) -> dict:
        """
        Remove a saved search query.
        """
        query_text = query_text.strip().lower()
        self._search_repo.remove_search(user_id=user_id, query_text=query_text)

        return {"message": f"Successfully removed search query '{query_text}' for user {user_id}"}

    def _to_dto(
            self,
            article: Article,
            current_user: Optional[User] = None
    ) -> ArticleDTO:
        """Convert Article model to DTO with bookmark status."""
        is_bookmarked = False
        if current_user:
            bookmark = self._bookmark_repo.get_by_user_id_and_article_id(current_user.id, article.id)
            is_bookmarked = bookmark is not None

        return ArticleDTO(
            id=article.id,
            title=article.title,
            description=article.description,
            keywords=article.keywords or [],
            slug=article.slug,
            featured_image_url=article.featured_image_url,
            view_count=article.view_count,
            created_at=article.created_at,
            updated_at=article.updated_at,
            is_bookmarked=is_bookmarked,
            blocks=None,
        )

    def _empty_result(self, page: int, limit: int) -> ArticleListDTO:
        """Return empty result set."""
        return ArticleListDTO(
            items=[],
            total=0,
            page=page,
            limit=limit,
            total_pages=0,
            has_next=False,
            has_prev=False
        )

def get_search_service(
		search_repo: SearchRepository = Depends(get_search_repository),
        bookmark_repo: BookmarkRepository = Depends(get_bookmark_repository),
        scoring_service: ScoringService = Depends(get_scoring_service)
) -> SearchService:
    return SearchService(search_repo, bookmark_repo, scoring_service)