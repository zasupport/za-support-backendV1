"""
Verify that V1 and V3 entry points expose only their own routes.
"""
import pytest


class TestV1AppRoutes:
    """main_v1.py should serve V1 routes, NOT V3 health/network."""

    def test_root(self, v1_client):
        resp = v1_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "Full Health Check" in data["service"]
        assert "tickets" in data["endpoints"]
        assert "health_monitoring" not in data["endpoints"]

    def test_health_check(self, v1_client):
        resp = v1_client.get("/health")
        assert resp.status_code == 200
        assert "V1" in resp.json()["service"]

    def test_v1_has_tickets(self, v1_client):
        # Auth required, but route should exist (401, not 404)
        resp = v1_client.get("/api/v1/tickets")
        assert resp.status_code != 404

    def test_v1_has_chat(self, v1_client):
        resp = v1_client.get("/api/v1/chat/sessions")
        assert resp.status_code != 404

    def test_v1_has_dashboard(self, v1_client):
        resp = v1_client.get("/api/v1/dashboard/stats")
        assert resp.status_code != 404

    def test_v1_has_auth(self, v1_client):
        resp = v1_client.get("/api/v1/auth/me")
        assert resp.status_code != 404

    def test_v1_has_diagnostics(self, v1_client):
        resp = v1_client.get("/api/v1/diagnostics/")
        assert resp.status_code == 200

    def test_v1_no_health_route(self, v1_client):
        resp = v1_client.get("/api/v1/health/machines")
        assert resp.status_code == 404

    def test_v1_no_network_route(self, v1_client):
        resp = v1_client.get("/api/v1/network/controllers")
        assert resp.status_code == 404


class TestV3AppRoutes:
    """main_v3.py should serve V3 routes, NOT V1 tickets/chat/dashboard."""

    def test_root(self, v3_client):
        resp = v3_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "Diagnostics" in data["service"]
        assert "health_monitoring" in data["endpoints"]
        assert "tickets" not in data["endpoints"]

    def test_health_check(self, v3_client):
        resp = v3_client.get("/health")
        assert resp.status_code == 200
        assert "V3" in resp.json()["service"]

    def test_v3_has_health_route(self, v3_client):
        resp = v3_client.get("/api/v1/health/machines")
        assert resp.status_code != 404

    def test_v3_has_network_route(self, v3_client):
        resp = v3_client.get("/api/v1/network/controllers")
        assert resp.status_code != 404

    def test_v3_has_auth(self, v3_client):
        resp = v3_client.get("/api/v1/auth/me")
        assert resp.status_code != 404

    def test_v3_has_diagnostics(self, v3_client):
        resp = v3_client.get("/api/v1/diagnostics/")
        assert resp.status_code == 200

    def test_v3_no_tickets(self, v3_client):
        resp = v3_client.get("/api/v1/tickets")
        assert resp.status_code == 404

    def test_v3_no_chat(self, v3_client):
        resp = v3_client.get("/api/v1/chat/sessions")
        assert resp.status_code == 404

    def test_v3_no_dashboard(self, v3_client):
        resp = v3_client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 404
