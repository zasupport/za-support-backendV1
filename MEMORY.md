# ZA SUPPORT — MEMORY.md (Health Check v11 Backend)
# Last Updated: 12/03/2026
# Purpose: Persistent context across all Claude Code sessions — no knowledge loss between chats

---

## INFRASTRUCTURE STATE

### Repositories
| Repo | Purpose | Hosting | Status |
|------|---------|---------|--------|
| `zasupport/za-support-backendV1` | Health Check v11 backend (THIS REPO) | Render (Frankfurt) | Active — free tier |
| `zasupport/za-support-backend` | Original backend (may be deprecated — VERIFY) | Render | Status unclear |
| `zasupport/za-support-dashboard` | CyberPulse Dashboard (Next.js) | Vercel | Planned |
| `zasupport/za-diagnostic-v3-engine` | Scout diagnostic engine (Bash) | Client macOS | Active |

### Database
- **Name:** zasupportdb (PostgreSQL, free tier, Frankfurt)
- **CRITICAL FLAG:** Repo is `za-support-backendV1` but CLAUDE.md Section 6 references `za-support-backend` as the primary backend. Courtney needs to confirm which is canonical.
- **TimescaleDB:** Referenced in CLAUDE.md but not confirmed active on Render free tier (TimescaleDB requires paid plan or self-managed)
- **Tables built:** 17 ORM models across devices, health, diagnostics, ISP, automation, agents
- **Migrations:** 3 Alembic migrations (ISP monitor, agent router, automation layer)

### Redis
- **Name:** zasupport-redis (starter tier, Frankfurt)
- **Usage:** ISP alert cooldown locks (SETNX)

### Deployment
- **render.yaml:** Configured for free tier (1 gunicorn worker, Python 3.11)
- **Procfile:** `web: gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
- **Agent auth token:** Hardcoded in render.yaml (should be moved to Render env var management)

---

## WHAT'S BUILT (as of 12/03/2026)

### API Endpoints (50+ across 8 routers)
1. `/health`, `/` — Service health
2. `/api/v1/devices` — Device registration, listing, health submission, history
3. `/api/v1/alerts` — Alert queries, resolution
4. `/api/v1/dashboard` — Overview metrics, device summaries
5. `/api/v1/network` — Network telemetry submission, history
6. `/api/v1/diagnostics` — za_diag_v3.sh JSON upload, search, listing
7. `/api/v1/isp` — ISP providers CRUD, status checks, outages, dashboard (15 endpoints)
8. `/api/v1/agent` — Heartbeat, diagnostic upload, device list/status (bearer auth)
9. `/api/v1/system` — Events, jobs, automation health

### Services (Background)
- Event bus (publish/subscribe)
- APScheduler (7 scheduled jobs: patch monitor, backup monitor, report gen, stale device, security scan, cleanup, heartbeat rollup)
- ISP monitor (4-layer: status page scrape, Downdetector, HTTP probe, agent connectivity)
- Notification engine (Mailgun + Slack)
- Workshop bridge (external integration point)

### ISP Providers Seeded (13 SA ISPs)
Telkom, Vodacom, MTN, Rain, Afrihost, RSAWEB, Vox, Herotel, Cool Ideas, Stem, Cybersmart, Web Africa, NTT Data

---

## WHAT'S NOT BUILT (Planned Modules)

| Module | Priority | Chat Assignment |
|--------|----------|-----------------|
| sales_crm | HIGH | Chat 1 |
| checkin_trigger | HIGH | Chat 1 |
| customer_guides | MEDIUM-HIGH | Chat 3 |
| medical_practice | MEDIUM-HIGH | Chat 3 |
| physical_assessment | MEDIUM-HIGH | Chat 3 |
| deduplication | MEDIUM | Chat 2 |
| ai_profiling | MEDIUM | Chat 4 |
| research_module | MEDIUM | Chat 4 |

---

## CLIENT STATE

| Client | ISP | Key Details |
|--------|-----|-------------|
| Dr Evan Shoul | Stem (X-DSL underlying) | Gateway 192.168.1.252, UniFi Express 7 |
| Charles Chemel | NTT Data | UniFi Site Manager |
| Dr Anton Meyberg | Unknown | "Dr's Pieterse, Hunt, Meyberg, Laher & Associates" |
| Gillian Pearson | Unknown | MacBook Pro 13" Mid 2012, Catalina, ESET, Movie Magic 6.2 |

---

## KEY DECISIONS (Accumulated)

1. **Module architecture:** Every feature in `app/modules/{name}/` with router.py, models.py, service.py, migration SQL, README — modules NEVER import each other
2. **Database pattern:** asyncpg for queries, NOT ORM — but current code uses SQLAlchemy ORM (needs alignment)
3. **Event bus for inter-module comms:** `app/services/event_bus.py` (currently basic publish/subscribe)
4. **Open source first:** Always check for 80%+ solution before building custom
5. **AI strategy:** FastAPI-first, Claude Sonnet for speed, Opus for complex, Max for interactive
6. **Microsoft migration:** OneDrive for docs (iCloud deprecated), Graph API for email
7. **9 agents planned:** Phase 1 = Claude Projects, Phase 2 = FastAPI endpoints, Phase 3 = autonomous
8. **Free tier deployment:** Render free (1 worker), will need upgrade for production load
9. **File naming:** ALWAYS spaces, never underscores/hyphens
10. **Currency:** R with space (R 899)

---

## REPO NAMING CONCERN (FLAGGED 12/03/2026)

CLAUDE.md Section 6 lists the primary backend as:
```
/Users/courtneybentley/Developer/za-support-backend/ → zasupport/za-support-backend
```

But this repo is `zasupport/za-support-backendV1`. Courtney flagged this as potentially incorrect.

**ACTION REQUIRED:** Confirm which repo/database is canonical:
- `za-support-backend` (original, referenced in CLAUDE.md)
- `za-support-backendV1` (this repo, currently active on Render)

If V1 is the correct one, update CLAUDE.md Section 6. If original is correct, migrate code there.

---

## ARCHITECTURE ALIGNMENT ISSUES

1. **ORM vs asyncpg:** CLAUDE.md mandates asyncpg, but all current code uses SQLAlchemy ORM. Decision needed: migrate to asyncpg or accept ORM.
2. **Module structure:** CLAUDE.md mandates `app/modules/{name}/` but current code uses `app/api/` + `app/services/` + `app/models/`. Not yet migrated to module pattern.
3. **TimescaleDB:** Referenced but may not be available on Render free tier.
4. **Agent auth token:** Hardcoded in render.yaml — should use Render's secret management.
