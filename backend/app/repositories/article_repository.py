import uuid
import re
from datetime import datetime
from typing import List, Tuple, Optional

from fastapi import Depends
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.exceptions.exceptions import InvalidFieldError, APIError
from app.models.article import Article
from app.models.field import Field
from app.models.paper import Paper
from app.models.search import UserMoreLikeThis, UserReadHistory

class ArticleRepository:
	def __init__(self, db: Session):
		self._db = db

	def get_article_by_slug(self, slug: str):
		return (
			self._db
				.query(Article)
				.filter(Article.slug == slug)
				.first()
		)

	def list_articles(
			self,
			offset: int = 0,
			limit: int = 20,
			field_code: Optional[str] = None,
			search_query: Optional[str] = None,
			sort: str = "date",
			status: str = "published"
	) -> Tuple[List[Article], int]:
		"""
		List articles with filters and pagination.
		"""
		query = (
			self._db.query(Article)
			.join(Article.paper)
		)

		filters = [Article.status == status]

		# Field filter by code
		if field_code:
			# Look up the field by code (case-insensitive)
			field = (
				self._db.query(Field)
				.filter(Field.code.ilike(field_code))
				.one_or_none()
			)

			if not field:
				raise InvalidFieldError(f"Field with code '{field_code}' does not exist")

			# Filter papers by this field's code or name
			filters.append(
				or_(
					Paper.primary_field_id == field.id,
					Paper.primary_subfield_id == field.id,
				)
			)

		if search_query:
			search_term = f"%{search_query}%"
			filters.append(
				or_(
					Article.title.ilike(search_term),
					Article.description.ilike(search_term),
					Article.keywords.overlap([search_query.lower()])
				)
			)

		query = query.filter(and_(*filters))

		# Count total matching records
		total = query.count()

		# Apply sorting
		if sort == "title":
			query = query.order_by(Article.title.asc())
		elif sort == "views":
			query = query.order_by(Article.view_count.desc())
		else:  # date (default)
			query = query.order_by(Article.created_at.desc())

		# Apply pagination
		articles = query.offset(offset).limit(limit).all()

		return articles, total

	def get_more_like_this_by_user(
			self,
			user_id: uuid.UUID
	) -> List[Article]:
		"""
        Get articles user marked as 'more like this'.
        """
		return (
			self._db.query(Article)
			.join(UserMoreLikeThis, UserMoreLikeThis.article_id == Article.id)
			.filter(UserMoreLikeThis.user_id == user_id)
			.all()
		)

	def get_read_history_by_user(
			self,
			user_id: uuid.UUID
	) -> List[Article]:
		"""
		Get articles read by the user.
		"""
		return (
			self._db.query(Article)
			.join(UserReadHistory, UserReadHistory.article_id == Article.id)
			.filter(UserReadHistory.user_id == user_id)
			.all()
		)

	def record_view(
			self,
			article_id:uuid.UUID,
			user_id:uuid.UUID
	) -> None:
		"""Record article view in read history"""
		existing = self._db.query(UserReadHistory).filter_by(user_id=user_id, article_id=article_id).first()
		if existing:
			existing.last_read_at = datetime.utcnow()
		else:
			self._db.add(UserReadHistory(user_id=user_id, article_id=article_id))
		try:
			self._db.commit()
		except IntegrityError as e:
			self._db.rollback()
			raise APIError("Invalid user_id or article_id")

	def add_more_like_this(
			self,
			article_id:uuid.UUID,
			user_id:uuid.UUID
	) -> None:
		"""Record user preference for similar articles"""
		existing = self._db.query(UserMoreLikeThis).filter_by(user_id=user_id, article_id=article_id).first()

		if not existing:
			self._db.add(UserMoreLikeThis(user_id=user_id, article_id=article_id))
			try:
				self._db.commit()
			except IntegrityError as e:
				self._db.rollback()
				raise APIError("Invalid user_id or article_id")

	def remove_more_like_this(
			self,
			article_id: uuid.UUID,
			user_id: uuid.UUID):
		"""Remove user preference for similar articles"""
		deleted = self._db.query(UserMoreLikeThis).filter_by(user_id=user_id, article_id=article_id).delete()
		if not deleted:
			raise APIError("Preference record not found")

	def get_article_by_id(
			self,
			article_id: uuid.UUID
	) -> Article | None:
		"""Get article by ID."""
		return self._db.query(Article).filter(Article.id == article_id).first()

	def get_recent_published_articles(self, limit: int = 100) -> List[Article]:
		"""
        Get recent published articles (ordered by creation date (newest first)).

        Args:
            limit: Maximum number of articles to return
        """
		return (
			self._db.query(Article)
			.filter(Article.status == "published")
			.order_by(Article.created_at.desc())
			.limit(limit)
			.all()
		)

	def get_published_articles_since(self, date: datetime) -> List[Article]:
		"""
        Get published articles created after a cutoff date.
        """
		return (
			self._db.query(Article)
			.filter(
				Article.status == "published",
				Article.created_at >= date
			)
			.all()
		)

def get_article_repository(db: Session = Depends(get_db)) -> ArticleRepository:
	return ArticleRepository(db)
