from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class FeedbackCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    message: str


class FeedbackCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    message: str


class FeedbackResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True