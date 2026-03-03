"""Tests for the scheduler and alert store (scheduler.py) — DB-backed."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.services.networking_scheduler import AlertStore, ISPMonitorScheduler
from app.services.detection_engine import OutageCorrelator, OutageStatus


@pytest.fixture
def db_session_factory():
    """Create a fresh in-memory SQLite DB for each test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def store(db_session_factory):
    return AlertStore(session_factory=db_session_factory)


# ---------------------------------------------------------------------------
# AlertStore
# ---------------------------------------------------------------------------

def test_alert_store_add_and_get(store):
    store.add("afrihost", {"severity": "critical", "old_status": "operational", "new_status": "full_outage"})
    store.add("afrihost", {"severity": "resolved", "old_status": "full_outage", "new_status": "operational"})
    alerts = store.get("afrihost")
    assert len(alerts) == 2


def test_alert_store_get_empty(store):
    assert store.get("nonexistent") == []


def test_alert_store_get_all(store):
    store.add("afrihost", {"severity": "critical", "old_status": "op", "new_status": "fo"})
    store.add("rain", {"severity": "warning", "old_status": "op", "new_status": "deg"})
    all_alerts = store.get_all()
    assert len(all_alerts) == 2


def test_alert_store_count(store):
    store.add("afrihost", {"severity": "critical", "old_status": "a", "new_status": "b"})
    store.add("afrihost", {"severity": "resolved", "old_status": "b", "new_status": "a"})
    store.add("rain", {"severity": "warning", "old_status": "a", "new_status": "c"})
    assert store.count() == 3


def test_alert_store_respects_max(store):
    """DB store keeps all rows — get() limit caps the return."""
    for i in range(5):
        store.add("afrihost", {"severity": "info", "old_status": "a", "new_status": "b"})
    assert store.count() == 5
    # Default limit=50, so all 5 returned
    assert len(store.get("afrihost")) == 5
    # Explicit limit returns capped result
    assert len(store.get("afrihost", limit=3)) == 3


# ---------------------------------------------------------------------------
# ISPMonitorScheduler status
# ---------------------------------------------------------------------------

def test_scheduler_get_status(store):
    correlator = OutageCorrelator()
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


def test_scheduler_fire_alert(store):
    """Test the _fire_alert internal method directly."""
    correlator = OutageCorrelator()
    scheduler = ISPMonitorScheduler(
        manager=None,
        correlator=correlator,
        alert_store=store,
        interval_seconds=60,
    )

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


def test_scheduler_fire_alert_resolved(store):
    """When status returns to operational from outage -> resolved severity."""
    correlator = OutageCorrelator()
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
