# tests/conftest.py
import uuid
from datetime import datetime

import pytest
from app.api.deps import get_db
from app.db.base import Base
from app.main import create_app
from app.models.article import Article
from app.models.bookmark import Bookmark
from app.models.field import Field
from app.models.interest import UserFieldInterest
from app.models.paper import Paper
from app.models.role import Role, UserRole
from app.models.user import User
from app.shared.config import Settings
from app.shared.emails.email_client import EmailClient
from app.shared.emails.resend_client import get_email_client
from app.shared.security import hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container once for entire test session."""
    with PostgresContainer("postgres:16", driver="psycopg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def test_engine(postgres_container):
    """Create engine and initialize schema once per session."""
    engine = create_engine(postgres_container.get_connection_url())

    # Create ENUM types manually before creating tables
    with engine.begin() as conn:
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE prompt_type AS ENUM ('article', 'image', 'video', 'text-to-speech');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE block_type AS ENUM ('title', 'paragraph', 'subheading', 'quote', 'image');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Provide a clean database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(test_db, test_engine):
    """Create a test client with overridden dependencies."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    test_settings = Settings(
        database_url=str(test_engine.url),
        redis_url=None,
        enable_otel=False,
        cors_origins=["https://zara.com:5132", "http://localhost:3000"]
    )

    app = create_app(settings_override=test_settings)

    class _DummyEmailClient(EmailClient):
        def send(self, to, subject, html, text=None, from_=None) -> dict:
            return {"id": "test-email", "status": "queued"}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_client] = lambda: _DummyEmailClient()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_field(test_db):
    """Create a sample top-level field (Physics)."""
    field = Field(
        code="physics",
        name="Physics",
        sort_order=1,
        parent_id=None
    )
    test_db.add(field)
    test_db.commit()
    test_db.refresh(field)
    return field


@pytest.fixture
def sample_subfield(test_db, sample_field):
    """Create a sample subfield (Quantum Physics) under Physics."""
    subfield = Field(
        code="quant-ph",
        name="Quantum Physics",
        sort_order=1,
        parent_id=sample_field.id
    )
    test_db.add(subfield)
    test_db.commit()
    test_db.refresh(subfield)
    return subfield


@pytest.fixture
def sample_paper(test_db, sample_field, sample_subfield):
    """Create a sample paper with proper field references."""
    paper = Paper(
        id=uuid.uuid4(),
        title="Quantum Entanglement in Photonic Systems",
        abstract="This paper explores the applications of quantum entanglement "
                 "in scalable photonic systems for secure communications.",
        primary_field_id=sample_field.id,
        primary_subfield_id=sample_subfield.id,
        subjects=["Physics", "Quantum Mechanics", "Photonics"],
        categories=["quant-ph", "physics.optics"],
        status="published",
        published_date=datetime(2023, 5, 15),
    )
    test_db.add(paper)
    test_db.flush()
    return paper


@pytest.fixture
def sample_article(test_db, sample_paper):
    """Create a sample article - with unique slug."""
    article = Article(
        id=uuid.uuid4(),
        paper_id=sample_paper.id,
        title="Breakthrough in Quantum Networking",
        description="Researchers demonstrate entanglement distribution across "
                    "a metropolitan-scale photonic network.",
        slug=f"quantum-networking-{uuid.uuid4().hex[:8]}",
        status="published",
        keywords=["quantum", "networking", "entanglement", "photonics"],
        view_count=42,
        created_at=datetime(2023, 6, 1),
        updated_at=datetime(2023, 6, 1),
    )
    test_db.add(article)
    test_db.flush()
    return article


@pytest.fixture
def test_user(test_db):
    """Create a verified test user for authentication tests."""
    # Create reader role if it doesn't exist
    role = test_db.query(Role).filter_by(name="reader").one_or_none()
    if not role:
        role = Role(name="reader", description="Default reader role")
        test_db.add(role)
        test_db.flush()

    user = User(
        email="testuser@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        display_name="testuser",
        email_verified_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.flush()

    # Assign reader role
    user_role = UserRole(user_id=user.id, role_id=role.id)
    test_db.add(user_role)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def article_factory(test_db, sample_paper):
    """Factory for creating test articles with guaranteed unique slugs."""
    created_articles = []

    def _create_article(**kwargs):
        defaults = {
            "id": uuid.uuid4(),
            "paper_id": sample_paper.id,
            "title": f"Test Article {uuid.uuid4().hex[:8]}",
            "description": "Test description",
            "slug": f"test-{uuid.uuid4().hex[:12]}",
            "status": "published",
            "keywords": ["test"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        defaults.update(kwargs)

        article = Article(**defaults)
        test_db.add(article)
        test_db.flush()
        created_articles.append(article)
        return article

    yield _create_article


@pytest.fixture
def paper_factory(test_db, sample_field, sample_subfield):
    """Factory for creating test papers with proper field references."""
    created_papers = []

    def _create_paper(**kwargs):
        defaults = {
            "id": uuid.uuid4(),
            "title": f"Test Paper {uuid.uuid4().hex[:8]}",
            "primary_field_id": sample_field.id,
            "primary_subfield_id": sample_subfield.id,
            "subjects": ["Physics"],
            "status": "published",
            "published_date": datetime.utcnow(),
        }
        defaults.update(kwargs)

        paper = Paper(**defaults)
        test_db.add(paper)
        test_db.flush()
        created_papers.append(paper)
        return paper

    yield _create_paper


@pytest.fixture
def field_factory(test_db):
    """Factory for creating test fields."""
    created_fields = []

    def _create_field(**kwargs):
        defaults = {
            "code": f"test-{uuid.uuid4().hex[:8]}",
            "name": f"Test Field {uuid.uuid4().hex[:8]}",
            "parent_id": None,
            "sort_order": None,
        }
        defaults.update(kwargs)

        field = Field(**defaults)
        test_db.add(field)
        test_db.flush()
        created_fields.append(field)
        return field

    yield _create_field


@pytest.fixture
def bookmark_factory(test_db):
    """Factory for creating test bookmarks."""
    created_bookmarks = []

    def _create_bookmark(user_id, article_id):
        bookmark = Bookmark(
            user_id=user_id,
            article_id=article_id
        )
        test_db.add(bookmark)
        test_db.flush()
        created_bookmarks.append(bookmark)
        return bookmark

    yield _create_bookmark


@pytest.fixture
def interest_factory(test_db):
    """Factory for creating test user interests."""
    created_interests = []

    def _create_interest(user_id, field_id):
        interest = UserFieldInterest(
            user_id=user_id,
            field_id=field_id
        )
        test_db.add(interest)
        test_db.flush()
        created_interests.append(interest)
        return interest

    yield _create_interest


@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authentication cookie set for tests."""
    # Log in
    response = client.post("/api/v1/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 204

    # Now client has cookie stored
    return client
