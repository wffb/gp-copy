from uuid import UUID

from pydantic import BaseModel, UUID4

class BookmarkCreateRequest(BaseModel):
    article_id: UUID

class BookmarkCreate(BaseModel):
    article_id: UUID
    user_id: UUID4 | None = None

class BookmarkUpdate(BaseModel):
    user_id: UUID | None = None
    article_id: UUID | None = None

class BookmarkResponse(BaseModel):
    id: UUID
    user_id: UUID
    article_id: UUID

    class Config:
        from_attributes = True
