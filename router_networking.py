"""
ZA Support — ISP Outage Monitor: Networking Router
FastAPI endpoints for ISP webhook reception, monitoring, correlation, and alerts.

Endpoints:
  POST /api/v1/isp/webhooks/{isp_slug}              — receive ISP status webhooks
  POST /api/v1/isp/webhooks/{isp_slug}/secret        — register webhook signing secrets
  GET  /api/v1/isp/country-health                    — SA-wide internet health overview
  GET  /api/v1/isp/providers                          — list active/configured providers
  GET  /api/v1/isp/isps/{isp_slug}/components        — Statuspage component breakdown
  GET  /api/v1/isp/isps/{isp_slug}/maintenance        — scheduled maintenance windows
  POST /api/v1/isp/isps/{isp_slug}/measure            — trigger on-demand RIPE Atlas measurement
  GET  /api/v1/isp/isps/{isp_slug}/bgp               — BGP route visibility
  GET  /api/v1/isp/isps/{isp_slug}/ioda-history       — IODA time-series data
  GET  /api/v1/isp/isps/{isp_slug}/full-check         — all providers concurrently
  GET  /api/v1/isp/isps/{isp_slug}/correlate          — correlate signals into outage status
  GET  /api/v1/isp/isps/{isp_slug}/correlation-history — check history
  GET  /api/v1/isp/alerts                             — all recent alerts
  GET  /api/v1/isp/alerts/{isp_slug}                  — alerts for a specific ISP
  GET  /api/v1/isp/scheduler-status                   — background scheduler status

Generated: 02/03/2026 SAST
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from networking_integrations import (
    NetworkingIntegrationManager,
    SA_ISP_ASNS,
)
from detection_engine import OutageCorrelator

logger = logging.getLogger("router_networking")

router = APIRouter(prefix="/api/v1/isp", tags=["isp-networking"])

# Singleton manager + correlator — initialised once at import time
manager = NetworkingIntegrationManager()
correlator = OutageCorrelator()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class WebhookSecretRequest(BaseModel):
    secret: str = Field(..., min_length=16, description="HMAC-SHA256 signing secret (min 16 chars)")


class MeasurementRequest(BaseModel):
    target: str = Field(..., description="Target hostname or IP to measure")
    measurement_type: str = Field(default="ping", description="ping | traceroute | dns")
    probe_ids: Optional[List[int]] = Field(default=None, description="Specific RIPE Atlas probe IDs (defaults to all SA probes)")


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------
@router.post("/webhooks/{isp_slug}")
async def receive_webhook(isp_slug: str, request: Request):
    """Receive an ISP status webhook (push notification)."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")

    raw_body = await request.body()
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    signature = request.headers.get(manager.webhook.signature_header)

    result = await manager.webhook.process_webhook(
        isp_slug=isp_slug,
        payload=payload,
        signature=signature,
        raw_body=raw_body,
    )

    if result.get("warning") == "signature_verification_failed":
        raise HTTPException(status_code=401, detail="Webhook signature verification failed")

    return result


@router.post("/webhooks/{isp_slug}/secret")
async def register_webhook_secret(isp_slug: str, req: WebhookSecretRequest):
    """Register a webhook signing secret for an ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")

    manager.webhook.register_secret(isp_slug, req.secret)
    return {"status": "ok", "isp": isp_slug, "message": "Webhook secret registered"}


# ---------------------------------------------------------------------------
# Country-level health
# ---------------------------------------------------------------------------
@router.get("/country-health")
async def country_health():
    """SA-wide internet health overview across all known ISPs and probes."""
    return await manager.check_country_health()


# ---------------------------------------------------------------------------
# Provider info
# ---------------------------------------------------------------------------
@router.get("/providers")
async def list_providers():
    """List all networking data providers and their current configuration."""
    return manager.get_provider_status()


# ---------------------------------------------------------------------------
# Per-ISP endpoints
# ---------------------------------------------------------------------------
@router.get("/isps/{isp_slug}/components")
async def isp_components(isp_slug: str):
    """Get Statuspage component breakdown for an ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")
    return await manager.statuspage.get_components(isp_slug)


