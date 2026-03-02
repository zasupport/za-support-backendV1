"""
ZA Support — ISP Outage Monitor: Background Scheduler & Alerts
Periodically polls all ISPs, correlates signals, fires alerts on status changes.

Usage:
    Called from main.py lifespan — starts an asyncio background task that runs
    indefinitely. On shutdown the task is cancelled cleanly.

Generated: 02/03/2026 SAST
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from detection_engine import OutageCorrelator, OutageStatus

logger = logging.getLogger("scheduler")

SAST = timezone(timedelta(hours=2))


# ===================================================================
# Alert Store
# ===================================================================
class AlertStore:
    """In-memory alert store with severity levels and history."""

    def __init__(self, max_per_isp: int = 200):
        self._alerts: Dict[str, List[Dict[str, Any]]] = {}  # isp_slug -> [alerts]
        self._max = max_per_isp

    def add(self, isp_slug: str, alert: Dict[str, Any]) -> None:
        if isp_slug not in self._alerts:
            self._alerts[isp_slug] = []
        self._alerts[isp_slug].append(alert)
        if len(self._alerts[isp_slug]) > self._max:
            self._alerts[isp_slug] = self._alerts[isp_slug][-self._max:]

    def get(self, isp_slug: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._alerts.get(isp_slug, [])[-limit:]

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        all_alerts: List[Dict[str, Any]] = []
        for alerts in self._alerts.values():
            all_alerts.extend(alerts)
        all_alerts.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
        return all_alerts[:limit]

    def count(self) -> int:
        return sum(len(v) for v in self._alerts.values())


# ===================================================================
# ISP Monitor Scheduler
# ===================================================================
class ISPMonitorScheduler:
    """Background task that polls ISPs and fires alerts on status changes."""

    def __init__(
        self,
        manager,  # NetworkingIntegrationManager
        correlator: OutageCorrelator,
        alert_store: AlertStore,
        interval_seconds: int = 300,
    ):
        self.manager = manager
        self.correlator = correlator
        self.alerts = alert_store
        self.interval = interval_seconds
        self._last_status: Dict[str, str] = {}  # isp_slug -> last OutageStatus value
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._cycle_count = 0

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"ISP monitor scheduler started (interval={self.interval}s)")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ISP monitor scheduler stopped")

    async def _loop(self) -> None:
        from networking_integrations import SA_ISP_ASNS

        while self._running:
            self._cycle_count += 1
            logger.info(f"Scheduler cycle #{self._cycle_count} starting")

            for isp_slug in SA_ISP_ASNS:
                if not self._running:
                    break
                try:
                    await self._check_isp(isp_slug)
                except Exception as e:
                    logger.error(f"Scheduler error checking {isp_slug}: {e}")

            logger.info(f"Scheduler cycle #{self._cycle_count} complete")
            await asyncio.sleep(self.interval)

    async def _check_isp(self, isp_slug: str) -> None:
        provider_results = await self.manager.check_all(isp_slug)
        checks = self.correlator.check_networking_providers(isp_slug, provider_results)
        determination = self.correlator.correlate(isp_slug, checks)

        new_status = determination.get("status", OutageStatus.OPERATIONAL)
        if isinstance(new_status, OutageStatus):
            new_status = new_status.value

        old_status = self._last_status.get(isp_slug, OutageStatus.OPERATIONAL.value)

        if new_status != old_status:
            self._fire_alert(isp_slug, old_status, new_status, determination)
            self._last_status[isp_slug] = new_status

    def _fire_alert(
        self,
        isp_slug: str,
        old_status: str,
        new_status: str,
        determination: Dict[str, Any],
    ) -> None:
        severity = "info"
        if new_status in (OutageStatus.FULL_OUTAGE.value, OutageStatus.PARTIAL_OUTAGE.value):
            severity = "critical"
        elif new_status == OutageStatus.DEGRADED.value:
            severity = "warning"
        elif old_status in (OutageStatus.FULL_OUTAGE.value, OutageStatus.PARTIAL_OUTAGE.value):
            severity = "resolved"

        alert = {
            "isp": isp_slug,
            "severity": severity,
            "old_status": old_status,
            "new_status": new_status,
            "weighted_score": determination.get("weighted_down_score", 0),
            "confirmed_down": determination.get("confirmed_down", 0),
            "down_methods": determination.get("down_methods", []),
            "timestamp": datetime.now(SAST).isoformat(),
            "cycle": self._cycle_count,
        }

        self.alerts.add(isp_slug, alert)
        logger.warning(
            f"ALERT [{severity.upper()}] {isp_slug}: {old_status} -> {new_status} "
            f"(score={alert['weighted_score']}, confirmed={alert['confirmed_down']})"
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "interval_seconds": self.interval,
            "cycles_completed": self._cycle_count,
            "monitored_isps": len(self._last_status),
            "last_statuses": dict(self._last_status),
            "total_alerts": self.alerts.count(),
        }
