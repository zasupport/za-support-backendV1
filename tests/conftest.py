import os

# Set required env vars BEFORE any app imports
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("ALLOWED_ORIGINS", "*")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import User, UserRole
from app.auth import hash_password

# In-memory SQLite for tests — no PostgreSQL needed
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Helpers ---

def _register(client, email, username, password):
    """Register a user via the API (always creates customer)."""
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
    })
    assert resp.status_code == 201, f"Registration failed: {resp.json()}"
    return resp.json()


def _login(client, email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["access_token"]


def _create_user_with_role(email, username, password, role):
    """Create a user directly in the test DB with a specific role."""
    db = TestingSessionLocal()
    try:
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "email": user.email, "username": user.username, "role": user.role.value}
    finally:
        db.close()


@pytest.fixture
def admin_user(client):
    return _create_user_with_role("admin@test.com", "admin", "admin123", UserRole.admin)


@pytest.fixture
def agent_user(client):
    return _create_user_with_role("agent@test.com", "agent", "agent123", UserRole.agent)


@pytest.fixture
def customer_user(client):
    return _register(client, "customer@test.com", "customer", "customer123")


@pytest.fixture
def admin_token(client, admin_user):
    return _login(client, "admin@test.com", "admin123")


@pytest.fixture
def agent_token(client, agent_user):
    return _login(client, "agent@test.com", "agent123")


@pytest.fixture
def customer_token(client, customer_user):
    return _login(client, "customer@test.com", "customer123")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
