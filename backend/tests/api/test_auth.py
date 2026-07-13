"""
API tests for the authentication module.
These test the full HTTP request/response cycle.
"""
import pytest


def test_register_success(client):
    """New user can register with valid data."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@test.com"
    assert data["user"]["full_name"] == "New User"
    assert "hashed_password" not in data["user"]


def test_register_duplicate_email(client, registered_user):
    """Cannot register with the same email twice."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",  # same as registered_user
            "full_name": "Another User",
            "password": "password123",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"] is True
    assert data["error_code"] == "USER_ALREADY_EXISTS"


def test_register_short_password(client):
    """Password shorter than 6 chars should be rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpass@test.com",
            "full_name": "User",
            "password": "abc",
        },
    )
    assert response.status_code == 422  # Pydantic validation error


def test_register_invalid_email(client):
    """Invalid email format should be rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "full_name": "User",
            "password": "password123",
        },
    )
    assert response.status_code == 422


def test_login_success(client, registered_user):
    """Registered user can login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"


def test_login_wrong_password(client, registered_user):
    """Wrong password returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] is True


def test_login_nonexistent_user(client):
    """Login with non-existent email returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@test.com",
            "password": "password123",
        },
    )
    assert response.status_code == 401


def test_get_me_with_valid_token(client, auth_headers):
    """GET /me returns user data with valid token."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "hashed_password" not in data


def test_get_me_with_invalid_token(client):
    """GET /me with invalid token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_get_me_without_token(client):
    """GET /me without any token returns 403."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]


def test_health_check(client):
    """Health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"