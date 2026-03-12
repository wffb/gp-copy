import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, UUID, UniqueConstraint, TIMESTAMP
from app.db.base import Base
from sqlalchemy.sql.sqltypes import Text, DateTime, Boolean, Float, Integer


class UserSearchHistory(Base):
    """Track user search queries and saved queries for personalization"""
    __tablename__ = "user_search_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    is_saved = Column(Boolean, nullable=False, default=False)
    last_searched_at = Column(DateTime, nullable=False, default=datetime.utcnow())
    search_count = Column(Integer, nullable=False, default=1)
    saved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "query", name="uq_user_search_history"),
    )

class UserReadHistory(Base):
    """Track user article read history for personalization"""
    __tablename__ = "user_read_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    first_read_at = Column(DateTime, nullable=False, default=datetime.utcnow())
    last_read_at = Column(DateTime, nullable=False, default=datetime.utcnow())

    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_read_history"),
    )

class UserMoreLikeThis(Base):
    """Track articles users marked as 'more like this"""
    __tablename__ = "user_more_like_this"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow())

    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_more_like_this"),
    )

class ArticleScore(Base):
    """Pre-calculated article scores for users"""
    __tablename__ = "article_score"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    final_score = Column(Float, nullable=False, default=0.0)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow())

    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_article_score"),
    )