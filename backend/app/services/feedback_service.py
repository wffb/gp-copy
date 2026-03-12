from __future__ import annotations

from fastapi import Depends

from app.exceptions.exceptions import FeedbackCreateFailedError
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from app.repositories.feedback_repository import FeedbackRepository, get_feedback_repository


class FeedbackService:
    def __init__(self, repo: FeedbackRepository) -> None:
        self._repo = repo

    def create_feedback(self, create: FeedbackCreate) -> Feedback:
        try:
            db_feedback = self._repo.create(create)
            return db_feedback
        except Exception as e:
            raise FeedbackCreateFailedError("Failed to create feedback")


def get_feedback_service(repo: FeedbackRepository = Depends(get_feedback_repository)) -> FeedbackService:
    return FeedbackService(repo)