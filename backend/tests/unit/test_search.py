# tests/unit/test_search.py
"""
Unit tests for personalized search algorithm.
Tests both scoring logic and search functionality.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest

from app.models import Article, ArticleScore
from app.models.user import User
from app.services.scoring_service import ScoringService
from app.services.search_service import SearchService


# ============================================================================
# SCORING SERVICE TESTS
# ============================================================================

class TestScoringService:
    """Test article scoring calculations."""

    def test_calculate_base_score_saved_searches(self):
        """Test scoring for saved search matches (43 pts)."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        article = Article(
            id=uuid.uuid4(),
            title="Quantum Computing",
            keywords=["quantum", "computing"]
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "saved_searches_article_ids": {article.id},
            "interest_ids": set(),
            "bookmarked_keywords": set(),
            "search_history_queries": [],
            "more_like_this_keywords": set(),
            "read_history_keywords": set(),
            "read_article_ids": set()
        }

        score = service.calculate_base_score(article, user_context)
        assert score == 43.0

    def test_calculate_base_score_interests(self, sample_field, sample_paper):
        """Test scoring for user interests (26 pts)."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        article = Article(
            id=uuid.uuid4(),
            title="Physics Paper",
            paper_id=sample_paper.id,
            paper=sample_paper,
            keywords=["physics"]
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "saved_searches_article_ids": set(),
            "interest_ids": {sample_field.id},
            "bookmarked_keywords": set(),
            "search_history_queries": [],
            "more_like_this_keywords": set(),
            "read_history_keywords": set(),
            "read_article_ids": set()
        }

        score = service.calculate_base_score(article, user_context)
        assert score == 26.0

    def test_calculate_base_score_bookmarked_keywords(self):
        """Test scoring for bookmark keyword matches (17 pts)."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        article = Article(
            id=uuid.uuid4(),
            title="Machine Learning",
            keywords=["machine", "learning", "ai"]
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "saved_searches_article_ids": set(),
            "interest_ids": set(),
            "bookmarked_keywords": {"machine", "learning"},
            "search_history_queries": [],
            "more_like_this_keywords": set(),
            "read_history_keywords": set(),
            "read_article_ids": set()
        }

        score = service.calculate_base_score(article, user_context)
        assert score == 17.0

    def test_calculate_base_score_multiple_signals(self):
        """Test scoring with multiple signals combined."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        article = Article(
            id=uuid.uuid4(),
            title="Quantum AI",
            keywords=["quantum", "ai", "machine"]
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "saved_searches_article_ids": {article.id},  # 43 pts
            "interest_ids": set(),
            "bookmarked_keywords": {"quantum", "ai"},  # 17 pts
            "search_history_queries": [],
            "more_like_this_keywords": {"machine"},  # 4 pts
            "read_history_keywords": set(),
            "read_article_ids": set()
        }

        score = service.calculate_base_score(article, user_context)
        assert score == 43 + 17 + 4  # 64 total

    def test_apply_modifiers_read_penalty(self):
        """Test read status modifier reduces score by 99%."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        article = Article(
            id=uuid.uuid4(),
            title="Read Article",
            created_at=datetime.utcnow()
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "read_article_ids": {article.id}
        }

        base_score = 100.0
        final_score = service.apply_modifiers(base_score, article, user_context)

        # Should be multiplied by 0.01
        assert final_score == 1.0

    def test_apply_modifiers_recency_boost(self):
        """Test recency modifier for recent articles."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        # Article from 1 day ago
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        article = Article(
            id=uuid.uuid4(),
            title="Recent Article",
            created_at=one_day_ago
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "read_article_ids": set()
        }

        base_score = 100.0
        final_score = service.apply_modifiers(base_score, article, user_context)

        # Should have recency boost: 100 * e^(-0.1 * 1) ≈ 90.48
        assert 90.0 < final_score < 91.0

    def test_apply_modifiers_old_article_decay(self):
        """Test recency modifier for old articles."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        # Article from 30 days ago
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        article = Article(
            id=uuid.uuid4(),
            title="Old Article",
            created_at=thirty_days_ago
        )

        user_context = {
            "user_id": uuid.uuid4(),
            "read_article_ids": set()
        }

        base_score = 100.0
        final_score = service.apply_modifiers(base_score, article, user_context)

        # Should have significant decay: 100 * e^(-0.1 * 30) ≈ 4.98
        assert 4.0 < final_score < 6.0

    def test_extract_keywords_from_articles(self):
        """Test keyword extraction from article list."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        articles = [
            Article(id=uuid.uuid4(), keywords=["Quantum", "Physics"]),
            Article(id=uuid.uuid4(), keywords=["Machine", "Learning"]),
            Article(id=uuid.uuid4(), keywords=["quantum", "computing"])
        ]

        keywords = service.extract_keywords(articles)

        # Should be lowercase and unique
        assert keywords == {"quantum", "physics", "machine", "learning", "computing"}

    def test_rank_articles_by_scores_simple(self):
        """Test basic ranking by scores."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        user_id = uuid.uuid4()
        article1_id = uuid.uuid4()
        article2_id = uuid.uuid4()
        article3_id = uuid.uuid4()

        scores = [
            ArticleScore(user_id=user_id, article_id=article1_id, final_score=10.0),
            ArticleScore(user_id=user_id, article_id=article2_id, final_score=50.0),
            ArticleScore(user_id=user_id, article_id=article3_id, final_score=30.0),
        ]

        ranked_ids = service.rank_articles_by_scores(
            scores,
            inject_random=False,
            all_articles=None
        )

        # Should be sorted by score descending
        assert ranked_ids == [article2_id, article3_id, article1_id]

    def test_rank_articles_handles_ties(self):
        """Test tie-breaking with equal scores."""
        mock_search_repo = Mock()
        mock_article_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_interest_repo = Mock()
        mock_user_repo = Mock()

        service = ScoringService(
            mock_search_repo,
            mock_article_repo,
            mock_bookmark_repo,
            mock_interest_repo,
            mock_user_repo
        )

        user_id = uuid.uuid4()
        article1_id = uuid.uuid4()
        article2_id = uuid.uuid4()
        article3_id = uuid.uuid4()

        scores = [
            ArticleScore(user_id=user_id, article_id=article1_id, final_score=50.0),
            ArticleScore(user_id=user_id, article_id=article2_id, final_score=50.0),
            ArticleScore(user_id=user_id, article_id=article3_id, final_score=30.0),
        ]

        ranked_ids = service.rank_articles_by_scores(
            scores,
            inject_random=False,
            all_articles=None
        )

        # First two should have score 50 (order random)
        assert len(ranked_ids) == 3
        assert ranked_ids[2] == article3_id  # Lowest score last
        assert set(ranked_ids[:2]) == {article1_id, article2_id}


