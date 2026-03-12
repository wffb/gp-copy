import logging
import math
import uuid
from datetime import datetime, timezone, timedelta
import random
from typing import Dict, List, Set, Tuple, Optional
from uuid import UUID

from fastapi import Depends

from app.models import Article, ArticleScore
from app.repositories.search_repository import SearchRepository, get_search_repository
from app.repositories.article_repository import ArticleRepository, get_article_repository
from app.repositories.bookmark_repository import BookmarkRepository, get_bookmark_repository
from app.repositories.interest_repository import InterestRepository, get_interest_repository
from app.repositories.user_repository import UserRepository, get_user_repository

class ScoringService:
    """
        Handles article scoring and ranking for personalized search.

        Scoring Formula:
        1. Base Score (normalized to 100):
           - Saved searches: 43 pts
           - Interests: 26 pts
           - Saved articles: 17 pts
           - Search history: 9 pts
           - More like this: 4 pts
           - Read history: 2 pts

        2. Modifiers:
           - Read penalty: score × 0.01 (if already read)
           - Recency boost: e^(-0.1 × days_ago)
        """

    # Base scores (normalized)
    SCORES = {
        "saved_searches": 43,  # Articles matching saved search queries
        "interests": 26,  # Articles in user's interest fields
        "saved_articles": 17,  # Keywords match bookmarked articles
        "search_history": 9,  # Matches recent search queries
        "more_like_this": 4,  # Keywords match preferred articles
        "read_history": 2,  # Keywords match previously read articles
    }

    RECENCY_DECAY_CONSTANT = 0.1
    READ_PENALTY_MULTIPLIER = 0.01
    RANDOM_INJECTION_RATE = 3

    def __init__(self,
                 search_repo: SearchRepository,
                 article_repo: ArticleRepository,
                 bookmark_repo: BookmarkRepository,
                 interest_repo: InterestRepository,
                 user_repo: UserRepository):
        self._search_repo = search_repo
        self._article_repo = article_repo
        self._bookmark_repo = bookmark_repo
        self._interest_repo = interest_repo
        self._user_repo = user_repo

    def calculate_article_score(
            self,
            article: Article,
            user_context: Dict
    ) -> Dict:
        """
        Calculate score for an article.
        Returns: Dict with: user_id, article_id, final_score, calculated_at
        """
        base_score = self.calculate_base_score(article, user_context)
        final_score = self.apply_modifiers(base_score, article, user_context)

        return {
            "id": uuid.uuid4(),
            "user_id": user_context["user_id"],
            "article_id": article.id,
            "final_score": final_score,
            "calculated_at": datetime.utcnow(),
        }

    def build_user_context(
            self,
            user_id: UUID,
            articles: Optional[List[Article]] = None
    ) -> Dict:
        """
        Build user context for scoring.

        Args:
            user_id: User to build context for
            articles: Optional list to populate saved_searches matches
        """
        # Get search history
        search_history = self._search_repo.get_search_history_by_user(user_id=user_id)
        saved_search_queries = [s.query for s in search_history if s.is_saved]
        search_history_queries = [s.query for s in search_history if not s.is_saved]

        # Get user interests (nested structure with parent/subfields)
        user_interests = self._interest_repo.get(user_id=user_id)
        interest_ids = set()
        for interest in user_interests:
            if isinstance(interest["id"], str):
                interest_ids.add(UUID(interest["id"]))
            interest_ids.add(interest["id"])  # Parent field ID
            for sub in interest.get("subfields", []):
                interest_ids.add(sub["id"])  # Subfield IDs

        # Get bookmarked articles and extract keywords
        bookmarked_articles = self._bookmark_repo.get_by_user_id(user_id=user_id)
        bookmarked_keywords = self.extract_keywords(bookmarked_articles)

        # Get "more like this" articles and extract keywords
        more_like_this_articles = self._article_repo.get_more_like_this_by_user(user_id=user_id)
        more_like_this_keywords = self.extract_keywords(more_like_this_articles)

        # Get read articles and extract keywords
        read_articles = self._article_repo.get_read_history_by_user(user_id=user_id)
        read_keywords = self.extract_keywords(read_articles)
        read_article_ids = {a.id for a in read_articles}

        user_context = {
            "user_id": user_id,
            "interest_ids": interest_ids,
            "bookmarked_keywords": bookmarked_keywords,
            "search_history_queries": search_history_queries,
            "more_like_this_keywords": more_like_this_keywords,
            "read_history_keywords": read_keywords,
            "read_article_ids": read_article_ids,
            "saved_search_queries": saved_search_queries,
            "saved_searches_article_ids": set(),  # Populated by caller
        }

        # Populate saved searches matches if articles provided
        if articles:
            self.populate_saved_searches_matches(user_context, articles)

        return user_context

    def populate_saved_searches_matches(
            self,
            user_context: Dict,
            articles: List[Article]
    ) -> None:
        """
        Populate saved_searches_article_ids in user context.
        """
        saved_queries = user_context.get("saved_search_queries", [])
        if not saved_queries:
            return

        matching_ids = set()
        for article in articles:
            for query in saved_queries:
                if self._search_repo.article_matches_search_query(query, article.id):
                    matching_ids.add(article.id)
                    break

        user_context["saved_searches_article_ids"] = matching_ids

    def rank_articles_by_scores(
            self,
            article_scores: List[ArticleScore],
            inject_random: bool = True,
            all_articles: Optional[List[Article]] = None
    ) -> List[UUID]:
        """
        Rank article IDs by their pre-calculated scores.

        Args:
            article_scores: List of ArticleScore objects
            inject_random: Whether to inject random articles every 3rd position
            all_articles: Pool of all articles for random injection

        Returns:
            List of article IDs in ranked order
        """
        if not article_scores:
            return []

        # Group by score for tie-breaking
        score_groups: Dict[float, List[UUID]] = {}
        for score_obj in article_scores:
            score = score_obj.final_score
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(score_obj.article_id)

        # Shuffle within each score group (tie-breaking)
        for score in score_groups:
            random.shuffle(score_groups[score])

        # Flatten in descending score order
        sorted_scores = sorted(score_groups.keys(), reverse=True)
        ranked_ids = []
        for score in sorted_scores:
            ranked_ids.extend(score_groups[score])


        # Inject random articles every Nth position
        if inject_random and all_articles and len(ranked_ids) >= self.RANDOM_INJECTION_RATE:
            ranked_ids = self.inject_random_articles(ranked_ids, all_articles)

        return ranked_ids

    def inject_random_articles(
            self,
            ranked_ids: List[UUID],
            all_articles: List[Article]
    ) -> List[UUID]:
        """Inject random articles at every 3rd position."""
        result = ranked_ids.copy()
        used_ids = set(ranked_ids)

        # Build random pool from unused articles
        random_pool = [a.id for a in all_articles if a.id not in used_ids]
        if not random_pool:
            return result

        random.shuffle(random_pool)
        pool_idx = 0

        # Replace every 3rd article
        for i in range(self.RANDOM_INJECTION_RATE - 1, len(result), self.RANDOM_INJECTION_RATE):
            if pool_idx >= len(random_pool):
                break
            result[i] = random_pool[pool_idx]
            pool_idx += 1

        return result

    def calculate_scores_for_user(
            self,
            user_id: UUID,
            limit: int = 100
    ) -> Dict:
        """
        Calculate and store scores for a batch of articles for a user.
        Called by background jobs.
        """

        # Get recent articles from repository
        articles = self._article_repo.get_recent_published_articles(limit=limit)

        if not articles:
            logging.warning("No articles found for scoring")
            return {"user_id": str(user_id), "articles_scored": 0}

        # Build user context with saved searches populated
        user_context = self.build_user_context(user_id, articles)

        # Score all articles and batch update
        total_scored = 0
        for article in articles:
            try:
                score_data = self.calculate_article_score(article, user_context)
                self._search_repo.update_article_score(score_data)
                total_scored += 1
            except Exception as e:
                logging.error(f"Error calculating score for article {article.id}: {e}")
                continue

        logging.info(f"Calculated scores for {len(articles)} articles for user {user_id}")

        return {
            "user_id": str(user_id),
            "articles_scored": total_scored,
            "timestamp": datetime.utcnow().isoformat()
        }

    def calculate_scores_for_new_article(
            self,
            article_id: UUID,
            max_users: int = 1000
    ) -> Dict:
        """
        Calculate scores for all users when new article is published.
        Called by background jobs
        """
        # Get the article from repository
        article = self._article_repo.get_article_by_id(article_id)
        if not article:
            logging.error(f"Article {article_id} not found")
            return {"error": "Article not found", "article_id": str(article_id)}

        # Get all users from repository
        user_ids = self._user_repo.get_all_user_ids(limit=max_users)

        logging.info(f"Scoring article {article_id} for {len(user_ids)} users")

        # Calculate scores for each user
        total_calculated = 0
        for user_id in user_ids:
            try:
                user_context = self.build_user_context(user_id,[article])
                score_data = self.calculate_article_score(article, user_context)
                self._search_repo.update_article_score(score_data)
                total_calculated += 1

            except Exception as e:
                logging.error(f"Failed scoring for user {user_id}: {e}")
                continue

        result = {
            "article_id": str(article_id),
            "users_scored": total_calculated,
            "timestamp": datetime.utcnow().isoformat()
        }

        return result

    def batch_update_scores(
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

        # Get recent articles from repository
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        articles = self._article_repo.get_published_articles_since(cutoff_date)

        if not articles:
            logging.info("No recent articles for batch update")
            return {"articles": 0, "users": 0, "total_scores": 0}

        # Get users from repository
        user_ids = self._user_repo.get_all_user_ids(limit=max_users)

        total_scores = 0
        for user_id in user_ids:
            try:
                user_context = self.build_user_context(user_id, articles)

                for article in articles:
                    try:
                        score_data = self.calculate_article_score(article, user_context)
                        self._search_repo.update_article_score(score_data)
                        total_scores += 1

                    except Exception as e:
                        logging.error(f"Failed scoring article {article.id}: {e}")
                        continue

            except Exception as e:
                logging.error(f"Failed batch for user {user_id}: {e}")
                continue

        result = {
            "articles_processed": len(articles),
            "users_processed": len(user_ids),
            "total_scores": total_scores,
            "timestamp": datetime.utcnow().isoformat()
        }

        return result

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def calculate_base_score(
            self,
            article: Article,
            user_context: Dict
    ) -> float:
        """Calculate base score from all components."""
        score = 0.0
        article_keywords = set(kw.lower() for kw in (article.keywords or []))

        # 1. Saved Searches (43 pts)
        if article.id in user_context.get("saved_searches_article_ids", set()):
            score += self.SCORES["saved_searches"]

        # 2. Interests (26 pts)
        # Check both primary field and subfield
        if hasattr(article, 'paper') and article.paper:
            if (article.paper.primary_field_id in user_context.get("interest_ids", set()) or
                    article.paper.primary_subfield_id in user_context.get("interest_ids", set())):
                score += self.SCORES["interests"]

        # 3. Saved Articles (17 pts) - keyword matching
        if article_keywords & user_context.get("bookmarked_keywords", set()):
            score += self.SCORES["saved_articles"]

        # 4. Search History (9 pts)
        for query in user_context.get("search_history_queries", []):
            if self._search_repo.article_matches_search_query(query, article.id):
                score += self.SCORES["search_history"]
                break  # Only count once

        # 5. More Like This (4 pts) - keyword matching
        if article_keywords & user_context.get("more_like_this_keywords", set()):
            score += self.SCORES["more_like_this"]

        # 6. Read History (2 pts) - keyword matching
        if article_keywords & user_context.get("read_history_keywords", set()):
            score += self.SCORES["read_history"]

        return score

    def apply_modifiers(
            self,
            base_score: float,
            article: Article,
            user_context: Dict
    ) -> float:
        """Apply read status and recency modifiers."""
        # 1. Read Status Modifier (drops read articles to bottom)
        is_read = article.id in user_context.get("read_article_ids", set())
        if is_read:
            base_score *= self.READ_PENALTY_MULTIPLIER

        # 2. Recency Modifier (exponential decay)
        if hasattr(article, 'created_at') and article.created_at:
            now = datetime.now(timezone.utc)
            created = article.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            days_ago = (now - created).days
            recency_multiplier = math.exp(-self.RECENCY_DECAY_CONSTANT * days_ago)
            base_score *= recency_multiplier

        return base_score

    def extract_keywords(self, articles: List[Article]) -> Set[str]:
        """Extract unique lowercase keywords from articles."""
        keywords = set()
        for article in articles:
            if article.keywords:
                keywords.update(kw.lower() for kw in article.keywords)
        return keywords

def get_scoring_service(
        search_repo: SearchRepository = Depends(get_search_repository),
        article_repo: ArticleRepository = Depends(get_article_repository),
        bookmark_repo: BookmarkRepository = Depends(get_bookmark_repository),
        interest_repo: InterestRepository = Depends(get_interest_repository),
        user_repo: UserRepository = Depends(get_user_repository),
) -> ScoringService:
    return ScoringService(search_repo, article_repo, bookmark_repo, interest_repo, user_repo)