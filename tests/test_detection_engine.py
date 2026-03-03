"""Tests for the ISP Outage Detection Engine (detection_engine.py)."""
from app.services.detection_engine import (
    CheckMethod,
    CheckResult,
    OutageCorrelator,
    OutageStatus,
    METHOD_WEIGHTS,
)


# ---------------------------------------------------------------------------
# CheckResult basics
# ---------------------------------------------------------------------------

def test_check_result_to_dict():
    cr = CheckResult(method=CheckMethod.HTTP, is_down=True, confidence=0.8, details="timeout")
    d = cr.to_dict()
    assert d["method"] == "http"
    assert d["is_down"] is True
    assert d["confidence"] == 0.8
    assert d["weight"] == METHOD_WEIGHTS[CheckMethod.HTTP]


def test_check_result_clamps_confidence():
    cr = CheckResult(method=CheckMethod.PING, is_down=False, confidence=2.5)
    assert cr.confidence == 1.0
    cr2 = CheckResult(method=CheckMethod.PING, is_down=False, confidence=-1.0)
    assert cr2.confidence == 0.0


# ---------------------------------------------------------------------------
# Correlator — operational
# ---------------------------------------------------------------------------

def test_correlate_no_checks():
    c = OutageCorrelator()
    result = c.correlate("afrihost", [])
    assert result["status"] == OutageStatus.OPERATIONAL
    assert result["total_checks"] == 0


def test_correlate_all_up():
    c = OutageCorrelator()
    checks = [
        CheckResult(method=CheckMethod.HTTP, is_down=False, confidence=1.0),
        CheckResult(method=CheckMethod.PING, is_down=False, confidence=1.0),
        CheckResult(method=CheckMethod.CLOUDFLARE_RADAR, is_down=False, confidence=1.0),
    ]
    result = c.correlate("afrihost", checks)
    assert result["status"] == OutageStatus.OPERATIONAL
    assert result["weighted_down_score"] == 0
    assert result["confirmed_down"] == 0


# ---------------------------------------------------------------------------
# Correlator — degraded
# ---------------------------------------------------------------------------

def test_correlate_degraded():
    """Single weight-2 down signal → score=2 → DEGRADED."""
    c = OutageCorrelator()
    checks = [
        CheckResult(method=CheckMethod.CLOUDFLARE_RADAR, is_down=True, confidence=1.0),
        CheckResult(method=CheckMethod.PING, is_down=False, confidence=1.0),
    ]
    result = c.correlate("rain", checks)
    assert result["status"] == OutageStatus.DEGRADED
    assert result["weighted_down_score"] == 2.0


# ---------------------------------------------------------------------------
# Correlator — full outage
# ---------------------------------------------------------------------------

def test_correlate_full_outage_by_score():
    """Weight >= 4 + confirmed >= 1 → FULL_OUTAGE."""
    c = OutageCorrelator()
    checks = [
        CheckResult(method=CheckMethod.RIPE_ATLAS, is_down=True, confidence=1.0),  # weight 3
        CheckResult(method=CheckMethod.HTTP, is_down=True, confidence=1.0),          # weight 1
    ]
    result = c.correlate("telkom", checks)
    assert result["status"] == OutageStatus.FULL_OUTAGE
    assert result["weighted_down_score"] == 4.0


def test_correlate_full_outage_by_bgp_drop():
    """BGP drop + any confirmation → FULL_OUTAGE regardless of score."""
    c = OutageCorrelator()
    checks = [
        CheckResult(method=CheckMethod.BGP_LOOKING_GLASS, is_down=True, confidence=1.0),  # weight 2
        CheckResult(method=CheckMethod.HTTP, is_down=True, confidence=1.0),                 # weight 1
    ]
    result = c.correlate("mtn", checks)
    assert result["status"] == OutageStatus.FULL_OUTAGE
    assert result["bgp_drop"] is True


# ---------------------------------------------------------------------------
# Correlator — partial outage
# ---------------------------------------------------------------------------

