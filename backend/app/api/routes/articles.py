from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, status, Query

from app.services.article_service import ArticleService, get_article_service
from app.services.session_service import get_session_service, SessionService
from app.api.deps.auth import get_current_user_optional, get_current_user
from app.models import User
from app.schemas.common import SuccessResponse
from app.schemas.article import ArticleListDTO
from app.exceptions.exceptions import ArticleWithSlugNotFound, UserDoesNotExist
from app.schemas import ArticleDTO, AddPreferenceRequest, MessageDTO, RemovePreferenceRequest

from app.exceptions.exceptions import ArticleWithSlugNotFound
from app.schemas import ArticleDTO

router = APIRouter()

# List articles with optional filtering and pagination
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List articles with filters and pagination",
    response_model=SuccessResponse[ArticleListDTO],
    response_model_exclude_none=True,
)
def list_articles(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    field: Optional[str] = Query(default=None, description="Filter by field code (e.g., 'physics', 'cs', 'math')"),
    q: str = Query(default=None, description="Search query"),
    sort: Optional[str] = Query(default="date", description="Sort by: date, title"),
    article_service: ArticleService = Depends(get_article_service),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> SuccessResponse[ArticleListDTO]:
    data = article_service.list_articles(page=page, limit=limit, field_code=field, search_query=q, sort=sort, current_user=current_user)
    return SuccessResponse(code=200, data=data)

@router.get(
    "/{slug}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve an article by slug.",
    response_model=SuccessResponse[ArticleDTO],
)
def get_article(slug: str, article_service: ArticleService = Depends(get_article_service), current_user: User = Depends(get_current_user_optional)):
    data = article_service.fetch_article_by_slug(slug)
    if data is None:
        return ArticleWithSlugNotFound("Article with this slug not found.")

    # record article view
    if current_user:
        try:
            article_service.record_read_history(data.id, current_user.id)
        except Exception as e:
            logging.warning(f"Failed to record article view: {e}")

    return SuccessResponse(code=200, data=data)

@router.post(
	"/more-like-this",
	status_code=status.HTTP_200_OK,
	summary="Record that the user wants to see similar articles",
	response_model=SuccessResponse
)
def add_more_like_this(article_preference: AddPreferenceRequest,
						article_service: ArticleService = Depends(get_article_service),
						current_user: User = Depends(get_current_user)
						) -> SuccessResponse[MessageDTO]:
    data = article_service.add_more_like_this(article_preference.article_id, current_user.id)
    return SuccessResponse(code=200, data=data)


@router.delete(
    "/more-like-this",
    status_code=status.HTTP_200_OK,
    summary="Remove article from user preferences",
    response_model=SuccessResponse[MessageDTO],
)
def remove_more_like_this(
        article_preference: RemovePreferenceRequest,
        article_service: ArticleService = Depends(get_article_service),
        current_user: User = Depends(get_current_user),
) -> SuccessResponse[MessageDTO]:
    """
    Remove an article from 'more like this' preferences.
    """
    data = article_service.remove_more_like_this(article_preference.article_id, current_user.id)
    return SuccessResponse(code=200, data=data)
