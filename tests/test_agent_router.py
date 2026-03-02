"""Tests for the Health Check Agent v3.0 bidirectional API (agent_router.py)."""
import pytest
from tests.conftest import auth_header


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

def test_heartbeat_registers_new_device(client):
    resp = client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-001",
        "model": "MacBook Pro 16",
        "hostname": "test-mac",
        "os_version": "14.3",
        "agent_version": "3.0.0",
        "hardware_uuid": "uuid-001",
        "uptime_seconds": 3600,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["collection_interval"] == 300
    assert data["heartbeat_interval"] == 60
    assert data["pending_commands"] == 0
    assert data["server_time"] != ""


def test_heartbeat_updates_existing_device(client):
    # First heartbeat — register
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-002", "model": "MacBook Air", "hostname": "air",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-002",
    })
    # Second heartbeat — update
    resp = client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-002", "model": "MacBook Air M3", "hostname": "air-m3",
        "os_version": "14.4", "agent_version": "3.1.0", "hardware_uuid": "uuid-002",
    })
    assert resp.status_code == 200
    # Verify the update is reflected in device list
    devices = client.get("/api/v1/agent/devices").json()
    dev = next(d for d in devices if d["serial"] == "TEST-002")
    assert dev["model"] == "MacBook Air M3"
    assert dev["agent_version"] == "3.1.0"


# ---------------------------------------------------------------------------
# Collection upload
# ---------------------------------------------------------------------------

def test_upload_collection(client):
    # Register device first
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-003", "model": "iMac", "hostname": "imac",
        "os_version": "14.2", "agent_version": "3.0.0", "hardware_uuid": "uuid-003",
    })
    resp = client.post("/api/v1/agent/upload", json={
        "agent_version": "3.0.0",
        "collection_type": "lite",
        "timestamp": "2026-03-02T10:00:00",
        "device": {"serial": "TEST-003", "model": "iMac"},
        "battery": {"percentage": 85},
        "storage": {"used_pct": 45},
        "memory": {"pressure_pct": 30},
        "cpu": {"usage_pct": 15},
        "security": {"firewall": "enabled", "filevault": "on"},
        "network": {},
        "errors": {},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["alerts"] == []


def test_upload_triggers_alerts(client):
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-004", "model": "Mac Mini", "hostname": "mini",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-004",
    })
    resp = client.post("/api/v1/agent/upload", json={
        "agent_version": "3.0.0",
        "collection_type": "lite",
        "device": {"serial": "TEST-004"},
        "battery": {"percentage": 5},
        "storage": {"used_pct": 95},
        "memory": {"pressure_pct": 90},
        "cpu": {},
        "security": {"firewall": "disabled", "filevault": "off"},
        "network": {},
        "errors": {},
    })
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    categories = [a["category"] for a in alerts]
    assert "battery" in categories
    assert "storage" in categories
    assert "memory" in categories
    assert "security" in categories
    assert len(alerts) >= 4


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def test_create_and_poll_commands(client):
    # Register device
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-005", "model": "MacBook", "hostname": "mb",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-005",
    })
    # Create command
    resp = client.post("/api/v1/agent/commands", json={
        "serial": "TEST-005", "type": "collect_full", "payload": "",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    cmd_id = data["command_id"]

    # Heartbeat should now show pending_commands=1
    hb = client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-005", "model": "MacBook", "hostname": "mb",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-005",
    }).json()
    assert hb["pending_commands"] == 1

    # Agent polls for commands — should get 1 and clear queue
    poll = client.get("/api/v1/agent/commands/TEST-005")
    assert poll.status_code == 200
    cmds = poll.json()
    assert len(cmds) == 1
    assert cmds[0]["type"] == "collect_full"

    # Polling again should be empty
    poll2 = client.get("/api/v1/agent/commands/TEST-005")
    assert poll2.json() == []

    # Report result
    result_resp = client.post("/api/v1/agent/command-result", json={
        "command_id": cmd_id, "serial": "TEST-005", "status": "success",
        "result": "Full collection completed", "duration_seconds": 12,
        "timestamp": "2026-03-02T10:05:00",
    })
    assert result_resp.status_code == 200

    # Retrieve results
    results = client.get("/api/v1/agent/devices/TEST-005/command-results").json()
    assert len(results["results"]) == 1
    assert results["results"][0]["status"] == "success"


def test_create_command_unknown_device(client):
    resp = client.post("/api/v1/agent/commands", json={
        "serial": "NONEXISTENT", "type": "collect_lite",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Device listing + detail
# ---------------------------------------------------------------------------

def test_list_devices(client):
    """The agent uses in-memory state so previous tests may have registered devices."""
    resp = client.get("/api/v1/agent/devices")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_device_not_found(client):
    resp = client.get("/api/v1/agent/devices/NONEXISTENT")
    assert resp.status_code == 404


def test_get_device_detail(client):
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-006", "model": "Mac Pro", "hostname": "pro",
        "os_version": "14.5", "agent_version": "3.0.0", "hardware_uuid": "uuid-006",
    })
    resp = client.get("/api/v1/agent/devices/TEST-006")
    assert resp.status_code == 200
    dev = resp.json()
    assert dev["serial"] == "TEST-006"
    assert dev["model"] == "Mac Pro"
    assert dev["online"] is True


# ---------------------------------------------------------------------------
# Collections history
# ---------------------------------------------------------------------------

def test_get_collections(client):
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-007", "model": "iMac", "hostname": "imac",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-007",
    })
    # Upload 2 collections
    for i in range(2):
        client.post("/api/v1/agent/upload", json={
            "agent_version": "3.0.0", "collection_type": "lite",
            "device": {"serial": "TEST-007"}, "battery": {}, "storage": {},
            "memory": {}, "cpu": {}, "security": {}, "network": {}, "errors": {},
        })
    resp = client.get("/api/v1/agent/devices/TEST-007/collections")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


def test_get_collections_device_not_found(client):
    resp = client.get("/api/v1/agent/devices/NONEXISTENT/collections")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Device config
# ---------------------------------------------------------------------------

def test_update_device_config(client):
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-008", "model": "MacBook", "hostname": "mb",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-008",
    })
    resp = client.post("/api/v1/agent/devices/TEST-008/config", json={
        "collection_interval": 120,
        "heartbeat_interval": 45,
    })
    assert resp.status_code == 200
    assert resp.json()["config"]["collection_interval"] == 120
    assert resp.json()["config"]["heartbeat_interval"] == 45

    # Verify heartbeat returns new interval
    hb = client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-008", "model": "MacBook", "hostname": "mb",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-008",
    }).json()
    assert hb["collection_interval"] == 120


def test_update_config_min_interval_rejected(client):
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-009", "model": "Mac", "hostname": "m",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-009",
    })
    resp = client.post("/api/v1/agent/devices/TEST-009/config", json={
        "collection_interval": 10,
    })
    assert resp.status_code == 400


def test_update_config_device_not_found(client):
    resp = client.post("/api/v1/agent/devices/NONEXISTENT/config", json={
        "collection_interval": 120,
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Agent API status
# ---------------------------------------------------------------------------

def test_agent_status(client):
    # Register a device
    client.post("/api/v1/agent/heartbeat", json={
        "serial": "TEST-010", "model": "Mac", "hostname": "m",
        "os_version": "14.0", "agent_version": "3.0.0", "hardware_uuid": "uuid-010",
    })
    resp = client.get("/api/v1/agent/status")
    assert resp.status_code == 200
    stats = resp.json()["stats"]
    assert stats["total_devices"] >= 1
    assert stats["online_devices"] >= 1
