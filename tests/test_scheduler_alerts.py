"""Tests for the scheduler and alert store (scheduler.py)."""
import pytest
from scheduler import AlertStore, ISPMonitorScheduler
from detection_engine import OutageCorrelator, OutageStatus


# ---------------------------------------------------------------------------
# AlertStore
# ---------------------------------------------------------------------------

def test_alert_store_add_and_get():
    store = AlertStore()
    store.add("afrihost", {"severity": "critical", "timestamp": "2026-03-02T10:00:00"})
    store.add("afrihost", {"severity": "resolved", "timestamp": "2026-03-02T10:05:00"})
    alerts = store.get("afrihost")
    assert len(alerts) == 2


def test_alert_store_get_empty():
    store = AlertStore()
    assert store.get("nonexistent") == []


def test_alert_store_get_all():
    store = AlertStore()
    store.add("afrihost", {"severity": "critical", "timestamp": "2026-03-02T10:00:00"})
    store.add("rain", {"severity": "warning", "timestamp": "2026-03-02T10:01:00"})
    all_alerts = store.get_all()
    assert len(all_alerts) == 2


def test_alert_store_count():
    store = AlertStore()
    store.add("afrihost", {"severity": "critical", "timestamp": "t1"})
    store.add("afrihost", {"severity": "resolved", "timestamp": "t2"})
    store.add("rain", {"severity": "warning", "timestamp": "t3"})
    assert store.count() == 3


def test_alert_store_respects_max():
    store = AlertStore(max_per_isp=3)
    for i in range(5):
        store.add("afrihost", {"id": i, "timestamp": f"t{i}"})
    assert len(store.get("afrihost")) == 3
    # Should keep the last 3
    assert store.get("afrihost")[0]["id"] == 2


# ---------------------------------------------------------------------------
# ISPMonitorScheduler status
# ---------------------------------------------------------------------------

def test_scheduler_get_status():
    correlator = OutageCorrelator()
    store = AlertStore()
    # We can't instantiate a real manager without config, so just test status reporting
    scheduler = ISPMonitorScheduler(
        manager=None,
        correlator=correlator,
        alert_store=store,
        interval_seconds=60,
    )
    status = scheduler.get_status()
    assert status["running"] is False
    assert status["interval_seconds"] == 60
    assert status["cycles_completed"] == 0
    assert status["total_alerts"] == 0


def test_scheduler_fire_alert():
    """Test the _fire_alert internal method directly."""
    correlator = OutageCorrelator()
    store = AlertStore()
    scheduler = ISPMonitorScheduler(
        manager=None,
        correlator=correlator,
        alert_store=store,
        interval_seconds=60,
    )

    # Simulate status change
    determination = {
        "weighted_down_score": 4.5,
        "confirmed_down": 2,
        "down_methods": ["ripe_atlas", "http"],
    }
    scheduler._fire_alert("afrihost", "operational", "full_outage", determination)

    alerts = store.get("afrihost")
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "critical"
    assert alerts[0]["old_status"] == "operational"
    assert alerts[0]["new_status"] == "full_outage"


def test_scheduler_fire_alert_resolved():
    """When status returns to operational from outage → resolved severity."""
    correlator = OutageCorrelator()
    store = AlertStore()
    scheduler = ISPMonitorScheduler(
        manager=None,
        correlator=correlator,
        alert_store=store,
        interval_seconds=60,
    )

    determination = {"weighted_down_score": 0, "confirmed_down": 0, "down_methods": []}
    scheduler._fire_alert("rain", "full_outage", "operational", determination)

    alerts = store.get("rain")
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "resolved"
