import uuid
import re
from datetime import datetime
from uuid import UUID
from typing import List, Tuple, Optional

from fastapi.params import Depends
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, joinedload

from app.api.deps import get_db
from app.exceptions.exceptions import APIError, InvalidFieldError
from app.models import UserSearchHistory
from app.models.article import Article
from app.models.field import Field
from app.models.paper import Paper
from app.models import ArticleScore


class SearchRepository:
    def __init__(self, db: Session):
        self._db = db

    def record_search(
            self,
            user_id: UUID,
            query_text: str,
            is_saved: bool
    ) -> UserSearchHistory:
        """Record or update a search query"""
        try:
            query_record = self._db.query(UserSearchHistory).filter_by(
                user_id=user_id,
                query=query_text
            ).first()

            if not query_record:
                query_record = UserSearchHistory(
                    user_id=user_id,
                    query=query_text,
                    is_saved=is_saved,
                    last_searched_at=datetime.utcnow(),
                    search_count=1,
                    saved_at=datetime.utcnow() if is_saved else None
                )
                self._db.add(query_record)
            else:
                # Update existing
                query_record.last_searched_at = datetime.utcnow()
                query_record.search_count += 1

                if is_saved and not query_record.is_saved:
                    query_record.is_saved = True
                    query_record.saved_at = query_record.last_searched_at

            self._db.commit()
            self._db.refresh(query_record)
            return query_record

        except IntegrityError as e:
            self._db.rollback()
            raise APIError(str(e))

    def remove_search(
            self,
            user_id: UUID,
            query_text: str
    ) -> UserSearchHistory:
        """Remove the saved status of a user's search query"""
        try:
            query_record = self._db.query(UserSearchHistory).filter_by(
                user_id=user_id,
                query=query_text
            ).first()

            if not query_record:
                raise APIError("Search query not found")

            if query_record.is_saved:
                query_record.is_saved = False
                query_record.saved_at = None

            self._db.commit()
            self._db.refresh(query_record)
            return query_record

        except IntegrityError as e:
            self._db.rollback()
            raise APIError(str(e))

    def get_saved_searches_by_user(self, user_id: UUID) -> List[UserSearchHistory]:
        """Get saved searches by user"""
        return (
            self._db.query(UserSearchHistory)
            .filter(UserSearchHistory.user_id == user_id)
            .filter(UserSearchHistory.is_saved == True)
            .all()
        )

    def get_search_history_by_user(self, user_id: UUID) -> List[UserSearchHistory]:
        """Get search history by user"""
        return (
            self._db.query(UserSearchHistory)
            .filter(UserSearchHistory.user_id == user_id)
            .all()
        )

    def get_article_scores_by_user(self, user_id: UUID) -> List[ArticleScore]:
        """Get article scores by user"""
        return (
            self._db.query(ArticleScore).join(Article)
            .filter(ArticleScore.user_id == user_id)
            .all()
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
            search_filter = self.build_search(search_query)
            filters.append(search_filter)

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

    def build_search(self, search_query: str):
        """
        Full-Text Search with Word boundary matching, Stemming, Ranking by relevance (Fast with GIN indexes)
        """
        clean_query = re.sub(r'[^\w\s]', ' ', search_query.lower())
        search_terms = [t.strip() for t in clean_query.split() if t.strip()]

        # Optional: Remove stop words
        # stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        # terms = [t for t in terms if t not in stop_words and len(t) > 1]

        tsquery_string = ' & '.join([f"{term}:*" for term in search_terms])

        # Create full-text search conditions
        title_search = func.to_tsvector('english', Article.title).op('@@')(
            func.to_tsquery('english', tsquery_string)
        )

        description_search = func.to_tsvector('english', Article.description).op('@@')(
            func.to_tsquery('english', tsquery_string)
        )

        # Keywords: Check if any search term is in keywords array
        keyword_search = or_(
            *[Article.keywords.contains([term]) for term in search_terms]
        )

        return or_(title_search, description_search, keyword_search)

    def article_matches_search_query(
            self,
            search_query: str,
            article_id: uuid,
    ) -> bool:
        """Checks if an article is listed in a search query"""

        # Use same search logic as list_articles
        search_filter = self.build_search(search_query)

        result = (
            self._db.query(Article)
            .filter(
                Article.id == article_id,
                search_filter
            )
            .first()
        )

        return result is not None


    def update_article_score(self, score_data: dict) -> None:
        """
        Create or update an article's score record.
        """
        try:
            score_record = self._db.query(ArticleScore).filter_by(
                user_id=score_data["user_id"],
                article_id=score_data["article_id"],
            ).first()

            if not score_record:
                # Create new record
                score_record = ArticleScore(
                    user_id=score_data["user_id"],
                    article_id=score_data["article_id"],
                    final_score=score_data["final_score"],
                    calculated_at=score_data["calculated_at"],
                )
                self._db.add(score_record)
            else:
                score_record.final_score = score_data["final_score"]
                score_record.calculated_at = datetime.utcnow()

            self._db.commit()
            self._db.refresh(score_record)

        except IntegrityError as e:
            self._db.rollback()
            raise APIError(f"Database integrity error: {e}")

        except Exception as e:
            self._db.rollback()
            raise APIError(str(e))


def get_search_repository(db: Session = Depends(get_db)) -> SearchRepository:
    return SearchRepository(db)