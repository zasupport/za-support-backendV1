"""
ZA Support — ISP Outage Monitor: Networking Integrations
Six real-world data provider classes + orchestrator for ground-truth outage detection.

Providers:
  1. CloudflareRadarProvider  — traffic anomalies per ASN via Cloudflare Radar API
  2. IODAProvider             — BGP, active probing, darknet signals via IODA/CAIDA
  3. RIPEAtlasProvider        — physical probe measurements in South Africa
  4. StatuspageProvider       — structured JSON from ISP Atlassian Statuspages
  5. BGPLookingGlassProvider  — BGP route visibility via RIPE RIS
  6. ISPWebhookHandler        — inbound push webhooks from ISPs (HMAC-SHA256)

Orchestrator:
  NetworkingIntegrationManager — initialises all providers, runs check_all() concurrently

Generated: 02/03/2026 SAST
"""

import asyncio
import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from app.config import (
    BGP_CHECK_INTERVAL,
    BGP_LOOKING_GLASS_ENABLED,
    CLOUDFLARE_RADAR_CHECK_INTERVAL,
    CLOUDFLARE_RADAR_ENABLED,
    CLOUDFLARE_RADAR_TOKEN,
    IODA_CHECK_INTERVAL,
    IODA_COUNTRY_CHECK_ENABLED,
    IODA_ENABLED,
    NETWORKING_INTEGRATIONS_ENABLED,
    PROVIDER_TIMEOUT,
    RIPE_ATLAS_API_KEY,
    RIPE_ATLAS_CHECK_INTERVAL,
    RIPE_ATLAS_ENABLED,
    STATUSPAGE_API_ENABLED,
    STATUSPAGE_CHECK_INTERVAL,
    WEBHOOK_ENABLED,
    WEBHOOK_SIGNATURE_HEADER,
)

logger = logging.getLogger("networking_integrations")

SAST = timezone(timedelta(hours=2))

# ---------------------------------------------------------------------------
# South African ISP ASN mappings
# ---------------------------------------------------------------------------
SA_ISP_ASNS: Dict[str, int] = {
    "afrihost": 37611,
    "rain": 327741,
    "vumatel": 328364,
    "openserve": 36874,
    "rsaweb": 37153,
    "coolideas": 328006,
    "webafrica": 37468,
    "herotel": 328210,
    "vodacom": 29975,
    "mtn": 16637,
    "telkom": 5713,
}

# ---------------------------------------------------------------------------
# RIPE Atlas probe IDs located in South Africa
# ---------------------------------------------------------------------------
SA_RIPE_PROBES: Dict[int, Dict[str, str]] = {
    6083: {"city": "Johannesburg", "isp": "generic"},
    6354: {"city": "Cape Town", "isp": "generic"},
    13498: {"city": "Durban", "isp": "generic"},
    14018: {"city": "Pretoria", "isp": "generic"},
    30808: {"city": "Johannesburg", "isp": "vumatel"},
    33362: {"city": "Cape Town", "isp": "rsaweb"},
    52148: {"city": "Johannesburg", "isp": "afrihost"},
}

# ---------------------------------------------------------------------------
# ISP Statuspage URLs (Atlassian Statuspage JSON API)
# ---------------------------------------------------------------------------
ISP_STATUSPAGES: Dict[str, str] = {
    "afrihost": "https://status.afrihost.com",
    "rsaweb": "https://status.rsaweb.co.za",
}


