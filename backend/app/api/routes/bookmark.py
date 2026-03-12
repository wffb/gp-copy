import string

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from starlette import status

from app.api.deps.auth import get_current_user
from app.exceptions.exceptions import UserDoesNotExist
from app.models import User, article
from app.models.article import Article
from app.schemas import SuccessResponse
from app.schemas.article import ArticleDTO
from app.services.bookmark_service import BookmarkService, get_bookmark_service
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkResponse, BookmarkCreateRequest
import uuid

router = APIRouter()

@router.post("/",
             status_code=status.HTTP_200_OK,
             summary="add bookmarks for current user",
             response_model=SuccessResponse)
def create_bookmark(bookmark: BookmarkCreate,
                    service: BookmarkService = Depends(get_bookmark_service),
                    current_user: User = Depends(get_current_user)
                    ):

    if current_user is None:
        raise UserDoesNotExist("Invalid session")
    if current_user.id is None:
        raise UserDoesNotExist("user_id does not exist")


    bookmark.user_id = current_user.id;

    service.create_bookmark(bookmark)
    return SuccessResponse(code=200, data="created successfully")




@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="get bookmarks of current user",
    response_model=SuccessResponse[list[ArticleDTO]],
)
def get_bookmark(
        current_user: User = Depends(get_current_user),
        service: BookmarkService = Depends(get_bookmark_service)
):

    if current_user is None:
        raise UserDoesNotExist("Invalid session")
    if current_user.id is None:
        raise UserDoesNotExist("user_id does not exist")

    bookmarks = service.get_bookmarks_by_user_id(current_user.id)

    # Map SQLAlchemy Article models to DTOs for response serialization
    items: list[ArticleDTO] = []
    if bookmarks:
        items = [
            ArticleDTO(
                id=a.id,
                title=a.title,
                description=a.description,
                keywords=a.keywords or [],
                slug=a.slug,
                featured_image_url=a.featured_image_url,
                view_count=a.view_count,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in bookmarks
        ]

    return SuccessResponse(code=200, data=items)


@router.delete("/{bookmark_id}",
            status_code=status.HTTP_200_OK,
            summary="delete bookmarks of current user",
            response_model=SuccessResponse)
def delete_bookmark(
        bookmark_id: uuid.UUID,
        service: BookmarkService = Depends(get_bookmark_service),
        current_user: User = Depends(get_current_user)
):

    if current_user is None:
        raise UserDoesNotExist("Invalid session")
    if current_user.id is None:
        raise UserDoesNotExist("user_id does not exist")

    service.delete_bookmark(bookmark_id,current_user.id)
    return  SuccessResponse(code=200,data="deleted successfully")


@router.delete("/by-article/{article_id}",
            status_code=status.HTTP_200_OK,
            summary="delete bookmark by article ID for current user",
            response_model=SuccessResponse)
def delete_bookmark_by_article(
        article_id: uuid.UUID,
        service: BookmarkService = Depends(get_bookmark_service),
        current_user: User = Depends(get_current_user)
):
    if current_user is None:
        raise UserDoesNotExist("Invalid session")
    if current_user.id is None:
        raise UserDoesNotExist("user_id does not exist")

    service.delete_bookmark_by_article_id(article_id, current_user.id)
    return SuccessResponse(code=200, data="deleted successfully")
