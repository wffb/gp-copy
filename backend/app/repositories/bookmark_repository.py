from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.exceptions.exceptions import BookmarkAlreadyExistsError
from app.models.article import Article
from app.models.bookmark import Bookmark
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate
from fastapi import HTTPException, Depends


class BookmarkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, bookmark: BookmarkCreate) -> Bookmark:
        db_bookmark = Bookmark(user_id=bookmark.user_id, article_id=bookmark.article_id)
        self._session.add(db_bookmark)
        self._session.commit()
        self._session.refresh(db_bookmark)
        return db_bookmark


    def get_by_id(self, bookmark_id: uuid.UUID) -> Bookmark | None:
        return self._session.query(Bookmark).filter(Bookmark.id == bookmark_id).first()

    def get_by_user_id(self, user_id: uuid.UUID) -> list[Article]:
        return (
            self._session.query(Article)
            .join(Bookmark, Bookmark.article_id == Article.id)
            .filter(Bookmark.user_id == user_id)
            .all()
        )

    def get_by_user_id_and_article_id(self, user_id: uuid.UUID, article_id: uuid.UUID) -> Bookmark | None:
        return self._session.query(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.article_id == article_id).first()


    def delete(self, bookmark_id: uuid.UUID) -> None:
        db_bookmark = self.get_by_id(bookmark_id)
        if db_bookmark is None:
            raise HTTPException(status_code=404, detail="Bookmark not found")

        self._session.delete(db_bookmark)
        self._session.commit()
        return


def get_bookmark_repository(db: Session = Depends(get_db)) -> BookmarkRepository:
    return BookmarkRepository(db)