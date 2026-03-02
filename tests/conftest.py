import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db

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
    """Combined app (main.py) — all routes."""
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def v1_client():
    """V1 app (main_v1.py) — support-desk routes only."""
    from main_v1 import app as v1_app
    v1_app.dependency_overrides[get_db] = override_get_db
    with TestClient(v1_app) as c:
        yield c
    v1_app.dependency_overrides.clear()


@pytest.fixture
def v3_client():
    """V3 app (main_v3.py) — diagnostics routes only."""
    from main_v3 import app as v3_app
    v3_app.dependency_overrides[get_db] = override_get_db
    with TestClient(v3_app) as c:
        yield c
    v3_app.dependency_overrides.clear()


# --- Create users via the API so they go through the same DB session ---

def _register(client, email, username, password, role="customer"):
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "role": role,
    })
    assert resp.status_code == 201, f"Registration failed: {resp.json()}"
    return resp.json()


def _login(client, email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["access_token"]


@pytest.fixture
def admin_user(client):
    return _register(client, "admin@test.com", "admin", "admin123", "admin")


@pytest.fixture
def agent_user(client):
    return _register(client, "agent@test.com", "agent", "agent123", "agent")


@pytest.fixture
def customer_user(client):
    return _register(client, "customer@test.com", "customer", "customer123", "customer")


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
