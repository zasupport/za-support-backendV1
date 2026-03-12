# Health Check v11

## Repository
- **Canonical repo:** `zasupport/za-support-backendV1` (confirmed 12/03/2026)
- **`za-support-backend` (no V1) is empty/deprecated** — all code lives here
- Version: 11.2.0 (single source of truth in `app/core/config.py:Settings.VERSION`)

## Stack
- FastAPI backend, PostgreSQL + TimescaleDB, Redis, SQLAlchemy 2.0 (asyncpg migration planned), httpx
- Deployed on Render (Frankfurt, free tier)
- Agent runs on client macOS devices, reports every 60s

## API Routers (50+ endpoints)
- `/api/v1/devices` — device registration, health, history
- `/api/v1/alerts` — alert queries, resolution
- `/api/v1/dashboard` — overview metrics, device summaries
- `/api/v1/network` — network telemetry
- `/api/v1/diagnostics` — za_diag_v3.sh JSON ingestion
- `/api/v1/isp` — ISP outage monitor (15 endpoints, 4-layer detection)
- `/api/v1/agent` — heartbeat, diagnostic upload, bearer auth
- `/api/v1/system` — events, jobs, automation status

## Authentication
- Device API: `X-API-Key` header
- Agent API: `Bearer <AGENT_AUTH_TOKEN>` (dual-token rotation supported via AGENT_AUTH_TOKEN_OLD)

## Database
- PostgreSQL (zasupportdb, Frankfurt)
- TimescaleDB hypertables for time-series
- Retention: 90 days detailed, 2 years aggregated
- 13 pre-seeded SA ISPs
- 17 ORM models, 3 Alembic migrations

## Key Files
- `main.py` — FastAPI app init, router registration
- `app/core/config.py` — all settings + VERSION
- `app/core/database.py` — SQLAlchemy engine, session factory
- `app/core/agent_auth.py` — dual-token bearer auth
- `app/services/event_bus.py` — central publish/subscribe
- `app/services/automation_scheduler.py` — 7 APScheduler jobs

## Consolidated Chats (5 sessions)
Session context files in `.claude/sessions/`:
1. CHAT_1_CRM_SALES.md — CRM, sales, upsell, Investec, check-in
2. CHAT_2_DIAGNOSTICS_MONITORING.md — Scout, ISP, agent, automation
3. CHAT_3_REPORTS_ASSESSMENTS.md — guides, medical, physical assessment, PDFs
4. CHAT_4_AI_AGENTS.md — AI profiling, research, 9-agent orchestrator
5. CHAT_5_DASHBOARD_INFRA.md — dashboard, Render, Vercel, database

## Clients
- Dr Evan Shoul → Stem ISP, X-DSL underlying, gateway 192.168.1.252
- Charles Chemel → NTT Data ISP, UniFi Site Manager
- Dr Anton Meyberg → "Dr's Pieterse, Hunt, Meyberg, Laher & Associates"
- Gillian Pearson → MacBook Pro 13" Mid 2012, Catalina, ESET, Movie Magic 6.2
