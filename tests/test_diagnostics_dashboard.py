from tests.conftest import auth_header


def test_diagnostics_full(client):
    resp = client.get("/api/v1/diagnostics/")
    assert resp.status_code == 200
    data = resp.json()
    assert "database" in data
    assert "system" in data
    assert "application" in data


def test_diagnostics_db(client):
    resp = client.get("/api/v1/diagnostics/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "connected"
    assert "tables" in data


def test_diagnostics_system(client):
    resp = client.get("/api/v1/diagnostics/system")
    assert resp.status_code == 200
    data = resp.json()
    assert "python_version" in data
    assert "platform" in data


def test_dashboard_as_admin(client, admin_token):
    resp = client.get("/api/v1/dashboard/stats", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "tickets" in data
    assert "chat" in data
    assert "monitoring" in data


def test_dashboard_as_customer(client, customer_token):
    resp = client.get("/api/v1/dashboard/stats", headers=auth_header(customer_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "my_tickets" in data
    assert "my_chats" in data


def test_dashboard_no_auth(client):
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 401