# ============================================================================
# SEARCH SERVICE TESTS
# ============================================================================

class TestSearchService:
    """Test search functionality with personalization."""

    def test_personalized_search_records_query(self, test_db, test_user, article_factory):
        """Test that non-dynamic searches are recorded."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        # Setup mocks
        article = article_factory(title="Test Article")
        mock_search_repo.list_articles.return_value = ([article], 1)
        mock_search_repo.get_article_scores_by_user.return_value = [
            ArticleScore(
                user_id=test_user.id,
                article_id=article.id,
                final_score=50.0
            )
        ]
        mock_scoring_service.rank_articles_by_scores.return_value = [article.id]
        mock_bookmark_repo.get_by_user_id_and_article_id.return_value = None

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        # Execute search
        service.personalized_search(
            page=1,
            limit=20,
            search_query="quantum",
            current_user=test_user,
            field_code=None,
            is_dynamic=False
        )

        # Verify search was recorded
        mock_search_repo.record_search.assert_called_once_with(
            user_id=test_user.id,
            query_text="quantum",
            is_saved=False
        )

    def test_personalized_search_dynamic_no_recording(self, test_user, article_factory):
        """Test that dynamic searches are NOT recorded."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        article = article_factory(title="Test Article")
        mock_search_repo.list_articles.return_value = ([article], 1)
        mock_search_repo.get_article_scores_by_user.return_value = [
            ArticleScore(
                user_id=test_user.id,
                article_id=article.id,
                final_score=50.0
            )
        ]
        mock_scoring_service.rank_articles_by_scores.return_value = [article.id]
        mock_bookmark_repo.get_by_user_id_and_article_id.return_value = None

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        # Execute dynamic search
        service.personalized_search(
            page=1,
            limit=20,
            search_query="quantum",
            current_user=test_user,
            field_code=None,
            is_dynamic=True
        )

        # Verify search was NOT recorded
        mock_search_repo.record_search.assert_not_called()

    def test_personalized_search_limit_enforcement(self, test_user):
        """Test that dynamic search enforces 8 result limit."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        # Setup: Return more than 8 articles
        articles = [
            Article(
                id=uuid.uuid4(),
                title=f"Article {i}",
                description="desc",
                slug=f"article-{i}",
                keywords=[],
                view_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(15)
        ]
        mock_search_repo.list_articles.return_value = (articles, 15)

        scores = [
            ArticleScore(user_id=test_user.id, article_id=a.id, final_score=50.0)
            for a in articles
        ]
        mock_search_repo.get_article_scores_by_user.return_value = scores
        mock_scoring_service.rank_articles_by_scores.return_value = [a.id for a in articles]
        mock_bookmark_repo.get_by_user_id_and_article_id.return_value = None

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        result = service.personalized_search(
            page=1,
            limit=20,  # Request 20
            search_query="test",
            current_user=test_user,
            field_code=None,
            is_dynamic=True  # But dynamic mode
        )

        # Should only return 8 (DYNAMIC_SEARCH_LIMIT)
        assert len(result.items) <= 8

    def test_basic_search_for_guests(self, article_factory):
        """Test basic search without personalization."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        articles = [article_factory(title=f"Article {i}") for i in range(3)]
        mock_search_repo.list_articles.return_value = (articles, 3)

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        result = service.basic_search(
            page=1,
            limit=20,
            search_query="test",
            field_code=None,
            current_user=None
        )

        # Should return all articles without scoring
        assert len(result.items) == 3
        assert result.total == 3
        mock_scoring_service.rank_articles_by_scores.assert_not_called()

    def test_personalized_search_fallback_to_basic(self, test_user, article_factory):
        """Test fallback to basic search when no scores exist."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        articles = [article_factory(title="Test Article")]
        mock_search_repo.list_articles.return_value = (articles, 1)
        mock_search_repo.get_article_scores_by_user.return_value = []  # No scores
        mock_bookmark_repo.get_by_user_id_and_article_id.return_value = None

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        result = service.personalized_search(
            page=1,
            limit=20,
            search_query="test",
            current_user=test_user,
            field_code=None,
            is_dynamic=False
        )

        # Should fall back to basic search
        assert len(result.items) == 1
        mock_scoring_service.rank_articles_by_scores.assert_not_called()

    def test_search_pagination(self, test_user):
        """Test search pagination works correctly."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        # Create 25 articles
        articles = [
            Article(
                id=uuid.uuid4(),
                title=f"Article {i}",
                description="Test description",  # Add this
                slug=f"article-{i}",  # Add this
                keywords=[],
                view_count=0,  # Add this
                created_at=datetime.utcnow(),  # Add this
                updated_at=datetime.utcnow()  # Add this
            )
            for i in range(25)
        ]
        mock_search_repo.list_articles.return_value = (articles, 25)

        scores = [
            ArticleScore(user_id=test_user.id, article_id=a.id, final_score=float(25-i))
            for i, a in enumerate(articles)
        ]
        mock_search_repo.get_article_scores_by_user.return_value = scores
        mock_scoring_service.rank_articles_by_scores.return_value = [a.id for a in articles]
        mock_bookmark_repo.get_by_user_id_and_article_id.return_value = None

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        # Get page 2 with 10 items per page
        result = service.personalized_search(
            page=2,
            limit=10,
            search_query="test",
            current_user=test_user,
            field_code=None,
            is_dynamic=False
        )

        assert result.page == 2
        assert result.limit == 10
        assert len(result.items) == 10
        assert result.has_prev is True
        assert result.has_next is True
        assert result.total_pages == 3

    def test_save_search_creates_record(self, test_user):
        """Test saving a search query."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        result = service.save_search(test_user.id, "quantum computing")

        mock_search_repo.record_search.assert_called_once_with(
            user_id=test_user.id,
            query_text="quantum computing",
            is_saved=True
        )
        assert "Successfully saved" in result["message"]

    def test_remove_search_deletes_record(self, test_user):
        """Test removing a saved search."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        result = service.remove_search(test_user.id, "quantum computing")

        mock_search_repo.remove_search.assert_called_once_with(
            user_id=test_user.id,
            query_text="quantum computing"
        )
        assert "Successfully removed" in result["message"]

    def test_search_includes_bookmark_status(self, test_user, article_factory):
        """Test that search results include bookmark status."""
        mock_search_repo = Mock()
        mock_bookmark_repo = Mock()
        mock_scoring_service = Mock()

        article = article_factory(title="Test Article")
        mock_search_repo.list_articles.return_value = ([article], 1)

        scores = [
            ArticleScore(user_id=test_user.id, article_id=article.id, final_score=50.0)
        ]
        mock_search_repo.get_article_scores_by_user.return_value = scores
        mock_scoring_service.rank_articles_by_scores.return_value = [article.id]

        # Mock bookmark exists
        mock_bookmark_repo.get_by_user_id_and_article_id.return_value = Mock()

        service = SearchService(mock_search_repo, mock_bookmark_repo, mock_scoring_service)

        result = service.personalized_search(
            page=1,
            limit=20,
            search_query="test",
            current_user=test_user,
            field_code=None,
            is_dynamic=False
        )

        assert len(result.items) == 1
        assert result.items[0].is_bookmarked is True


