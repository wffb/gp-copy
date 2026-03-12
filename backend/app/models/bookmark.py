from __future__ import annotations

import uuid
from sqlalchemy import String, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, UUID as SQLUUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db.base import Base

class Bookmark(Base):
    __tablename__ = "bookmark"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    article_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_article"),
        Index('ix_user_id_article_id', 'user_id', 'article_id'),
    )