def test_correlate_partial_outage():
    """DEGRADED + both up & down methods + >=2 down → PARTIAL_OUTAGE."""
    c = OutageCorrelator()
    checks = [
        CheckResult(method=CheckMethod.IODA, is_down=True, confidence=1.0),      # weight 2
        CheckResult(method=CheckMethod.HTTP, is_down=True, confidence=0.5),       # weight 1 * 0.5 = 0.5 — total 2.5
        CheckResult(method=CheckMethod.PING, is_down=False, confidence=1.0),
    ]
    result = c.correlate("vodacom", checks)
    assert result["status"] == OutageStatus.PARTIAL_OUTAGE
    assert len(result["down_methods"]) >= 2
    assert len(result["up_methods"]) >= 1


# ---------------------------------------------------------------------------
# Correlator — history tracking
# ---------------------------------------------------------------------------

def test_correlate_stores_history():
    c = OutageCorrelator()
    checks = [CheckResult(method=CheckMethod.PING, is_down=True, confidence=1.0)]
    c.correlate("rsaweb", checks)
    c.correlate("rsaweb", checks)
    history = c.get_history("rsaweb")
    assert len(history) == 2


def test_history_empty_for_unknown_isp():
    c = OutageCorrelator()
    assert c.get_history("unknown_isp") == []


# ---------------------------------------------------------------------------
# check_networking_providers conversion
# ---------------------------------------------------------------------------

def test_check_networking_providers_cloudflare():
    c = OutageCorrelator()
    provider_results = {
        "providers": {
            "cloudflare_radar": {
                "provider": "cloudflare_radar",
                "anomaly_detected": True,
                "confidence": 0.7,
                "details": "Traffic drop detected",
            }
        }
    }
    checks = c.check_networking_providers("afrihost", provider_results)
    assert len(checks) == 1
    assert checks[0].method == CheckMethod.CLOUDFLARE_RADAR
    assert checks[0].is_down is True
    assert checks[0].confidence == 0.7


def test_check_networking_providers_ripe_atlas():
    c = OutageCorrelator()
    provider_results = {
        "providers": {
            "ripe_atlas": {
                "provider": "ripe_atlas",
                "total": 10,
                "offline": 8,
            }
        }
    }
    checks = c.check_networking_providers("rsaweb", provider_results)
    assert len(checks) == 1
    assert checks[0].method == CheckMethod.RIPE_ATLAS
    assert checks[0].is_down is True  # 8/10 > 50%


def test_check_networking_providers_bgp():
    c = OutageCorrelator()
    provider_results = {
        "providers": {
            "bgp_looking_glass": {
                "provider": "bgp_looking_glass",
                "visibility_drop": True,
                "visibility_pct": 30,
            }
        }
    }
    checks = c.check_networking_providers("telkom", provider_results)
    assert len(checks) == 1
    assert checks[0].method == CheckMethod.BGP_LOOKING_GLASS
    assert checks[0].is_down is True


def test_check_networking_providers_webhook():
    c = OutageCorrelator()
    provider_results = {
        "providers": {
            "webhook": {
                "provider": "webhook",
                "latest": {
                    "verified": True,
                    "payload": {"status": "down"},
                },
            }
        }
    }
    checks = c.check_networking_providers("rain", provider_results)
    assert len(checks) == 1
    assert checks[0].method == CheckMethod.WEBHOOK
    assert checks[0].is_down is True


def test_check_networking_providers_statuspage():
    c = OutageCorrelator()
    provider_results = {
        "providers": {
            "statuspage_api": {
                "provider": "statuspage_api",
                "overall_status": "major",
                "status_description": "Major outage",
            }
        }
    }
    checks = c.check_networking_providers("afrihost", provider_results)
    assert len(checks) == 1
    assert checks[0].method == CheckMethod.STATUSPAGE_API
    assert checks[0].is_down is True


def test_check_networking_providers_ioda():
    c = OutageCorrelator()
    provider_results = {
        "providers": {
            "ioda": {
                "provider": "ioda",
                "outage_detected": True,
                "overall_score": 0.8,
                "signals": {"bgp": {"is_down": True}},
            }
        }
    }
    checks = c.check_networking_providers("mtn", provider_results)
    assert len(checks) == 1
    assert checks[0].method == CheckMethod.IODA
    assert checks[0].is_down is True


def test_check_networking_providers_empty():
    c = OutageCorrelator()
    checks = c.check_networking_providers("test", {"providers": {}})
    assert checks == []
