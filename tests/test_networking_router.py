"""Tests for the ISP Networking Router (router_networking.py) and alert/scheduler endpoints."""
import pytest


# ---------------------------------------------------------------------------
# Provider info
# ---------------------------------------------------------------------------

def test_list_providers(client):
    resp = client.get("/api/v1/isp/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "master_enabled" in data
    assert "providers" in data
    for name in ("cloudflare_radar", "ioda", "ripe_atlas", "statuspage_api", "bgp_looking_glass", "webhook"):
        assert name in data["providers"]


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------

def test_register_webhook_secret(client):
    resp = client.post("/api/v1/isp/webhooks/afrihost/secret", json={
        "secret": "a" * 16,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_webhook_secret_too_short(client):
    resp = client.post("/api/v1/isp/webhooks/afrihost/secret", json={
        "secret": "short",
    })
    assert resp.status_code == 422  # validation error


def test_register_webhook_unknown_isp(client):
    resp = client.post("/api/v1/isp/webhooks/unknown_isp_xyz/secret", json={
        "secret": "a" * 16,
    })
    assert resp.status_code == 404


def test_receive_webhook(client):
    resp = client.post(
        "/api/v1/isp/webhooks/afrihost",
        json={"status": "down", "component": "fibre"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "webhook"
    assert data["isp"] == "afrihost"


def test_receive_webhook_unknown_isp(client):
    resp = client.post(
        "/api/v1/isp/webhooks/unknown_isp_xyz",
        json={"status": "up"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Per-ISP endpoints
# ---------------------------------------------------------------------------

def test_isp_components(client):
    resp = client.get("/api/v1/isp/isps/afrihost/components")
    assert resp.status_code == 200
    assert "components" in resp.json()


def test_isp_components_unknown(client):
    resp = client.get("/api/v1/isp/isps/unknown_isp_xyz/components")
    assert resp.status_code == 404


def test_isp_maintenance(client):
    resp = client.get("/api/v1/isp/isps/afrihost/maintenance")
    assert resp.status_code == 200
    assert "maintenance" in resp.json()


def test_isp_bgp_unknown(client):
    resp = client.get("/api/v1/isp/isps/unknown_isp_xyz/bgp")
    assert resp.status_code == 404


def test_isp_ioda_history(client):
    resp = client.get("/api/v1/isp/isps/afrihost/ioda-history?hours=1")
    assert resp.status_code == 200


def test_isp_ioda_history_unknown(client):
    resp = client.get("/api/v1/isp/isps/unknown_isp_xyz/ioda-history")
    assert resp.status_code == 404


def test_trigger_measurement(client):
    resp = client.post("/api/v1/isp/isps/afrihost/measure", json={
        "target": "8.8.8.8",
        "measurement_type": "ping",
    })
    # May return disabled_or_no_key in test env, but shouldn't 404
    assert resp.status_code == 200


def test_trigger_measurement_bad_type(client):
    resp = client.post("/api/v1/isp/isps/afrihost/measure", json={
        "target": "8.8.8.8",
        "measurement_type": "invalid_type",
    })
    assert resp.status_code == 400


def test_trigger_measurement_unknown_isp(client):
    resp = client.post("/api/v1/isp/isps/unknown_isp_xyz/measure", json={
        "target": "8.8.8.8",
    })
    assert resp.status_code == 404


def test_full_check_unknown_isp(client):
    resp = client.get("/api/v1/isp/isps/unknown_isp_xyz/full-check")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Correlation endpoints
# ---------------------------------------------------------------------------

def test_correlate_unknown_isp(client):
    resp = client.get("/api/v1/isp/isps/unknown_isp_xyz/correlate")
    assert resp.status_code == 404


def test_correlation_history_unknown_isp(client):
    resp = client.get("/api/v1/isp/isps/unknown_isp_xyz/correlation-history")
    assert resp.status_code == 404


def test_correlation_history_empty(client):
    resp = client.get("/api/v1/isp/isps/afrihost/correlation-history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["isp"] == "afrihost"
    assert isinstance(data["history"], list)


# ---------------------------------------------------------------------------
# Alert endpoints
# ---------------------------------------------------------------------------

def test_list_all_alerts_empty(client):
    resp = client.get("/api/v1/isp/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["alerts"], list)


def test_list_isp_alerts_empty(client):
    resp = client.get("/api/v1/isp/alerts/afrihost")
    assert resp.status_code == 200
    data = resp.json()
    assert data["isp"] == "afrihost"
    assert isinstance(data["alerts"], list)


def test_list_isp_alerts_unknown(client):
    resp = client.get("/api/v1/isp/alerts/unknown_isp_xyz")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Scheduler status
# ---------------------------------------------------------------------------

def test_scheduler_status(client):
    resp = client.get("/api/v1/isp/scheduler-status")
    assert resp.status_code == 200
    data = resp.json()
    # In test context the scheduler should be bound
    assert "running" in data