# ===================================================================
# 1. Cloudflare Radar Provider
# ===================================================================
class CloudflareRadarProvider:
    """Queries Cloudflare Radar API for traffic anomaly data per ASN."""

    BASE_URL = "https://api.cloudflare.com/client/v4/radar"

    def __init__(self, token: str = "", timeout: int = PROVIDER_TIMEOUT):
        self.token = token or CLOUDFLARE_RADAR_TOKEN
        self.timeout = timeout
        self.enabled = CLOUDFLARE_RADAR_ENABLED and bool(self.token)
        self.check_interval = CLOUDFLARE_RADAR_CHECK_INTERVAL
        self._last_check: Dict[str, float] = {}
        self._cache: Dict[str, Dict] = {}

    async def check_asn(self, asn: int) -> Dict[str, Any]:
        """Check traffic anomalies for a specific ASN."""
        if not self.enabled:
            return {"status": "disabled", "asn": asn}

        cache_key = str(asn)
        now = time.time()
        if cache_key in self._last_check and (now - self._last_check[cache_key]) < self.check_interval:
            return self._cache.get(cache_key, {})

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        result: Dict[str, Any] = {
            "provider": "cloudflare_radar",
            "asn": asn,
            "checked_at": datetime.now(SAST).isoformat(),
            "anomaly_detected": False,
            "traffic_change_pct": 0.0,
            "confidence": 0.0,
            "raw": {},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Traffic anomaly detection
                resp = await client.get(
                    f"{self.BASE_URL}/traffic_anomalies",
                    headers=headers,
                    params={"asn": asn, "limit": 5, "dateRange": "1d"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    anomalies = data.get("result", {}).get("trafficAnomalies", [])
                    if anomalies:
                        latest = anomalies[0]
                        result["anomaly_detected"] = True
                        result["traffic_change_pct"] = latest.get("value", 0)
                        result["confidence"] = 0.8
                        result["details"] = latest.get("description", "Traffic anomaly detected")
                    result["raw"] = data

                # Also check traffic summary for context
                resp2 = await client.get(
                    f"{self.BASE_URL}/http/summary",
                    headers=headers,
                    params={"asn": asn, "dateRange": "1h"},
                )
                if resp2.status_code == 200:
                    result["traffic_summary"] = resp2.json().get("result", {})

        except httpx.TimeoutException:
            result["error"] = "timeout"
            logger.warning(f"Cloudflare Radar timeout for ASN {asn}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Cloudflare Radar error for ASN {asn}: {e}")

        self._last_check[cache_key] = now
        self._cache[cache_key] = result
        return result

    async def check_isp(self, isp_slug: str) -> Dict[str, Any]:
        """Check a named ISP by looking up its ASN."""
        asn = SA_ISP_ASNS.get(isp_slug)
        if not asn:
            return {"status": "unknown_isp", "isp": isp_slug}
        return await self.check_asn(asn)


# ===================================================================
# 2. IODA Provider (CAIDA / Georgia Tech)
# ===================================================================
class IODAProvider:
    """Queries IODA/CAIDA for BGP, active probing, and darknet outage signals."""

    BASE_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2"

    def __init__(self, timeout: int = PROVIDER_TIMEOUT):
        self.timeout = timeout
        self.enabled = IODA_ENABLED
        self.country_check = IODA_COUNTRY_CHECK_ENABLED
        self.check_interval = IODA_CHECK_INTERVAL
        self._last_check: Dict[str, float] = {}
        self._cache: Dict[str, Dict] = {}

    async def check_asn(self, asn: int) -> Dict[str, Any]:
        """Check IODA signals for a specific ASN."""
        if not self.enabled:
            return {"status": "disabled", "asn": asn}

        cache_key = f"asn_{asn}"
        now = time.time()
        if cache_key in self._last_check and (now - self._last_check[cache_key]) < self.check_interval:
            return self._cache.get(cache_key, {})

        result: Dict[str, Any] = {
            "provider": "ioda",
            "asn": asn,
            "checked_at": datetime.now(SAST).isoformat(),
            "outage_detected": False,
            "signals": {},
            "overall_score": 0.0,
            "raw": {},
        }

        try:
            until = int(datetime.now(SAST).timestamp())
            since = until - 3600  # last hour

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/signals/raw/asn/{asn}",
                    params={"from": since, "until": until},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result["raw"] = data

                    for source in data.get("data", []):
                        source_name = source.get("sourceName", "unknown")
                        values = source.get("values", [])
                        if values:
                            latest_val = values[-1]
                            normal_val = source.get("normalizedBaseline", 1)
                            if normal_val and normal_val > 0:
                                ratio = latest_val / normal_val
                                is_down = ratio < 0.5
                            else:
                                ratio = 1.0
                                is_down = False

                            result["signals"][source_name] = {
                                "latest_value": latest_val,
                                "baseline": normal_val,
                                "ratio": round(ratio, 3),
                                "is_down": is_down,
                            }

                    down_signals = sum(1 for s in result["signals"].values() if s.get("is_down"))
                    total_signals = len(result["signals"])
                    if total_signals > 0:
                        result["overall_score"] = round(down_signals / total_signals, 2)
                        result["outage_detected"] = down_signals >= 2 or (
                            total_signals == 1 and down_signals == 1
                        )

        except httpx.TimeoutException:
            result["error"] = "timeout"
            logger.warning(f"IODA timeout for ASN {asn}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"IODA error for ASN {asn}: {e}")

        self._last_check[cache_key] = now
        self._cache[cache_key] = result
        return result

    async def check_country(self, country_code: str = "ZA") -> Dict[str, Any]:
        """Check IODA country-level signals for South Africa."""
        if not self.enabled or not self.country_check:
            return {"status": "disabled", "country": country_code}

        cache_key = f"country_{country_code}"
        now = time.time()
        if cache_key in self._last_check and (now - self._last_check[cache_key]) < self.check_interval:
            return self._cache.get(cache_key, {})

        result: Dict[str, Any] = {
            "provider": "ioda",
            "entity_type": "country",
            "country": country_code,
            "checked_at": datetime.now(SAST).isoformat(),
            "outage_detected": False,
            "signals": {},
            "raw": {},
        }

        try:
            until = int(datetime.now(SAST).timestamp())
            since = until - 3600

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/signals/raw/country/{country_code}",
                    params={"from": since, "until": until},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result["raw"] = data
                    for source in data.get("data", []):
                        source_name = source.get("sourceName", "unknown")
                        values = source.get("values", [])
                        if values:
                            result["signals"][source_name] = {
                                "latest_value": values[-1],
                                "count": len(values),
                            }
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"IODA country check error: {e}")

        self._last_check[cache_key] = now
        self._cache[cache_key] = result
        return result

    async def get_history(self, asn: int, hours: int = 24) -> Dict[str, Any]:
        """Get IODA time-series data for an ASN over the given window."""
        if not self.enabled:
            return {"status": "disabled", "asn": asn}

        result: Dict[str, Any] = {
            "provider": "ioda",
            "asn": asn,
            "hours": hours,
            "series": [],
        }

        try:
            until = int(datetime.now(SAST).timestamp())
            since = until - (hours * 3600)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/signals/raw/asn/{asn}",
                    params={"from": since, "until": until},
                )
                if resp.status_code == 200:
                    result["series"] = resp.json().get("data", [])
        except Exception as e:
            result["error"] = str(e)

        return result

    async def check_isp(self, isp_slug: str) -> Dict[str, Any]:
        asn = SA_ISP_ASNS.get(isp_slug)
        if not asn:
            return {"status": "unknown_isp", "isp": isp_slug}
        return await self.check_asn(asn)


# ===================================================================
# 3. RIPE Atlas Provider
# ===================================================================
class RIPEAtlasProvider:
    """Queries RIPE Atlas for real physical probe measurements in South Africa."""

    BASE_URL = "https://atlas.ripe.net/api/v2"

    def __init__(self, api_key: str = "", timeout: int = PROVIDER_TIMEOUT):
        self.api_key = api_key or RIPE_ATLAS_API_KEY
        self.timeout = timeout
        self.enabled = RIPE_ATLAS_ENABLED
        self.check_interval = RIPE_ATLAS_CHECK_INTERVAL
        self._last_check: Dict[str, float] = {}
        self._cache: Dict[str, Dict] = {}

    async def check_probes(self) -> Dict[str, Any]:
        """Check status of all known SA probes."""
        if not self.enabled:
            return {"status": "disabled"}

        cache_key = "sa_probes"
        now = time.time()
        if cache_key in self._last_check and (now - self._last_check[cache_key]) < self.check_interval:
            return self._cache.get(cache_key, {})

        result: Dict[str, Any] = {
            "provider": "ripe_atlas",
            "checked_at": datetime.now(SAST).isoformat(),
            "probes": {},
            "online_count": 0,
            "offline_count": 0,
            "total": len(SA_RIPE_PROBES),
        }

        try:
            probe_ids = ",".join(str(p) for p in SA_RIPE_PROBES.keys())
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Key {self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/probes/",
                    headers=headers,
                    params={"id__in": probe_ids, "format": "json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for probe in data.get("results", []):
                        pid = probe.get("id")
                        is_connected = probe.get("status", {}).get("id") == 1
                        probe_meta = SA_RIPE_PROBES.get(pid, {})
                        result["probes"][pid] = {
                            "id": pid,
                            "city": probe_meta.get("city", "unknown"),
                            "isp": probe_meta.get("isp", "unknown"),
                            "connected": is_connected,
                            "asn_v4": probe.get("asn_v4"),
                            "country_code": probe.get("country_code"),
                            "status_name": probe.get("status", {}).get("name", "unknown"),
                            "last_connected": probe.get("last_connected"),
                        }
                        if is_connected:
                            result["online_count"] += 1
                        else:
                            result["offline_count"] += 1

        except httpx.TimeoutException:
            result["error"] = "timeout"
            logger.warning("RIPE Atlas timeout checking probes")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"RIPE Atlas error: {e}")

        self._last_check[cache_key] = now
        self._cache[cache_key] = result
        return result

    async def create_measurement(
        self, target: str, probe_ids: Optional[List[int]] = None, measurement_type: str = "ping"
    ) -> Dict[str, Any]:
        """Create an on-demand RIPE Atlas measurement from SA probes."""
        if not self.enabled or not self.api_key:
            return {"status": "disabled_or_no_key"}

        probes = probe_ids or list(SA_RIPE_PROBES.keys())
        definitions = {
            "ping": {
                "type": "ping",
                "af": 4,
                "target": target,
                "description": f"ZA Support on-demand ping to {target}",
                "packets": 3,
                "size": 48,
            },
            "traceroute": {
                "type": "traceroute",
                "af": 4,
                "target": target,
                "description": f"ZA Support on-demand traceroute to {target}",
                "protocol": "ICMP",
            },
            "dns": {
                "type": "dns",
                "af": 4,
                "target": target,
                "description": f"ZA Support on-demand DNS to {target}",
                "query_class": "IN",
                "query_type": "A",
                "query_argument": target,
                "use_macros": False,
            },
        }

        definition = definitions.get(measurement_type, definitions["ping"])

        payload = {
            "definitions": [definition],
            "probes": [{"requested": len(probes), "type": "probes", "value": ",".join(str(p) for p in probes)}],
            "is_oneoff": True,
        }

        result: Dict[str, Any] = {
            "provider": "ripe_atlas",
            "action": "create_measurement",
            "target": target,
            "type": measurement_type,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/measurements/",
                    headers={"Authorization": f"Key {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    result["measurement_ids"] = data.get("measurements", [])
                    result["status"] = "created"
                else:
                    result["status"] = "error"
                    result["error"] = resp.text
                    result["status_code"] = resp.status_code
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def check_isp(self, isp_slug: str) -> Dict[str, Any]:
        """Check probes associated with a specific ISP."""
        probe_data = await self.check_probes()
        isp_probes = {
            pid: info
            for pid, info in probe_data.get("probes", {}).items()
            if SA_RIPE_PROBES.get(int(pid) if isinstance(pid, str) else pid, {}).get("isp") == isp_slug
        }
        online = sum(1 for p in isp_probes.values() if p.get("connected"))
        return {
            "provider": "ripe_atlas",
            "isp": isp_slug,
            "checked_at": probe_data.get("checked_at"),
            "probes": isp_probes,
            "online": online,
            "offline": len(isp_probes) - online,
            "total": len(isp_probes),
        }


# ===================================================================
# 4. Statuspage Provider (Atlassian Statuspage JSON API)
# ===================================================================
class StatuspageProvider:
    """Queries structured JSON API from ISPs using Atlassian Statuspage."""

    def __init__(self, timeout: int = PROVIDER_TIMEOUT):
        self.timeout = timeout
        self.enabled = STATUSPAGE_API_ENABLED
        self.check_interval = STATUSPAGE_CHECK_INTERVAL
        self._last_check: Dict[str, float] = {}
        self._cache: Dict[str, Dict] = {}

    async def check_isp(self, isp_slug: str) -> Dict[str, Any]:
        """Check ISP status via their Statuspage JSON API."""
        if not self.enabled:
            return {"status": "disabled", "isp": isp_slug}

        base_url = ISP_STATUSPAGES.get(isp_slug)
        if not base_url:
            return {"status": "no_statuspage", "isp": isp_slug}

        cache_key = isp_slug
        now = time.time()
        if cache_key in self._last_check and (now - self._last_check[cache_key]) < self.check_interval:
            return self._cache.get(cache_key, {})

        result: Dict[str, Any] = {
            "provider": "statuspage_api",
            "isp": isp_slug,
            "checked_at": datetime.now(SAST).isoformat(),
            "overall_status": "unknown",
            "components": [],
            "incidents": [],
            "maintenance": [],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Overall status
                resp = await client.get(f"{base_url}/api/v2/status.json")
                if resp.status_code == 200:
                    data = resp.json()
                    result["overall_status"] = data.get("status", {}).get("indicator", "unknown")
                    result["status_description"] = data.get("status", {}).get("description", "")

                # Components
                resp2 = await client.get(f"{base_url}/api/v2/components.json")
                if resp2.status_code == 200:
                    components = resp2.json().get("components", [])
                    result["components"] = [
                        {
                            "name": c.get("name"),
                            "status": c.get("status"),
                            "description": c.get("description", ""),
                            "updated_at": c.get("updated_at"),
                        }
                        for c in components
                    ]

                # Active incidents
                resp3 = await client.get(f"{base_url}/api/v2/incidents/unresolved.json")
                if resp3.status_code == 200:
                    incidents = resp3.json().get("incidents", [])
                    result["incidents"] = [
                        {
                            "name": inc.get("name"),
                            "status": inc.get("status"),
                            "impact": inc.get("impact"),
                            "created_at": inc.get("created_at"),
                            "updated_at": inc.get("updated_at"),
                            "shortlink": inc.get("shortlink", ""),
                        }
                        for inc in incidents
                    ]

                # Scheduled maintenance
                resp4 = await client.get(f"{base_url}/api/v2/scheduled-maintenances/upcoming.json")
                if resp4.status_code == 200:
                    maint = resp4.json().get("scheduled_maintenances", [])
                    result["maintenance"] = [
                        {
                            "name": m.get("name"),
                            "status": m.get("status"),
                            "scheduled_for": m.get("scheduled_for"),
                            "scheduled_until": m.get("scheduled_until"),
                            "impact": m.get("impact"),
                        }
                        for m in maint
                    ]

        except httpx.TimeoutException:
            result["error"] = "timeout"
            logger.warning(f"Statuspage timeout for {isp_slug}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Statuspage error for {isp_slug}: {e}")

        self._last_check[cache_key] = now
        self._cache[cache_key] = result
        return result

    async def get_components(self, isp_slug: str) -> Dict[str, Any]:
        """Get detailed component breakdown for an ISP."""
        data = await self.check_isp(isp_slug)
        return {
            "isp": isp_slug,
            "components": data.get("components", []),
            "overall_status": data.get("overall_status"),
        }

    async def get_maintenance(self, isp_slug: str) -> Dict[str, Any]:
        """Get scheduled maintenance windows for an ISP."""
        data = await self.check_isp(isp_slug)
        return {
            "isp": isp_slug,
            "maintenance": data.get("maintenance", []),
        }


# ===================================================================
# 5. BGP Looking Glass Provider (RIPE RIS)
# ===================================================================
class BGPLookingGlassProvider:
    """Queries RIPE RIS for BGP route visibility per ASN."""

    BASE_URL = "https://stat.ripe.net/data"

    def __init__(self, timeout: int = PROVIDER_TIMEOUT):
        self.timeout = timeout
        self.enabled = BGP_LOOKING_GLASS_ENABLED
        self.check_interval = BGP_CHECK_INTERVAL
        self._last_check: Dict[str, float] = {}
        self._cache: Dict[str, Dict] = {}

    async def check_asn(self, asn: int) -> Dict[str, Any]:
        """Check BGP route visibility for a specific ASN."""
        if not self.enabled:
            return {"status": "disabled", "asn": asn}

        cache_key = str(asn)
        now = time.time()
        if cache_key in self._last_check and (now - self._last_check[cache_key]) < self.check_interval:
            return self._cache.get(cache_key, {})

        result: Dict[str, Any] = {
            "provider": "bgp_looking_glass",
            "asn": asn,
            "checked_at": datetime.now(SAST).isoformat(),
            "visibility_drop": False,
            "prefixes_announced": 0,
            "peers_seeing": 0,
            "visibility_pct": 100.0,
            "raw": {},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # RIS peer count / visibility
                resp = await client.get(
                    f"{self.BASE_URL}/routing-status/data.json",
                    params={"resource": f"AS{asn}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result["raw"] = data
                    status = data.get("data", {}).get("routing_status", {})

                    announced = status.get("announced_space", {})
                    result["prefixes_v4"] = announced.get("v4", {}).get("prefixes", 0)
                    result["prefixes_v6"] = announced.get("v6", {}).get("prefixes", 0)
                    result["prefixes_announced"] = result["prefixes_v4"] + result["prefixes_v6"]

                    visibility = data.get("data", {}).get("visibility", {})
                    v4_vis = visibility.get("v4", {})
                    result["peers_seeing"] = v4_vis.get("total_peers", 0)
                    ris_peers = v4_vis.get("ris_peers_seeing", 0)
                    total_ris = v4_vis.get("total_ris_peers", 1)

                    if total_ris > 0:
                        result["visibility_pct"] = round((ris_peers / total_ris) * 100, 1)

                    # Significant drop = less than 50% visibility
                    result["visibility_drop"] = result["visibility_pct"] < 50

                # Also check for BGP announcements
                resp2 = await client.get(
                    f"{self.BASE_URL}/announced-prefixes/data.json",
                    params={"resource": f"AS{asn}"},
                )
                if resp2.status_code == 200:
                    prefix_data = resp2.json()
                    prefixes = prefix_data.get("data", {}).get("prefixes", [])
                    result["announced_prefixes"] = [
                        {"prefix": p.get("prefix"), "timelines": len(p.get("timelines", []))}
                        for p in prefixes[:20]  # limit to 20
                    ]

        except httpx.TimeoutException:
            result["error"] = "timeout"
            logger.warning(f"BGP Looking Glass timeout for ASN {asn}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"BGP Looking Glass error for ASN {asn}: {e}")

        self._last_check[cache_key] = now
        self._cache[cache_key] = result
        return result

    async def check_isp(self, isp_slug: str) -> Dict[str, Any]:
        asn = SA_ISP_ASNS.get(isp_slug)
        if not asn:
            return {"status": "unknown_isp", "isp": isp_slug}
        return await self.check_asn(asn)


# ===================================================================
# 6. ISP Webhook Handler
# ===================================================================
class ISPWebhookHandler:
    """Receives inbound push webhooks from ISPs with HMAC-SHA256 verification."""

    def __init__(self):
        self.enabled = WEBHOOK_ENABLED
        self.signature_header = WEBHOOK_SIGNATURE_HEADER
        self._secrets: Dict[str, str] = {}  # isp_slug -> signing secret
        self._recent_webhooks: Dict[str, List[Dict]] = {}  # isp_slug -> [payloads]

    def register_secret(self, isp_slug: str, secret: str) -> None:
        """Register a webhook signing secret for an ISP."""
        self._secrets[isp_slug] = secret
        logger.info(f"Webhook secret registered for {isp_slug}")

    def verify_signature(self, isp_slug: str, payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature on an incoming webhook."""
        secret = self._secrets.get(isp_slug)
        if not secret:
            logger.warning(f"No webhook secret registered for {isp_slug}")
            return False

        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        # Support both raw hex and "sha256=hex" prefix format
        sig_clean = signature.replace("sha256=", "")
        return hmac.compare_digest(expected, sig_clean)

    async def process_webhook(
        self, isp_slug: str, payload: Dict[str, Any], signature: Optional[str] = None, raw_body: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Process an incoming ISP status webhook."""
        if not self.enabled:
            return {"status": "disabled"}

        result: Dict[str, Any] = {
            "provider": "webhook",
            "isp": isp_slug,
            "received_at": datetime.now(SAST).isoformat(),
            "verified": False,
            "payload": payload,
        }

        # Verify signature if available
        if signature and raw_body and isp_slug in self._secrets:
            result["verified"] = self.verify_signature(isp_slug, raw_body, signature)
            if not result["verified"]:
                logger.warning(f"Invalid webhook signature from {isp_slug}")
                result["warning"] = "signature_verification_failed"
        elif isp_slug in self._secrets:
            result["warning"] = "signature_missing"
        else:
            result["verified"] = True  # no secret registered, accept unsigned

        # Store webhook
        if isp_slug not in self._recent_webhooks:
            self._recent_webhooks[isp_slug] = []
        self._recent_webhooks[isp_slug].append(result)
        # Keep last 100 webhooks per ISP
        if len(self._recent_webhooks[isp_slug]) > 100:
            self._recent_webhooks[isp_slug] = self._recent_webhooks[isp_slug][-100:]

        logger.info(f"Webhook received from {isp_slug}: verified={result['verified']}")
        return result

    def get_recent(self, isp_slug: str, limit: int = 20) -> List[Dict]:
        """Get recent webhooks for an ISP."""
        return self._recent_webhooks.get(isp_slug, [])[-limit:]


# ===================================================================
# Orchestrator — NetworkingIntegrationManager
# ===================================================================
class NetworkingIntegrationManager:
    """Initialises all providers and runs check_all() concurrently."""

    def __init__(self):
        self.enabled = NETWORKING_INTEGRATIONS_ENABLED
        self.cloudflare = CloudflareRadarProvider()
        self.ioda = IODAProvider()
        self.ripe_atlas = RIPEAtlasProvider()
        self.statuspage = StatuspageProvider()
        self.bgp = BGPLookingGlassProvider()
        self.webhook = ISPWebhookHandler()
        self._providers = {
            "cloudflare_radar": self.cloudflare,
            "ioda": self.ioda,
            "ripe_atlas": self.ripe_atlas,
            "statuspage_api": self.statuspage,
            "bgp_looking_glass": self.bgp,
            "webhook": self.webhook,
        }
        logger.info(
            f"NetworkingIntegrationManager initialised: master={'ON' if self.enabled else 'OFF'}, "
            f"cloudflare={'ON' if self.cloudflare.enabled else 'OFF'}, "
            f"ioda={'ON' if self.ioda.enabled else 'OFF'}, "
            f"ripe_atlas={'ON' if self.ripe_atlas.enabled else 'OFF'}, "
            f"statuspage={'ON' if self.statuspage.enabled else 'OFF'}, "
            f"bgp={'ON' if self.bgp.enabled else 'OFF'}, "
            f"webhooks={'ON' if self.webhook.enabled else 'OFF'}"
        )

    async def check_all(self, isp_slug: str) -> Dict[str, Any]:
        """Run all enabled providers concurrently for a given ISP."""
        if not self.enabled:
            return {"status": "disabled", "isp": isp_slug}

        results: Dict[str, Any] = {
            "isp": isp_slug,
            "checked_at": datetime.now(SAST).isoformat(),
            "providers": {},
        }

        tasks = {}
        if self.cloudflare.enabled:
            tasks["cloudflare_radar"] = self.cloudflare.check_isp(isp_slug)
        if self.ioda.enabled:
            tasks["ioda"] = self.ioda.check_isp(isp_slug)
        if self.ripe_atlas.enabled:
            tasks["ripe_atlas"] = self.ripe_atlas.check_isp(isp_slug)
        if self.statuspage.enabled:
            tasks["statuspage_api"] = self.statuspage.check_isp(isp_slug)
        if self.bgp.enabled:
            tasks["bgp_looking_glass"] = self.bgp.check_isp(isp_slug)

        if not tasks:
            results["status"] = "no_providers_enabled"
            return results

        gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for provider_name, result in zip(tasks.keys(), gathered):
            if isinstance(result, Exception):
                results["providers"][provider_name] = {"error": str(result)}
                logger.error(f"Provider {provider_name} failed for {isp_slug}: {result}")
            else:
                results["providers"][provider_name] = result

        # Add recent webhooks if any
        if self.webhook.enabled:
            recent = self.webhook.get_recent(isp_slug, limit=5)
            if recent:
                results["providers"]["webhook"] = {
                    "provider": "webhook",
                    "isp": isp_slug,
                    "recent_count": len(recent),
                    "latest": recent[-1] if recent else None,
                }

        return results

    async def check_country_health(self) -> Dict[str, Any]:
        """Run a SA-wide internet health overview across all known ISPs."""
        if not self.enabled:
            return {"status": "disabled"}

        result: Dict[str, Any] = {
            "country": "ZA",
            "checked_at": datetime.now(SAST).isoformat(),
            "isps": {},
            "ripe_atlas": {},
            "ioda_country": {},
        }

        # Check all ISPs concurrently
        isp_tasks = {slug: self.check_all(slug) for slug in SA_ISP_ASNS.keys()}
        gathered = await asyncio.gather(*isp_tasks.values(), return_exceptions=True)
        for slug, data in zip(isp_tasks.keys(), gathered):
            if isinstance(data, Exception):
                result["isps"][slug] = {"error": str(data)}
            else:
                result["isps"][slug] = data

        # RIPE Atlas probe overview
        if self.ripe_atlas.enabled:
            try:
                result["ripe_atlas"] = await self.ripe_atlas.check_probes()
            except Exception as e:
                result["ripe_atlas"] = {"error": str(e)}

        # IODA country-level
        if self.ioda.enabled and self.ioda.country_check:
            try:
                result["ioda_country"] = await self.ioda.check_country()
            except Exception as e:
                result["ioda_country"] = {"error": str(e)}

        return result

    def get_provider_status(self) -> Dict[str, Any]:
        """Return the enabled/disabled status of each provider."""
        return {
            "master_enabled": self.enabled,
            "providers": {
                "cloudflare_radar": {
                    "enabled": self.cloudflare.enabled,
                    "has_token": bool(self.cloudflare.token),
                    "check_interval": self.cloudflare.check_interval,
                },
                "ioda": {
                    "enabled": self.ioda.enabled,
                    "country_check": self.ioda.country_check,
                    "check_interval": self.ioda.check_interval,
                },
                "ripe_atlas": {
                    "enabled": self.ripe_atlas.enabled,
                    "has_api_key": bool(self.ripe_atlas.api_key),
                    "check_interval": self.ripe_atlas.check_interval,
                    "sa_probes": len(SA_RIPE_PROBES),
                },
                "statuspage_api": {
                    "enabled": self.statuspage.enabled,
                    "check_interval": self.statuspage.check_interval,
                    "configured_isps": list(ISP_STATUSPAGES.keys()),
                },
                "bgp_looking_glass": {
                    "enabled": self.bgp.enabled,
                    "check_interval": self.bgp.check_interval,
                },
                "webhook": {
                    "enabled": self.webhook.enabled,
                    "registered_isps": list(self.webhook._secrets.keys()),
                    "signature_header": self.webhook.signature_header,
                },
            },
            "sa_isp_asns": SA_ISP_ASNS,
            "sa_ripe_probes": {
                pid: info for pid, info in SA_RIPE_PROBES.items()
            },
        }