def test_search_route_guest_access(client, article_factory):
    """Test search endpoint accessible to guests."""
    article_factory(title="Quantum Physics")

    response = client.get("/api/v1/search/?q=quantum")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data


def test_search_route_authenticated_user(authenticated_client, article_factory):
    """Test search endpoint for authenticated users."""
    article_factory(title="Machine Learning")

    response = authenticated_client.get("/api/v1/search/?q=machine")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data


def test_search_route_dynamic_mode(client, article_factory):
    """Test search with dynamic=true parameter."""
    # Create more than 8 articles
    for i in range(15):
        article_factory(title=f"Test Article {i}")

    response = client.get("/api/v1/search/?q=test&dynamic=true")

    assert response.status_code == 200
    data = response.json()["data"]

    # Should return max 8 articles in dynamic mode
    assert len(data["items"]) <= 8


def test_search_route_field_filter(client, article_factory, sample_field, test_db):
    """Test search with field filter."""
    from app.models.paper import Paper

    paper = Paper(
        title="Physics Paper",
        primary_field_id=sample_field.id,
        primary_subfield_id=sample_field.id,
        status="published"
    )
    test_db.add(paper)
    test_db.flush()

    article_factory(paper_id=paper.id, title="Physics Article")

    response = client.get(f"/api/v1/search/?field={sample_field.code}&q=physics")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) >= 1


def test_save_search_requires_auth(client):
    """Test save search requires authentication."""
    response = client.post(
        "/api/v1/search/save",
        json={"query_text": "quantum"}
    )

    assert response.status_code == 401


def test_search_pagination_metadata(client, article_factory):
    """Test search returns correct pagination metadata."""
    # Create 25 articles
    for i in range(25):
        article_factory(title=f"Article {i}")

    response = client.get("/api/v1/search/?page=2&limit=10")

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["page"] == 2
    assert data["limit"] == 10
    assert data["total"] == 25
    assert data["total_pages"] == 3
    assert data["has_prev"] is True
    assert data["has_next"] is True


def test_search_empty_query(client):
    """Test search with empty query returns all articles."""
    response = client.get("/api/v1/search/")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_search_no_results(client):
    """Test search with no matching results."""
    response = client.get("/api/v1/search/?q=nonexistentquery12345")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 0
    assert data["total"] == 0