@router.get("/isps/{isp_slug}/maintenance")
async def isp_maintenance(isp_slug: str):
    """Get scheduled maintenance windows for an ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")
    return await manager.statuspage.get_maintenance(isp_slug)


@router.post("/isps/{isp_slug}/measure")
async def trigger_measurement(isp_slug: str, req: MeasurementRequest):
    """Trigger an on-demand RIPE Atlas measurement from SA probes."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")

    if req.measurement_type not in ("ping", "traceroute", "dns"):
        raise HTTPException(status_code=400, detail="measurement_type must be ping, traceroute, or dns")

    return await manager.ripe_atlas.create_measurement(
        target=req.target,
        probe_ids=req.probe_ids,
        measurement_type=req.measurement_type,
    )


@router.get("/isps/{isp_slug}/bgp")
async def isp_bgp(isp_slug: str):
    """Get BGP route visibility for an ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")
    return await manager.bgp.check_isp(isp_slug)


@router.get("/isps/{isp_slug}/ioda-history")
async def isp_ioda_history(isp_slug: str, hours: int = Query(default=24, ge=1, le=168)):
    """Get IODA time-series data for an ISP (default: last 24h, max 7 days)."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")

    asn = SA_ISP_ASNS[isp_slug]
    return await manager.ioda.get_history(asn, hours=hours)


@router.get("/isps/{isp_slug}/full-check")
async def isp_full_check(isp_slug: str):
    """Run all enabled providers concurrently for a single ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")
    return await manager.check_all(isp_slug)


# ---------------------------------------------------------------------------
# Outage correlation endpoints (detection_engine integration)
# ---------------------------------------------------------------------------
@router.get("/isps/{isp_slug}/correlate")
async def correlate_isp(isp_slug: str):
    """Run all providers, then correlate signals into an outage determination."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")

    provider_results = await manager.check_all(isp_slug)
    checks = correlator.check_networking_providers(isp_slug, provider_results)
    determination = correlator.correlate(isp_slug, checks)
    determination["provider_results"] = provider_results
    return determination


@router.get("/isps/{isp_slug}/correlation-history")
async def isp_correlation_history(
    isp_slug: str,
    limit: int = Query(default=50, ge=1, le=500),
):
    """Get recent correlation check history for an ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")
    return {"isp": isp_slug, "history": correlator.get_history(isp_slug, limit=limit)}


# ---------------------------------------------------------------------------
# Alert + scheduler endpoints (wired from main.py at runtime)
# ---------------------------------------------------------------------------
# These use late-binding so they work even before main.py sets them up.
_alert_store = None
_isp_scheduler = None


def bind_scheduler(alert_store, scheduler) -> None:
    """Called from main.py after objects are constructed."""
    global _alert_store, _isp_scheduler
    _alert_store = alert_store
    _isp_scheduler = scheduler


@router.get("/alerts")
async def list_all_alerts(limit: int = Query(default=100, ge=1, le=500)):
    """Get all recent ISP outage alerts across every ISP."""
    if _alert_store is None:
        return {"alerts": [], "total": 0}
    return {"alerts": _alert_store.get_all(limit=limit), "total": _alert_store.count()}


@router.get("/alerts/{isp_slug}")
async def list_isp_alerts(isp_slug: str, limit: int = Query(default=50, ge=1, le=500)):
    """Get recent alerts for a specific ISP."""
    if isp_slug not in SA_ISP_ASNS:
        raise HTTPException(status_code=404, detail=f"Unknown ISP: {isp_slug}")
    if _alert_store is None:
        return {"isp": isp_slug, "alerts": [], "total": 0}
    alerts = _alert_store.get(isp_slug, limit=limit)
    return {"isp": isp_slug, "alerts": alerts, "total": len(alerts)}


@router.get("/scheduler-status")
async def scheduler_status():
    """Get the background ISP monitor scheduler status."""
    if _isp_scheduler is None:
        return {"running": False, "message": "Scheduler not initialised"}
    return _isp_scheduler.get_status()
