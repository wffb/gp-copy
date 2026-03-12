from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.models import Field


class SaveSearchRequest(BaseModel):
	query_text: str

class RemoveSearchRequest(BaseModel):
	query_text: str