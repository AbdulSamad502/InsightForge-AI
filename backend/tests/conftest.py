"""
Shared test fixtures for the entire test suite.
Uses SQLite in-memory database — no PostgreSQL needed for tests.
"""
import os
import pytest
import tempfile
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment BEFORE importing app
os.environ["DATABASE_URL"]            = "sqlite://"
os.environ["SECRET_KEY"]              = "test-secret-key-for-testing-only"
os.environ["ALGORITHM"]               = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"
os.environ["GROQ_API_KEY"]            = "test-groq-key"
os.environ["GROQ_MAIN_MODEL"]         = "llama-3.3-70b-versatile"
os.environ["GROQ_FAST_MODEL"]         = "llama-3.1-8b-instant"
os.environ["LANGCHAIN_TRACING_V2"]    = "false"
os.environ["LANGCHAIN_API_KEY"]       = "test-langsmith-key"
os.environ["LANGCHAIN_PROJECT"]       = "test"
os.environ["MAX_UPLOAD_SIZE_MB"]      = "50"
os.environ["ALLOWED_EXTENSIONS"]      = "csv,xlsx"
os.environ["STORAGE_PATH"]            = "./test_storage"
os.environ["ENVIRONMENT"]             = "test"
os.environ["DEBUG"]                   = "false"
os.environ["GROQ_API_KEYS"]           = ""

from app.core.database import Base, get_db
from app.main import app


# ── In-memory SQLite engine ────────────────────────────────
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override FastAPI dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def create_tables():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield


@pytest.fixture
def db():
    """Fresh DB session for each test."""
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    """FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_csv_bytes() -> bytes:
    """A small, valid CSV file as bytes."""
    df = pd.DataFrame({
        "product":    ["Laptop", "Phone", "Chair", "Desk", "Headphones"],
        "category":  ["Electronics", "electronics", "Furniture", "Furniture", "Electronics"],
        "revenue":   [45000.0, 25000.0, None, 12000.0, 3500.0],
        "quantity":  [2, 5, 3, 1, -1],
        "order_date": ["2024-01-15", "2024-01-16", "not-a-date", "2024-01-18", "2024-01-19"],
    })
    return df.to_csv(index=False).encode("utf-8")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A small DataFrame for unit tests."""
    return pd.DataFrame({
        "product":    ["Laptop", "Phone", "Chair", "Desk", "Headphones"],
        "category":  ["Electronics", "electronics", "Furniture", "Furniture", "Electronics"],
        "revenue":   [45000.0, 25000.0, None, 12000.0, 3500.0],
        "quantity":  [2, 5, 3, 1, -1],
        "order_date": ["2024-01-15", "2024-01-16", "not-a-date", "2024-01-18", "2024-01-19"],
    })


@pytest.fixture
def registered_user(client) -> dict:
    """Register a test user and return the response data."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password": "testpass123",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_token(registered_user) -> str:
    """Return a valid JWT token for the test user."""
    return registered_user["access_token"]


@pytest.fixture
def auth_headers(auth_token) -> dict:
    """Return auth headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}