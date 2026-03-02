"""
ZA Support — ISP Outage Monitor: Detection Engine
Weighted correlation engine that fuses signals from all monitoring sources
to determine outage status with confidence scoring.

Method weights reflect reliability:
  - ripe_atlas=3       (physical probes — ground truth)
  - agent=3            (our own Health Check Agent — ground truth)
  - bgp_looking_glass=2 (routing layer — root cause indicator)
  - cloudflare_radar=2 (large-scale traffic analysis)
  - ioda=2             (multi-signal academic observatory)
  - webhook=2          (direct ISP push notification)
  - statuspage_api=1   (ISP self-reported, may lag)
  - status_page=1      (scraped status page, may lag)
  - downdetector=1     (crowdsourced, noisy)
  - http=1             (single-point HTTP probe)
  - ping=1             (single-point ICMP probe)

Correlation rules:
  - weighted_down_score >= 4  AND  confirmed_down >= 1  →  FULL OUTAGE
  - BGP visibility drop + any confirmation  →  FULL OUTAGE (routing is root cause)
  - weighted_down_score >= 2  →  DEGRADED
  - else  →  OPERATIONAL

Generated: 02/03/2026 SAST
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("detection_engine")

SAST = timezone(timedelta(hours=2))


class OutageStatus(str, Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    FULL_OUTAGE = "full_outage"


class CheckMethod(str, Enum):
    """All monitoring methods available."""
    HTTP = "http"
    PING = "ping"
    STATUS_PAGE = "status_page"
    DOWNDETECTOR = "downdetector"
    AGENT = "agent"
    CLOUDFLARE_RADAR = "cloudflare_radar"
    IODA = "ioda"
    RIPE_ATLAS = "ripe_atlas"
    STATUSPAGE_API = "statuspage_api"
    WEBHOOK = "webhook"
    BGP_LOOKING_GLASS = "bgp_looking_glass"


# Reliability weights — higher = more trustworthy signal
METHOD_WEIGHTS: Dict[str, int] = {
    CheckMethod.RIPE_ATLAS: 3,
    CheckMethod.AGENT: 3,
    CheckMethod.BGP_LOOKING_GLASS: 2,
    CheckMethod.CLOUDFLARE_RADAR: 2,
    CheckMethod.IODA: 2,
    CheckMethod.WEBHOOK: 2,
    CheckMethod.STATUSPAGE_API: 1,
    CheckMethod.STATUS_PAGE: 1,
    CheckMethod.DOWNDETECTOR: 1,
    CheckMethod.HTTP: 1,
    CheckMethod.PING: 1,
}


class CheckResult:
    """A single check result from any monitoring method."""

    def __init__(
        self,
        method: str,
        is_down: bool,
        confidence: float = 1.0,
        details: str = "",
        raw: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.method = method
        self.is_down = is_down
        self.confidence = min(max(confidence, 0.0), 1.0)
        self.details = details
        self.raw = raw or {}
        self.timestamp = timestamp or datetime.now(SAST)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "is_down": self.is_down,
            "confidence": self.confidence,
            "details": self.details,
            "weight": METHOD_WEIGHTS.get(self.method, 1),
            "timestamp": self.timestamp.isoformat(),
        }


class OutageCorrelator:
    """
    Fuses multiple CheckResult signals into a single outage determination.

    Correlation logic:
      1. Calculate weighted_down_score = sum of (weight * confidence) for all down signals
      2. Count confirmed_down = number of distinct methods reporting down
      3. Check for BGP visibility drop (routing-layer root cause)
      4. Apply thresholds to determine overall status
    """

    FULL_OUTAGE_THRESHOLD = 4      # weighted score needed for full outage
    DEGRADED_THRESHOLD = 2          # weighted score needed for degraded
    MIN_CONFIRMATIONS = 1           # minimum distinct methods confirming down

    def __init__(self):
        self._check_history: Dict[str, List[CheckResult]] = {}  # isp_slug -> [results]

    def correlate(self, isp_slug: str, checks: List[CheckResult]) -> Dict[str, Any]:
        """Correlate multiple check results into an outage determination."""
        if not checks:
            return {
                "isp": isp_slug,
                "status": OutageStatus.OPERATIONAL,
                "weighted_down_score": 0,
                "confirmed_down": 0,
                "total_checks": 0,
                "details": "No check data available",
                "checks": [],
            }

        # Store history
        if isp_slug not in self._check_history:
            self._check_history[isp_slug] = []
        self._check_history[isp_slug].extend(checks)
        # Keep last 500 results per ISP
        if len(self._check_history[isp_slug]) > 500:
            self._check_history[isp_slug] = self._check_history[isp_slug][-500:]

        # Calculate weighted scores
        weighted_down_score = 0.0
        confirmed_down = 0
        bgp_drop = False
        down_methods = []
        up_methods = []

        for check in checks:
            weight = METHOD_WEIGHTS.get(check.method, 1)
            if check.is_down:
                weighted_down_score += weight * check.confidence
                confirmed_down += 1
                down_methods.append(check.method)
                if check.method == CheckMethod.BGP_LOOKING_GLASS:
                    bgp_drop = True
            else:
                up_methods.append(check.method)

        # Determine status
        status = OutageStatus.OPERATIONAL

        if bgp_drop and confirmed_down >= 1:
            # BGP visibility drop + any confirmation = routing-level outage
            status = OutageStatus.FULL_OUTAGE
        elif weighted_down_score >= self.FULL_OUTAGE_THRESHOLD and confirmed_down >= self.MIN_CONFIRMATIONS:
            status = OutageStatus.FULL_OUTAGE
        elif weighted_down_score >= self.DEGRADED_THRESHOLD:
            status = OutageStatus.DEGRADED

        # Partial outage: some methods up, some down with moderate score
        if status == OutageStatus.DEGRADED and up_methods and down_methods:
            if len(down_methods) >= 2:
                status = OutageStatus.PARTIAL_OUTAGE

        result = {
            "isp": isp_slug,
            "status": status,
            "weighted_down_score": round(weighted_down_score, 2),
            "confirmed_down": confirmed_down,
            "total_checks": len(checks),
            "bgp_drop": bgp_drop,
            "down_methods": down_methods,
            "up_methods": up_methods,
            "correlated_at": datetime.now(SAST).isoformat(),
            "checks": [c.to_dict() for c in checks],
        }

        if status in (OutageStatus.FULL_OUTAGE, OutageStatus.PARTIAL_OUTAGE):
            logger.warning(
                f"OUTAGE DETECTED for {isp_slug}: status={status} "
                f"score={weighted_down_score:.1f} confirmed={confirmed_down} "
                f"bgp_drop={bgp_drop} methods={down_methods}"
            )

        return result

    def check_networking_providers(self, isp_slug: str, provider_results: Dict[str, Any]) -> List[CheckResult]:
        """
        Convert raw provider results from NetworkingIntegrationManager.check_all()
        into CheckResult objects for correlation.
        """
        checks: List[CheckResult] = []
        providers = provider_results.get("providers", {})

        # Cloudflare Radar
        cf = providers.get("cloudflare_radar", {})
        if cf and cf.get("provider") == "cloudflare_radar":
            checks.append(CheckResult(
                method=CheckMethod.CLOUDFLARE_RADAR,
                is_down=cf.get("anomaly_detected", False),
                confidence=cf.get("confidence", 0.5),
                details=cf.get("details", ""),
                raw=cf,
            ))

        # IODA
        ioda = providers.get("ioda", {})
        if ioda and ioda.get("provider") == "ioda":
            checks.append(CheckResult(
                method=CheckMethod.IODA,
                is_down=ioda.get("outage_detected", False),
                confidence=ioda.get("overall_score", 0.0),
                details=f"Signals: {ioda.get('signals', {})}",
                raw=ioda,
            ))

        # RIPE Atlas
        ripe = providers.get("ripe_atlas", {})
        if ripe and ripe.get("provider") == "ripe_atlas":
            total = ripe.get("total", 0)
            offline = ripe.get("offline", 0)
            is_down = total > 0 and offline > total / 2
            confidence = (offline / total) if total > 0 else 0.0
            checks.append(CheckResult(
                method=CheckMethod.RIPE_ATLAS,
                is_down=is_down,
                confidence=confidence,
                details=f"{offline}/{total} probes offline",
                raw=ripe,
            ))

        # Statuspage API
        sp = providers.get("statuspage_api", {})
        if sp and sp.get("provider") == "statuspage_api":
            overall = sp.get("overall_status", "none")
            is_down = overall in ("major", "critical")
            confidence = 0.9 if is_down else 0.3
            checks.append(CheckResult(
                method=CheckMethod.STATUSPAGE_API,
                is_down=is_down,
                confidence=confidence,
                details=f"Status: {overall} — {sp.get('status_description', '')}",
                raw=sp,
            ))

        # BGP Looking Glass
        bgp = providers.get("bgp_looking_glass", {})
        if bgp and bgp.get("provider") == "bgp_looking_glass":
            checks.append(CheckResult(
                method=CheckMethod.BGP_LOOKING_GLASS,
                is_down=bgp.get("visibility_drop", False),
                confidence=1.0 - (bgp.get("visibility_pct", 100) / 100),
                details=f"Visibility: {bgp.get('visibility_pct', 100)}%",
                raw=bgp,
            ))

        # Webhook (latest)
        wh = providers.get("webhook", {})
        if wh and wh.get("provider") == "webhook":
            latest = wh.get("latest", {})
            if latest:
                payload = latest.get("payload", {})
                wh_status = str(payload.get("status", "")).lower()
                is_down = wh_status in ("down", "outage", "major", "critical")
                checks.append(CheckResult(
                    method=CheckMethod.WEBHOOK,
                    is_down=is_down,
                    confidence=0.9 if latest.get("verified") else 0.4,
                    details=f"Webhook status: {wh_status}",
                    raw=latest,
                ))

        return checks

    def get_history(self, isp_slug: str, limit: int = 50) -> List[Dict]:
        """Get recent check history for an ISP."""
        results = self._check_history.get(isp_slug, [])
        return [r.to_dict() for r in results[-limit:]]
