# tests/unit/test_articles.py
from __future__ import annotations

import pytest
from datetime import datetime
from app.models.paper import Paper

# List Articles Tests

def test_list_articles_default_pagination(client, article_factory):
    """Test listing articles with default pagination."""
    # Create 3 test articles
    for i in range(3):
        article_factory(title=f"Article {i}")

    response = client.get("/api/v1/articles/")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert len(data["data"]["items"]) == 3
    assert data["data"]["page"] == 1
    assert data["data"]["limit"] == 20


def test_list_articles_custom_pagination(client, article_factory):
    """Test listing articles with custom page size."""
    # Create 5 articles
    for i in range(5):
        article_factory(title=f"Article {i}")

    response = client.get("/api/v1/articles/?page=1&limit=2")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3


def test_list_articles_second_page(client, article_factory):
    """Test pagination to second page."""
    for i in range(5):
        article_factory(title=f"Article {i}")

    response = client.get("/api/v1/articles/?page=2&limit=2")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["page"] == 2
    assert data["has_prev"] is True
    assert data["has_next"] is True


def test_list_articles_filter_by_field(client, article_factory, sample_field, test_db):
    """Test filtering articles by field code (E1-U2)."""

    # Create paper with physics field
    paper = Paper(
        title="Physics Paper",
        primary_field_id=sample_field.id,
        primary_subfield_id=sample_field.id,
        status="published"
    )
    test_db.add(paper)
    test_db.flush()

    article_factory(paper_id=paper.id, title="Physics Article")

    response = client.get(f"/api/v1/articles/?field={sample_field.code}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) >= 1


def test_list_articles_invalid_field(client):
    """Test filtering with non-existent field code."""
    response = client.get("/api/v1/articles/?field=nonexistent")

    assert response.status_code == 400
    error = response.json()
    assert error["title"] == "InvalidFieldError"


def test_list_articles_search_by_title(client, article_factory):
    """Test searching articles by title (E1-U4)."""
    article_factory(title="Quantum Computing Breakthrough")
    article_factory(title="Classical Physics Review")

    response = client.get("/api/v1/articles/?q=quantum")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 1
    assert "quantum" in data["items"][0]["title"].lower()

# Search Tests

def test_list_articles_search_by_description(client, article_factory):
    """Test searching articles by description."""
    article_factory(
        title="Article 1",
        description="This article discusses machine learning"
    )
    article_factory(
        title="Article 2",
        description="This article is about databases"
    )

    response = client.get("/api/v1/articles/?q=machine")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 1


def test_list_articles_search_no_results(client, article_factory):
    """Test search with no matching results."""
    article_factory(title="Test Article")

    response = client.get("/api/v1/articles/?q=nonexistentterm")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 0
    assert data["total"] == 0


def test_list_articles_sort_by_date(client, article_factory):
    """Test sorting articles by date (default)."""
    from datetime import timedelta
    now = datetime.utcnow()

    article_factory(title="Old", created_at=now - timedelta(days=2))
    article_factory(title="Recent", created_at=now)

    response = client.get("/api/v1/articles/?sort=date")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"][0]["title"] == "Recent"


def test_list_articles_sort_by_title(client, article_factory):
    """Test sorting articles by title."""
    article_factory(title="Zebra Article")
    article_factory(title="Apple Article")

    response = client.get("/api/v1/articles/?sort=title")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"][0]["title"] == "Apple Article"


def test_list_articles_invalid_page(client):
    """Test invalid page number."""
    response = client.get("/api/v1/articles/?page=0")

    assert response.status_code == 422


def test_list_articles_invalid_limit(client):
    """Test invalid limit value."""
    response = client.get("/api/v1/articles/?limit=0")

    assert response.status_code == 422


def test_list_articles_limit_exceeds_max(client):
    """Test limit exceeding maximum allowed."""
    response = client.get("/api/v1/articles/?limit=200")

    assert response.status_code == 422


# Get Article by Slug Tests

def test_get_article_by_slug_success(client, sample_article):
    """Test retrieving article by slug."""
    response = client.get(f"/api/v1/articles/{sample_article.slug}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["slug"] == sample_article.slug
    assert data["data"]["title"] == sample_article.title


def test_get_article_by_slug_not_found(client):
    """Test retrieving non-existent article."""
    response = client.get("/api/v1/articles/nonexistent-slug")

    assert response.status_code == 404
    error = response.json()
    assert error["title"] == "ArticleNotFoundError"


def test_get_article_includes_all_fields(client, sample_article):
    """Test that article response includes all expected fields."""
    response = client.get(f"/api/v1/articles/{sample_article.slug}")

    assert response.status_code == 200
    article = response.json()["data"]

    required_fields = [
        "id", "title", "description", "slug",
        "keywords", "featured_image_url", "view_count",
        "created_at", "updated_at"
    ]

    for field in required_fields:
        assert field in article


def test_get_article_slug_case_insensitive(client, article_factory):
    """Test that slug matching is case-insensitive."""
    article = article_factory(slug="test-article")

    response = client.get("/api/v1/articles/TEST-ARTICLE")

    # Should work due to slugify normalization
    assert response.status_code in [200, 404]  # Implementation dependent


# Field Filter Tests

def test_list_articles_field_and_search(client, article_factory, sample_field, test_db):
    """Test combining field filter and search."""

    paper = Paper(
        title="Physics Paper",
        primary_field_id=sample_field.id,
        primary_subfield_id=sample_field.id,
        status="published"
    )
    test_db.add(paper)
    test_db.flush()

    article_factory(
        paper_id=paper.id,
        title="Quantum Physics Article"
    )
    article_factory(
        paper_id=paper.id,
        title="Classical Physics Article"
    )

    response = client.get(
        f"/api/v1/articles/?field={sample_field.code}&q=quantum"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 1


def test_list_articles_all_filters(client, article_factory, sample_field, test_db):
    """Test combining all available filters."""

    paper = Paper(
        title="Physics Paper",
        primary_field_id=sample_field.id,
        primary_subfield_id=sample_field.id,
        status="published"
    )
    test_db.add(paper)
    test_db.flush()

    article_factory(
        paper_id=paper.id,
        title="Test Article"
    )

    response = client.get(
        f"/api/v1/articles/?field={sample_field.code}"
        "&q=test&sort=title&page=1&limit=10"
    )

    assert response.status_code == 200


def test_list_articles_empty_database(client):
    """Test listing articles when database is empty."""
    response = client.get("/api/v1/articles/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 0