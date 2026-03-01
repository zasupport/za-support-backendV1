from tests.conftest import auth_header


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_register_customer(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "username": "newuser",
        "password": "pass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "customer"


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "username": "user1", "password": "pass",
    })
    resp = client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "username": "user2", "password": "pass",
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_register_duplicate_username(client):
    client.post("/api/v1/auth/register", json={
        "email": "a@test.com", "username": "same", "password": "pass",
    })
    resp = client.post("/api/v1/auth/register", json={
        "email": "b@test.com", "username": "same", "password": "pass",
    })
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"]


def test_login_success(client, customer_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": "customer@test.com", "password": "customer123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, customer_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": "customer@test.com", "password": "wrong",
    })
    assert resp.status_code == 401


def test_get_me(client, customer_token):
    resp = client.get("/api/v1/auth/me", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "customer@test.com"


def test_get_me_no_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_list_users_as_admin(client, admin_token, customer_user):
    resp = client.get("/api/v1/auth/users", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_list_users_as_customer_forbidden(client, customer_token):
    resp = client.get("/api/v1/auth/users", headers=auth_header(customer_token))
    assert resp.status_code == 403
