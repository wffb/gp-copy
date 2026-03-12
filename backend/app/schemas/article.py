from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

# Block data transfer object for article content blocks
class BlockDTO(BaseModel):
    id: UUID
    block_type: str
    content: Optional[str] = None
    order_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Article data transfer object for API responses
class ArticleDTO(BaseModel):

    id: UUID
    title: str
    description: str
    keywords: Optional[list[str]] = None
    slug: str
    featured_image_url: Optional[str] = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    is_bookmarked: Optional[bool] = False
    # When fetching a single article, include its blocks
    blocks: Optional[list[BlockDTO]] = None

    class Config:
        from_attributes = True

# Response model for paginated article listing.
class ArticleListDTO(BaseModel):
    items: list[ArticleDTO]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

# Request model for user to mark preference for similar articles
class AddPreferenceRequest(BaseModel):
    article_id: UUID

# Request model for user to mark preference for similar articles
class RemovePreferenceRequest(BaseModel):
    article_id: UUID