from tests.conftest import auth_header


def test_create_ticket(client, customer_token):
    resp = client.post("/api/v1/tickets/", json={
        "subject": "Login broken",
        "description": "Cannot log in to dashboard",
        "priority": "high",
    }, headers=auth_header(customer_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject"] == "Login broken"
    assert data["status"] == "open"
    assert data["priority"] == "high"


def test_list_tickets_customer_sees_own(client, customer_token, admin_token):
    # Customer creates a ticket
    client.post("/api/v1/tickets/", json={
        "subject": "My issue", "description": "Details",
    }, headers=auth_header(customer_token))

    # Customer sees only their ticket
    resp = client.get("/api/v1/tickets/", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Admin sees all tickets
    resp = client.get("/api/v1/tickets/", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_ticket(client, customer_token):
    create = client.post("/api/v1/tickets/", json={
        "subject": "Test", "description": "Desc",
    }, headers=auth_header(customer_token))
    ticket_id = create.json()["id"]

    resp = client.get(f"/api/v1/tickets/{ticket_id}", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert resp.json()["subject"] == "Test"


def test_update_ticket_as_admin(client, customer_token, admin_token):
    create = client.post("/api/v1/tickets/", json={
        "subject": "Bug", "description": "Broken",
    }, headers=auth_header(customer_token))
    ticket_id = create.json()["id"]

    resp = client.put(f"/api/v1/tickets/{ticket_id}", json={
        "status": "in_progress",
    }, headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_customer_cannot_change_status(client, customer_token):
    create = client.post("/api/v1/tickets/", json={
        "subject": "Bug", "description": "Desc",
    }, headers=auth_header(customer_token))
    ticket_id = create.json()["id"]

    resp = client.put(f"/api/v1/tickets/{ticket_id}", json={
        "status": "closed",
    }, headers=auth_header(customer_token))
    assert resp.status_code == 403


def test_delete_ticket_as_admin(client, customer_token, admin_token):
    create = client.post("/api/v1/tickets/", json={
        "subject": "Delete me", "description": "Desc",
    }, headers=auth_header(customer_token))
    ticket_id = create.json()["id"]

    resp = client.delete(f"/api/v1/tickets/{ticket_id}", headers=auth_header(admin_token))
    assert resp.status_code == 204


def test_customer_cannot_delete(client, customer_token):
    create = client.post("/api/v1/tickets/", json={
        "subject": "No delete", "description": "Desc",
    }, headers=auth_header(customer_token))
    ticket_id = create.json()["id"]

    resp = client.delete(f"/api/v1/tickets/{ticket_id}", headers=auth_header(customer_token))
    assert resp.status_code == 403


def test_filter_tickets_by_status(client, customer_token):
    client.post("/api/v1/tickets/", json={
        "subject": "Open one", "description": "Desc",
    }, headers=auth_header(customer_token))

    resp = client.get("/api/v1/tickets/?status=open", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert all(t["status"] == "open" for t in resp.json())

    resp = client.get("/api/v1/tickets/?status=closed", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 0
