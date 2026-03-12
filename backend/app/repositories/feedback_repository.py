from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from fastapi import Depends


class FeedbackRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, feedback: FeedbackCreate) -> Feedback:
        db_feedback = Feedback(
            first_name=feedback.first_name,
            last_name=feedback.last_name,
            email=feedback.email,
            message=feedback.message
        )
        self._session.add(db_feedback)
        self._session.commit()
        self._session.refresh(db_feedback)
        return db_feedback

    def get_by_id(self, feedback_id: uuid.UUID) -> Feedback | None:
        return self._session.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_feedback_repository(db: Session = Depends(get_db)) -> FeedbackRepository:
    return FeedbackRepository(db)