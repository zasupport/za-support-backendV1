from app.config import API_KEY

API_HEADER = {"X-API-Key": API_KEY}


def test_submit_health_data(client):
    resp = client.post("/api/v1/health/submit", json={
        "machine_id": "machine-001",
        "cpu_percent": 45.2,
        "memory_percent": 62.1,
        "disk_percent": 78.0,
        "battery_percent": 85.0,
        "threat_score": 2,
        "raw_data": {"os": "Windows 11"},
    }, headers=API_HEADER)
    assert resp.status_code == 201
    assert resp.json()["status"] == "success"


def test_submit_health_bad_api_key(client):
    resp = client.post("/api/v1/health/submit", json={
        "machine_id": "machine-001",
        "cpu_percent": 10.0, "memory_percent": 20.0,
        "disk_percent": 30.0, "threat_score": 0,
        "raw_data": {},
    }, headers={"X-API-Key": "wrong_key"})
    assert resp.status_code == 401


def test_get_latest_health(client):
    client.post("/api/v1/health/submit", json={
        "machine_id": "m1", "cpu_percent": 10.0, "memory_percent": 20.0,
        "disk_percent": 30.0, "threat_score": 1, "raw_data": {},
    }, headers=API_HEADER)

    client.post("/api/v1/health/submit", json={
        "machine_id": "m1", "cpu_percent": 90.0, "memory_percent": 80.0,
        "disk_percent": 70.0, "threat_score": 8, "raw_data": {},
    }, headers=API_HEADER)

    resp = client.get("/api/v1/health/latest/m1", headers=API_HEADER)
    assert resp.status_code == 200
    assert resp.json()["cpu_percent"] == 90.0


def test_get_latest_health_no_api_key(client):
    """GET endpoints now require API key."""
    client.post("/api/v1/health/submit", json={
        "machine_id": "m1", "cpu_percent": 10.0, "memory_percent": 20.0,
        "disk_percent": 30.0, "threat_score": 1, "raw_data": {},
    }, headers=API_HEADER)

    resp = client.get("/api/v1/health/latest/m1")
    assert resp.status_code == 422  # missing required header


def test_get_health_history(client):
    for i in range(5):
        client.post("/api/v1/health/submit", json={
            "machine_id": "m2", "cpu_percent": float(i * 10),
            "memory_percent": 50.0, "disk_percent": 50.0,
            "threat_score": i, "raw_data": {},
        }, headers=API_HEADER)

    resp = client.get("/api/v1/health/history/m2?limit=3", headers=API_HEADER)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_list_machines(client):
    client.post("/api/v1/health/submit", json={
        "machine_id": "pc-1", "cpu_percent": 10.0, "memory_percent": 20.0,
        "disk_percent": 30.0, "threat_score": 0, "raw_data": {},
    }, headers=API_HEADER)

    resp = client.get("/api/v1/health/machines", headers=API_HEADER)
    assert resp.status_code == 200
    machines = resp.json()
    assert any(m["machine_id"] == "pc-1" for m in machines)


def test_health_not_found(client):
    resp = client.get("/api/v1/health/latest/nonexistent", headers=API_HEADER)
    assert resp.status_code == 404


# --- Network ---

def test_submit_network_data(client):
    resp = client.post("/api/v1/network/submit", json={
        "controller_id": "ctrl-001",
        "total_clients": 42,
        "total_devices": 15,
        "raw_data": {"site": "main-office"},
    }, headers=API_HEADER)
    assert resp.status_code == 201
    assert resp.json()["status"] == "success"


def test_get_latest_network(client):
    client.post("/api/v1/network/submit", json={
        "controller_id": "c1", "total_clients": 10,
        "total_devices": 5, "raw_data": {},
    }, headers=API_HEADER)

    resp = client.get("/api/v1/network/latest/c1", headers=API_HEADER)
    assert resp.status_code == 200
    assert resp.json()["total_clients"] == 10


def test_get_network_history(client):
    for i in range(4):
        client.post("/api/v1/network/submit", json={
            "controller_id": "c2", "total_clients": i * 5,
            "total_devices": i, "raw_data": {},
        }, headers=API_HEADER)

    resp = client.get("/api/v1/network/history/c2?limit=2", headers=API_HEADER)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_controllers(client):
    client.post("/api/v1/network/submit", json={
        "controller_id": "ctrl-main", "total_clients": 100,
        "total_devices": 20, "raw_data": {},
    }, headers=API_HEADER)

    resp = client.get("/api/v1/network/controllers", headers=API_HEADER)
    assert resp.status_code == 200
    assert any(c["controller_id"] == "ctrl-main" for c in resp.json())


def test_network_not_found(client):
    resp = client.get("/api/v1/network/latest/nonexistent", headers=API_HEADER)
    assert resp.status_code == 404
