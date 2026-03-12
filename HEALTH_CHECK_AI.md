# Health Check AI — Backend API & Automation Platform

Health Check AI is the FastAPI backend that ingests telemetry, runs automated monitoring, and powers the ZA Support dashboard.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────────────────────────┐
│ Scout Agents │────▶│              │     │ Automation Layer                      │
│ (Mac fleet)  │     │   FastAPI    │────▶│ ├── Patch Monitor (6h)               │
├─────────────┤     │   Backend    │     │ ├── Backup Monitor (6h)              │
│ za_diag_v3  │────▶│              │     │ ├── Security Posture Scan (12h)      │
│   script    │     │ api.zasupport│     │ ├── Stale Device Check (1h)          │
├─────────────┤     │   .com       │     │ ├── Report Generator (daily 06:00)   │
│ Dashboard   │────▶│              │     │ ├── Heartbeat Rollup (daily 02:00)   │
│ (Next.js)   │     │              │     │ └── Event Cleanup (monthly)          │
└─────────────┘     └──────┬───────┘     └───────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼────┐ ┌─────▼─────┐
        │PostgreSQL │ │  Redis  │ │ Mailgun + │
        │TimescaleDB│ │(cooldown│ │  Slack    │
        └──────────┘ │ + rate) │ │(alerts)   │
                      └─────────┘ └───────────┘
```

## Quick Start

```bash
# Local development
pip install -r requirements.txt
DATABASE_URL=postgresql://user:pass@localhost:5432/hcdb python main.py

# Run test suite
bash test_api.sh http://localhost:8080 <your-api-key>
```

## API Reference

### Authentication

| Endpoint Group | Auth Method | Header |
|---------------|-------------|--------|
| Devices, Alerts, Dashboard, Network, ISP, Diagnostics (read) | API Key | `X-API-Key: <API_KEY>` |
| Agent endpoints | Bearer Token | `Authorization: Bearer <AGENT_AUTH_TOKEN>` |
| Diagnostic upload, Agent health | None | — |
| System events/jobs/status | None | — |

### Endpoint Map

| Prefix | Router | Endpoints |
|--------|--------|-----------|
| `/health` | `health.py` | Service liveness probe |
| `/api/v1/devices` | `devices.py` | Register, health submit, list, history |
| `/api/v1/alerts` | `alerts.py` | List, resolve, resolve-all |
| `/api/v1/dashboard` | `dashboard.py` | Overview (aggregated device + alert status) |
| `/api/v1/network` | `network.py` | Submit + history (UniFi controllers) |
| `/api/v1/diagnostics` | `diagnostics.py` | Upload, list, get, compare |
| `/api/v1/isp` | `isp.py` | 15 endpoints: providers CRUD, checks, outages, heartbeat, dashboard, seed |
| `/api/v1/agent` | `agent.py` | Heartbeat, diagnostics, devices, health |
| `/api/v1/system` | `system.py` | Events, jobs, automation status |

## Database Schema

### Core Tables

| Table | Purpose | Type |
|-------|---------|------|
| `devices` | Device registry (machine_id PK) | Standard |
| `health_data` | Health telemetry from devices | Standard |
| `alerts` | Generated alerts (threshold-based) | Standard |
| `network_data` | UniFi controller telemetry | Standard |
| `workshop_diagnostics` | Full `za_diag_v3.sh` snapshots (215 data points) | Standard |

### Agent Tables

| Table | Purpose | Type |
|-------|---------|------|
| `agent_heartbeats` | 60s telemetry from Scout agents | TimescaleDB hypertable (1-day chunks, 90-day retention) |
| `diagnostic_reports` | Full JSON uploads via agent | JSONB + GIN index |

### ISP Monitor Tables

| Table | Purpose | Type |
|-------|---------|------|
| `isp_providers` | 13 pre-seeded SA ISPs | Standard |
| `isp_status_checks` | Time-series check results (4 layers) | TimescaleDB hypertable |
| `agent_connectivity` | Agent heartbeat for ISP tracking | TimescaleDB hypertable |
| `isp_outages` | Confirmed outage events | Standard |

### Automation Tables

| Table | Purpose | Type |
|-------|---------|------|
| `system_events` | Central event bus log | Standard |
| `scheduled_jobs` | Job registry (7 jobs) | Standard |
| `patch_status` | macOS version tracking per device | Standard |
| `backup_status` | Time Machine + third-party backup tracking | Standard |
| `notification_log` | Email + Slack notification audit trail | Standard |

## ISP Outage Monitor — 4-Layer Detection

| Layer | Source | Method | Thresholds |
|-------|--------|--------|------------|
| 1 | Status pages | Scrape Statuspage.io + keyword scan | Statuspage components or keywords |
| 2 | Downdetector ZA | Report count parsing | <50=OK, 50-200=degraded, >200=outage |
| 3 | HTTP probes | HEAD request to probe_targets | >5s=degraded, timeout=outage, 5xx=outage |
| 4 | Agent connectivity | devices.last_seen vs timeout | 2+ agents offline=ISP issue |

**Confirmation logic**: N consecutive unhealthy checks → 2+ sources = confirmed outage, 1 source = degraded.

## Automation Scheduled Jobs

| Job ID | Schedule | Function |
|--------|----------|----------|
| `patch_monitor` | Every 6h | Check device OS vs latest macOS |
| `backup_monitor` | Every 6h | Check Time Machine + third-party backup status |
| `report_generator` | Daily 06:00 | Generate per-device health reports |
| `stale_device_check` | Every 1h | Flag devices not seen for 24h+ |
| `security_posture_scan` | Every 12h | Check SIP, FileVault, Firewall, Gatekeeper |
| `event_cleanup` | Monthly | Remove system events older than 90 days |
| `heartbeat_rollup` | Daily 02:00 | Refresh TimescaleDB continuous aggregate |

## Environment Variables

### Required

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `API_KEY` | Dashboard/API authentication |
| `ENCRYPTION_KEY` | Fernet key for sensitive telemetry encryption |
| `AGENT_AUTH_TOKEN` | Bearer token for Scout agents |

### Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_AUTH_TOKEN_OLD` | `""` | Previous token for zero-downtime rotation |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable debug mode |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for rate limiting + cooldowns |
| `ISP_MONITOR_ENABLED` | `false` | Enable ISP outage monitor |
| `ISP_MONITOR_STATUS_PAGE_CHECK_INTERVAL` | `300` | Seconds between ISP checks |
| `ISP_MONITOR_AGENT_HEARTBEAT_TIMEOUT` | `180` | Seconds before agent considered offline |
| `ISP_MONITOR_OUTAGE_CONFIRMATION_THRESHOLD` | `3` | Consecutive unhealthy checks to confirm |
| `ISP_MONITOR_OUTAGE_DEGRADED_THRESHOLD` | `10.0` | Degraded score threshold |
| `ISP_MONITOR_ALERT_COOLDOWN_MINS` | `30` | Minutes between duplicate ISP alerts |
| `ALLOWED_ORIGINS` | `zasupport.com,app.zasupport.com,localhost:3000` | CORS origins |

