import math
import uuid
from typing import Optional
from fastapi import Depends
from slugify import slugify

from app.repositories.article_repository import ArticleRepository, get_article_repository
from app.repositories.bookmark_repository import BookmarkRepository, get_bookmark_repository
from app.schemas import ArticleListDTO, ArticleDTO
from app.schemas.article import BlockDTO
from app.models.article import Article
from app.models.user import User
from app.exceptions.exceptions import ArticleNotFoundError


class ArticleService:
	def __init__(self, article_repo: ArticleRepository, bookmark_repo: BookmarkRepository):
		self._repo = article_repo
		self._bookmark_repo = bookmark_repo

	def fetch_article_by_slug(self, slug: str) -> ArticleDTO:
		"""
		Fetch a single article by slug.
		"""

		slug = slugify(slug)
		article = self._repo.get_article_by_slug(slug)

		if not article:
			raise ArticleNotFoundError(f"Article with slug '{slug}' not found")

		# For a single-article fetch, include content blocks
		return self._to_dto(article, include_blocks=True)

	def list_articles(
			self,
			page: int = 1,
			limit: int = 20,
			field_code: Optional[str] = None,
			search_query: Optional[str] = None,
			sort: str = "date",
			current_user: Optional[User] = None
	) -> ArticleListDTO:
		"""
		List published articles with pagination and optional field filtering.
		"""
		offset = (page - 1) * limit

		# Repository will raise InvalidFieldError if field_code is invalid
		articles, total = self._repo.list_articles(
			offset=offset,
			limit=limit,
			field_code=field_code,
			search_query=search_query,
			sort=sort,
			status="published"
		)

		# In list view, do not include blocks to avoid large payloads
		items = [self._to_dto(article, current_user, include_blocks=False) for article in articles]
		total_pages = math.ceil(total / limit) if total > 0 else 0

		return ArticleListDTO(
			items=items,
			total=total,
			page=page,
			limit=limit,
			total_pages=total_pages,
			has_next=page < total_pages,
			has_prev=page > 1
		)

	def _to_dto(self, article: Article, current_user: Optional[User] = None, include_blocks: bool = True) -> ArticleDTO:
		"""Convert Article model to DTO.

		- When include_blocks is True (single-article view), include ordered blocks.
		- When False (list view), omit blocks to reduce payload and queries.
		"""
		is_bookmarked = False
		if current_user:
			bookmark = self._bookmark_repo.get_by_user_id_and_article_id(current_user.id, article.id)
			is_bookmarked = bookmark is not None

		blocks = None
		if include_blocks:
			# Ensure blocks are ordered by order_index; omit if empty
			ordered_blocks = sorted(getattr(article, "blocks", []) or [], key=lambda b: b.order_index)
			blocks = [
				BlockDTO(
					id=b.id,
					block_type=b.block_type,
					content=b.content,
					order_index=b.order_index,
					created_at=b.created_at,
					updated_at=b.updated_at,
				)
				for b in ordered_blocks
			] or None

		return ArticleDTO(
			id=article.id,
			title=article.title,
			description=article.description,
			keywords=article.keywords or [],
			slug=article.slug,
			featured_image_url=article.featured_image_url,
			view_count=article.view_count,
			created_at=article.created_at,
			updated_at=article.updated_at,
			is_bookmarked=is_bookmarked,
			blocks=blocks,
		)

	def record_read_history(self, article_id:uuid.UUID, user_id:uuid.UUID):
		"""Record article view in read history"""
		self._repo.record_view(article_id, user_id)
		return {"message": "Successfully recorded read history for article {} and user {} ".format(
			article_id, user_id)}

	def add_more_like_this(self, article_id:uuid.UUID, user_id:uuid.UUID):
		"""Record user preference for similar articles"""
		self._repo.add_more_like_this(article_id, user_id)
		return {"message": "Successfully added preference for articles like article {} for user {} ".format(
			article_id, user_id)}

	def remove_more_like_this(self, article_id:uuid.UUID, user_id:uuid.UUID):
		"""Remove recorded user preference for similar articles"""
		self._repo.remove_more_like_this(article_id, user_id)
		return {"message": "Successfully removed preference for articles like article {} for user {} ".format(
			article_id, user_id)}

def get_article_service(
		repo: ArticleRepository = Depends(get_article_repository),
		bookmark_repo: BookmarkRepository = Depends(get_bookmark_repository)
) -> ArticleService:
	return ArticleService(repo, bookmark_repo)
