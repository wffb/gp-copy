from fastapi import APIRouter

from .fields import router as fields_router
from .health import router as health_router
from .users import router as users_router
from .auth import router as auth_router
from .bookmark import router as bookmark_router
from .interests import router as interests_router
from .articles import router as articles_router
from .feedback import router as feedback_router
from .search import router as search_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(fields_router, prefix="/fields", tags=["fields"])
api_router.include_router(interests_router, prefix="/interests", tags=["interests"])
api_router.include_router(articles_router, prefix="/articles", tags=["articles"])
api_router.include_router(bookmark_router, prefix="/bookmarks", tags=["bookmarks"])
api_router.include_router(feedback_router, prefix="/feedbacks", tags=["feedbacks"])
api_router.include_router(search_router, prefix="/search", tags=["search"])

__all__ = ["api_router"]