### Notification Variables

| Variable | Purpose |
|----------|---------|
| `HC_NOTIFY_MAILGUN_API_KEY` | Mailgun API key |
| `HC_NOTIFY_MAILGUN_DOMAIN` | Mailgun sending domain |
| `HC_NOTIFY_MAILGUN_FROM` | From address |
| `HC_NOTIFY_EMAIL_TO` | Alert recipient email |
| `HC_NOTIFY_SLACK_WEBHOOK` | Slack incoming webhook URL |

### Alert Thresholds

| Variable | Default | Purpose |
|----------|---------|---------|
| `CPU_CRITICAL` | `90` | CPU % for critical alert |
| `CPU_WARNING` | `75` | CPU % for warning alert |
| `MEMORY_CRITICAL` | `90` | Memory % for critical alert |
| `MEMORY_WARNING` | `80` | Memory % for warning alert |
| `DISK_CRITICAL` | `90` | Disk % for critical alert |
| `DISK_WARNING` | `80` | Disk % for warning alert |
| `BATTERY_CRITICAL` | `20` | Battery % for critical alert |
| `THREAT_CRITICAL` | `7` | Threat score for critical alert |

## Deployment (Render)

Defined in `render.yaml`:
- **Web service**: `zasupport-api` (free plan, Python, gunicorn + uvicorn worker)
- **Database**: `zasupportdb` (PostgreSQL, Frankfurt region)
- **Redis**: `zasupport-redis` (starter plan, Frankfurt region)

### Deploy Commands

```bash
# Build
pip install -r requirements.txt

# Start
gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
```

### Migrations

```bash
# Run automation layer migration
DATABASE_URL=<render_url> bash deploy_migrations.sh

# Or via Alembic
alembic upgrade head
```

## File Structure

```
app/
├── api/
│   ├── agent.py          # Scout agent endpoints (bearer auth)
│   ├── alerts.py         # Alert management
│   ├── dashboard.py      # Aggregated overview
│   ├── devices.py        # Device registration + health
│   ├── diagnostics.py    # za_diag_v3.sh upload + compare
│   ├── health.py         # Liveness probe
│   ├── isp.py            # ISP outage monitor (15 endpoints)
│   ├── network.py        # UniFi controller telemetry
│   └── system.py         # Event bus + job status
├── core/
│   ├── agent_auth.py     # Bearer token auth (dual-token support)
│   ├── auth.py           # API key auth
│   ├── config.py         # Settings (single source of truth for VERSION)
│   ├── database.py       # SQLAlchemy engine + session
│   └── encryption.py     # Fernet encryption for sensitive data
├── models/
│   ├── models.py         # 15 ORM models
│   └── schemas.py        # Pydantic v2 request/response schemas
├── services/
│   ├── alert_engine.py   # Threshold-based alert generation
│   ├── automation_scheduler.py  # APScheduler job management
│   ├── backup_monitor.py # Time Machine + third-party backup checks
│   ├── event_bus.py      # Central event publication
│   ├── isp_monitor.py    # 4-layer ISP detection engine
│   ├── isp_scheduler.py  # ISP check scheduler
│   ├── isp_seed.py       # 13 SA ISP provider definitions
│   ├── notification_engine.py  # Mailgun + Slack notifications
│   ├── patch_monitor.py  # macOS version tracking
│   ├── report_generator.py    # Device health report generation
│   └── workshop_bridge.py     # HC ↔ diagnostic correlation
└── migrations/
    └── versions/
        ├── 001_add_isp_outage_monitor.py
        ├── 002_add_agent_router.py
        └── 003_add_automation_layer.py
```

## Pre-seeded ISP Providers (13)

Afrihost, Axxess, Cool Ideas, MWEB, Rain, RSAWeb, Telkom, Vox, WebAfrica, Herotel, Metrofibre, Vumatel, Stem

Seed via: `POST /api/v1/isp/seed` (requires API key)
