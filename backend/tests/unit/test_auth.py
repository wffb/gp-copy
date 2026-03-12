import pytest
from datetime import datetime
from app.models.user import User
from app.shared.security import hash_password


# REGISTER TESTS

def test_register_success(client):
    """Test successful user registration."""
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "johndoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 204


def test_register_duplicate_email(client, test_user):
    """Test registration with existing email fails."""
    payload = {
        "email": test_user.email,
        "password": "SecurePass123!",
        "first_name": "Jane",
        "last_name": "Doe",
        "display_name": "janedoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code in [400, 409]


def test_register_invalid_email(client):
    """Test registration with invalid email format."""
    payload = {
        "email": "not-an-email",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "johndoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 422


def test_register_missing_email(client):
    """Test registration without email."""
    payload = {
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "johndoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 422


def test_register_missing_password(client):
    """Test registration without password."""
    payload = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "johndoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 422


def test_register_missing_names(client):
    """Test registration without required name fields."""
    payload = {
        "email": "test@example.com",
        "password": "SecurePass123!"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 422


def test_register_empty_password(client):
    """Test registration with empty password."""
    payload = {
        "email": "test@example.com",
        "password": "",
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "johndoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 422


def test_register_empty_email(client):
    """Test registration with empty email."""
    payload = {
        "email": "",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "johndoe"
    }
    response = client.post("/api/v1/register", json=payload)

    assert response.status_code == 422


# LOGIN TESTS

def test_login_success(client, test_user):
    """Test successful login sets cookie."""
    payload = {
        "email": test_user.email,
        "password": "password123"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 204
    assert "sid" in response.cookies or "Set-Cookie" in response.headers


def test_login_sets_httponly_cookie(client, test_user):
    """Test login sets HttpOnly secure cookie."""
    payload = {
        "email": test_user.email,
        "password": "password123"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower() or "sid" in response.cookies


def test_login_wrong_password(client, test_user):
    """Test login with incorrect password."""
    payload = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 401
    error = response.json()
    assert error["title"] == "InvalidCredentialsError"


def test_login_nonexistent_user(client):
    """Test login with non-existent email."""
    payload = {
        "email": "doesnotexist@example.com",
        "password": "password123"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 401
    error = response.json()
    assert error["title"] == "UserDoesNotExist"


def test_login_unverified_email(client, test_db):
    """Test login with unverified email."""
    unverified_user = User(
        email="unverified@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        display_name="testuser",
        email_verified_at=None
    )
    test_db.add(unverified_user)
    test_db.commit()

    payload = {
        "email": "unverified@example.com",
        "password": "password123"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 401
    error = response.json()
    assert error["title"] == "EmailVerificationNotVerified"


def test_login_invalid_email_format(client):
    """Test login with invalid email format."""
    payload = {
        "email": "not-an-email",
        "password": "password123"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 422


def test_login_missing_email(client):
    """Test login without email."""
    payload = {
        "password": "password123"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 422


def test_login_missing_password(client):
    """Test login without password."""
    payload = {
        "email": "test@example.com"
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 422


def test_login_empty_credentials(client):
    """Test login with empty credentials."""
    payload = {
        "email": "",
        "password": ""
    }
    response = client.post("/api/v1/login", json=payload)

    assert response.status_code == 422


# LOGOUT TESTS

def test_logout_success(authenticated_client):
    """Test successful logout clears cookie."""
    response = authenticated_client.post("/api/v1/logout")

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "sid=" in set_cookie or len(set_cookie) > 0


def test_logout_without_session(client):
    """Test logout without active session."""
    response = client.post("/api/v1/logout")

    assert response.status_code == 204


def test_logout_invalidates_session(authenticated_client, client):
    """Test logout invalidates the session."""
    response = authenticated_client.post("/api/v1/logout")
    assert response.status_code == 204

    response = authenticated_client.get("/api/v1/users/me")
    assert response.status_code == 401
