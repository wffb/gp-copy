"""
Background tasks for article scoring.
"""

from __future__ import annotations

import logging
from typing import Dict
from uuid import UUID
from app.services.scoring_service import ScoringService, get_scoring_service

class ScoreCalculationJobs:
    """
    Manages background jobs for score calculation.
    """

    def __init__(self, scoring_service: ScoringService):
        self._scoring_service = scoring_service


    def score_new_article_task(
            self,
            article_id: UUID,
            max_users: int = 1000
    ) -> Dict:
        """
        Calculate scores for all users when new article is published.

        Args:
            article_id: ID of the newly published article
            max_users: Maximum users to process in one batch

        Returns:
            Dict with article_id, users_scored, timestamp
        """
        logging.info(f"Task: Calculating scores for new article: {article_id}")

        try:
            result = self._scoring_service.calculate_scores_for_new_article(article_id, max_users)
            logging.info(f"Task complete: {result}")
            return result

        except Exception as e:
            logging.error(f"Task failed: {e}")
            raise


    def score_for_user_task(
            self,
            user_id: UUID,
            limit: int = 100
    ) -> Dict:
        """
        Recalculate scores for user's recent articles.

        Args:
            user_id: ID of the user
            limit: Maximum articles to score

        Returns:
            Dict with user_id, articles_scored, timestamp
        """
        logging.info(f"Task: Recalculating scores for user: {user_id}")

        try:
            result = self._scoring_service.calculate_scores_for_user(user_id, limit)
            logging.info(f"Task complete: {result}")
            return result

        except Exception as e:
            logging.error(f"Task failed: {e}")
            raise


    def batch_update_scores_task(
            self,
            days_back: int = 2,
            max_users: int = 100
    ) -> Dict:
        """
        Periodic batch update: Recent articles × Active users.

        Args:
            days_back: How many days of articles to process
            max_users: Maximum users to process

        Returns:
            Dict with articles_processed, users_processed, total_scores, timestamp
        """
        logging.info("Task: Starting batch score update")

        try:
            result = self._scoring_service.batch_update_scores(days_back, max_users)
            logging.info(f"Batch update task complete: {result}")
            return result

        except Exception as e:
            logging.error(f"Batch update task failed: {e}")
            raise
