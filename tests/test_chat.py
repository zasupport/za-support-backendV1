from tests.conftest import auth_header


def test_create_chat_session(client, customer_token):
    resp = client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["agent_id"] is None


def test_create_session_linked_to_ticket(client, customer_token):
    ticket = client.post("/api/v1/tickets/", json={
        "subject": "Help", "description": "Need help",
    }, headers=auth_header(customer_token))
    ticket_id = ticket.json()["id"]

    resp = client.post("/api/v1/chat/sessions", json={
        "ticket_id": ticket_id,
    }, headers=auth_header(customer_token))
    assert resp.status_code == 201
    assert resp.json()["ticket_id"] == ticket_id


def test_list_sessions(client, customer_token):
    client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))

    resp = client.get("/api/v1/chat/sessions", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_agent_joins_session(client, customer_token, agent_token):
    session = client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    session_id = session.json()["id"]

    resp = client.post(f"/api/v1/chat/sessions/{session_id}/join", headers=auth_header(agent_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "joined"


def test_customer_cannot_join_session(client, customer_token):
    session = client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    session_id = session.json()["id"]

    resp = client.post(f"/api/v1/chat/sessions/{session_id}/join", headers=auth_header(customer_token))
    assert resp.status_code == 403


def test_send_and_get_messages(client, customer_token):
    session = client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    session_id = session.json()["id"]

    # Send a message
    resp = client.post(f"/api/v1/chat/sessions/{session_id}/messages", json={
        "content": "Hello, I need help!",
    }, headers=auth_header(customer_token))
    assert resp.status_code == 201
    assert resp.json()["content"] == "Hello, I need help!"

    # Get messages (includes system message from session creation + our message)
    resp = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_header(customer_token))
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) >= 2
    assert any(m["content"] == "Hello, I need help!" for m in messages)


def test_close_session(client, customer_token):
    session = client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    session_id = session.json()["id"]

    resp = client.post(f"/api/v1/chat/sessions/{session_id}/close", headers=auth_header(customer_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


def test_cannot_message_closed_session(client, customer_token):
    session = client.post("/api/v1/chat/sessions", json={}, headers=auth_header(customer_token))
    session_id = session.json()["id"]

    client.post(f"/api/v1/chat/sessions/{session_id}/close", headers=auth_header(customer_token))

    resp = client.post(f"/api/v1/chat/sessions/{session_id}/messages", json={
        "content": "This should fail",
    }, headers=auth_header(customer_token))
    assert resp.status_code == 400
    assert "closed" in resp.json()["detail"]
