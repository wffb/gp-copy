from __future__ import annotations

from fastapi import APIRouter, Depends, status, Query
from typing import Optional

from app.schemas.common import SuccessResponse
from app.schemas.article import ArticleListDTO
from app.schemas import MessageDTO
from app.schemas.search import SaveSearchRequest, RemoveSearchRequest
from app.api.deps.auth import get_current_user
from app.models import User
from app.services.search_service import SearchService, get_search_service
from app.exceptions.exceptions import UserDoesNotExist
from app.api.deps.auth import get_current_user_optional

router = APIRouter()


@router.post(
    "/save",
    status_code=status.HTTP_200_OK,
    summary="Save a search query",
    response_model=SuccessResponse[MessageDTO],
)
def save_search(
        request: SaveSearchRequest,
        search_service: SearchService = Depends(get_search_service),
        current_user: User = Depends(get_current_user),
) -> SuccessResponse[MessageDTO]:
    """Save a search query for future notifications and personalization"""
    data = search_service.save_search(current_user.id, request.query_text)
    return SuccessResponse(code=200, data=data)

@router.delete(
    "/remove",
    status_code=status.HTTP_200_OK,
    summary="Remove a search query",
    response_model=SuccessResponse[MessageDTO],
)
def remove_search(
        request: RemoveSearchRequest,
        search_service: SearchService = Depends(get_search_service),
        current_user: User = Depends(get_current_user),
) -> SuccessResponse[MessageDTO]:
    """
    Remove an article from 'more like this' preferences.
    """
    data = search_service.remove_search(current_user.id, request.query_text)
    return SuccessResponse(code=200, data=data)

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Search articles with personalization",
    response_model=SuccessResponse[ArticleListDTO]
)
def search_articles(
        page: int = Query(default=1, ge=1, description="Page number"),
        limit: int = Query(default=250, ge=1, le=250, description="Items per page"),
        field: Optional[str] = Query(default=None, description="Filter by field code"),
        q: Optional[str] = Query(default=None, description="Search query"),
        dynamic: bool = Query(default=False, description="Dynamic search mode (while typing)"),
        search_service: SearchService = Depends(get_search_service),
        current_user: Optional[User] = Depends(get_current_user_optional),
) -> SuccessResponse[ArticleListDTO]:
    """
    Search articles with personalized ranking.

    - For logged-in users: Returns personalized results
    - For guests: Returns basic keyword-matched results
    - Use dynamic=true for live search (8 results max)
    """
    data = search_service.search_articles(
        page=page,
        limit=limit,
        search_query=q,
        current_user=current_user,
        field_code=field,
        is_dynamic=dynamic
    )
    return SuccessResponse(code=200, data=data)