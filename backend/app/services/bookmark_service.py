from __future__ import annotations

import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from app.exceptions.exceptions import BookmarkAlreadyExistsError, BookmarkDoesNotExistError
from app.models.article import Article
from app.models.bookmark import Bookmark
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.repositories.bookmark_repository import BookmarkRepository, get_bookmark_repository
from fastapi import HTTPException


class BookmarkService:
	def __init__(self, repo: BookmarkRepository) -> None:
		self._repo = repo

	def create_bookmark(self, create: BookmarkCreate) -> Bookmark:
		if self._repo.get_by_user_id_and_article_id(create.user_id, create.article_id) is not None:
			raise BookmarkAlreadyExistsError("Bookmark already exists")

		db_bookmark = self._repo.create(create)
		return db_bookmark

	def get_bookmark_by_id(self, bookmark_id: uuid.UUID) -> Bookmark:
		db_bookmark = self._repo.get_by_id(bookmark_id)
		if db_bookmark is None:
			raise BookmarkDoesNotExistError("Bookmark not found")
		return db_bookmark

	def get_bookmarks_by_user_id(self, user_id: uuid.UUID) -> list[Article]:
		return self._repo.get_by_user_id(user_id)

	def delete_bookmark(self, bookmark_id: uuid.UUID, user_id: uuid.UUID) -> Bookmark:

		db_bookmark = self._repo.get_by_id(bookmark_id)

		if (db_bookmark is None) or (str(db_bookmark.user_id) != str(user_id)):
			raise BookmarkDoesNotExistError("Bookmark not found")
		self._repo.delete(bookmark_id)

		return db_bookmark

	def delete_bookmark_by_article_id(self, article_id: uuid.UUID, user_id: uuid.UUID) -> None:
		db_bookmark = self._repo.get_by_user_id_and_article_id(user_id, article_id)
		
		if db_bookmark is None:
			raise BookmarkDoesNotExistError("Bookmark not found")
		
		self._repo.delete(db_bookmark.id)


def get_bookmark_service(repo: BookmarkRepository = Depends(get_bookmark_repository)) -> BookmarkService:
	return BookmarkService(repo)
