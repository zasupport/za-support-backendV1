# ZA SUPPORT — MEMORY.md (Health Check v11 Backend)
# Last Updated: 12/03/2026 (session: consolidate-chats)
# Purpose: Persistent context across all Claude Code sessions — no knowledge loss between chats

---

## INFRASTRUCTURE STATE

### Repositories
| Repo | Purpose | Hosting | Status |
|------|---------|---------|--------|
| `zasupport/za-support-backendV1` | Health Check v11 backend (CANONICAL) | Render (Frankfurt) | Active — free tier |
| `zasupport/za-support-backend` | **EMPTY/DEPRECATED** — confirmed via git ls-remote (no refs) | N/A | Dead |
| `zasupport/za-support-dashboard` | CyberPulse Dashboard (Next.js) | Vercel | Planned |
| `zasupport/za-diagnostic-v3-engine` | Scout diagnostic engine (Bash) | Client macOS | Active |

### Database
- **Name:** zasupportdb (PostgreSQL, free tier, Frankfurt)
- **RESOLVED:** `za-support-backendV1` IS the canonical repo. `za-support-backend` is empty. CLAUDE.md Section 6 updated.
- **TimescaleDB:** Referenced but requires paid Render plan or self-managed. Free tier = standard PostgreSQL.
- **Tables built:** 17 ORM models across devices, health, diagnostics, ISP, automation, agents
- **Migrations:** 3 Alembic migrations (ISP monitor, agent router, automation layer)

### Redis
- **Name:** zasupport-redis (starter tier, Frankfurt)
- **Usage:** ISP alert cooldown locks (SETNX)

### Deployment
- **render.yaml:** Configured for free tier (1 gunicorn worker, Python 3.11)
- **Procfile:** `web: gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
- **AGENT_AUTH_TOKEN:** FIXED — now uses `generateValue: true` in render.yaml (was hardcoded)
- **Dual-token rotation:** AGENT_AUTH_TOKEN_OLD added for zero-downtime token rotation

---

## PREVIOUS SESSION HISTORY (extracted from git branches)

### Branch: claude/identify-database-chat-LxAki (earliest work)
- Initial upload of backend code
- Modular architecture restructure (core/ + modules/)
- Admin user management endpoints
- Production security hardening (auth, CORS, secrets, rate limiting)
- Auto-migration on startup
- CLAUDE.md created with autonomous execution preferences

### Branch: claude/complete-system-LxAki
- Built complete Backend system v2.0
- Lifespan startup with auto-migration and admin seed
- Tests, CI pipeline, JWT auth cleanup
- Removed Railway config — using Render only

### Branch: claude/fix-render-deploy-LxAki
- Fixed Render deploy: pinned Python 3.11, relaxed dependency versions
- Added Render deploy automation

### Branch: claude/compare-repo-files-inB59
- Ported missing features from old repo: devices, alerts, ISP monitor, encryption, diagnostics
- Session closed after completion

### Branch: claude/health-check-agent-router-i27kL
- Built agent v3.0 bidirectional communication router
- Added ISP outage monitor networking integrations
- Consolidated v3.0: wired detection engine, scheduler/alerts, full test coverage
- Persistent DB storage + diagnostic client agent
- Consolidated project structure: moved root-level modules into app/

### Branch: claude/consolidate-sessions-wZS7l (previous consolidation attempt)
- Session consolidation audit tool and project manifest created
- Separated V1 and V3 into distinct entry points
- Added per-service CORS origins and PORT config
- Removed encryption_key.txt from repo, added ENCRYPTION_KEY env var
- Fixed product descriptions: V1 is the comprehensive client platform, V3 supports it

### Branch: claude/audit-codebase-Q4AeZ (most recent unmerged work)
- **MERGED INTO THIS BRANCH:** dual-token auth, VERSION centralization, code dedup, API docs
- Created HEALTH_CHECK_AI.md (full architecture diagram, API reference, database schema)
- Created HEALTH_CHECK_SCOUT.md (agent config, heartbeat/diagnostic payloads, token rotation)
- Deduplicated version strings → single `settings.VERSION`
- Implemented `_to_device_status()` helper (removed code duplication in agent.py)
- Added dual-token auth support (AGENT_AUTH_TOKEN + AGENT_AUTH_TOKEN_OLD)

---

## WHAT'S BUILT (as of 12/03/2026)

### API Endpoints (50+ across 8 routers)
1. `/health`, `/` — Service health (now uses settings.VERSION)
2. `/api/v1/devices` — Device registration, listing, health submission, history
3. `/api/v1/alerts` — Alert queries, resolution
4. `/api/v1/dashboard` — Overview metrics, device summaries
5. `/api/v1/network` — Network telemetry submission, history
6. `/api/v1/diagnostics` — za_diag_v3.sh JSON upload, search, listing
7. `/api/v1/isp` — ISP providers CRUD, status checks, outages, dashboard (15 endpoints)
8. `/api/v1/agent` — Heartbeat, diagnostic upload, device list/status (dual-token bearer auth)
9. `/api/v1/system` — Events, jobs, automation health

### Services (Background)
- Event bus (publish/subscribe)
- APScheduler (7 scheduled jobs: patch monitor, backup monitor, report gen, stale device, security scan, cleanup, heartbeat rollup)
- ISP monitor (4-layer: status page scrape, Downdetector, HTTP probe, agent connectivity)
- Notification engine (Mailgun + Slack)
- Workshop bridge (external integration point)

### ISP Providers Seeded (13 SA ISPs)
Telkom, Vodacom, MTN, Rain, Afrihost, RSAWEB, Vox, Herotel, Cool Ideas, Stem, Cybersmart, Web Africa, NTT Data

### Documentation (from audit branch, now merged)
- HEALTH_CHECK_AI.md — Full architecture diagram, API reference, database schema
- HEALTH_CHECK_SCOUT.md — Agent config, heartbeat/diagnostic payloads, token rotation guide

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
| Neil Brandt | Unknown | Client |
| Roger Naidoo | Unknown | Client |
| Kim Ayoub | Unknown | Client |
| Steve Pillinger | Unknown | Client |
| Richard Meade | Unknown | Client |
| Linda Forrest | Unknown | Client |
| Zoë Jewell | Unknown | Client |

---

## KEY DECISIONS (Accumulated — all resolved)

1. **Canonical repo:** `zasupport/za-support-backendV1` — RESOLVED, `za-support-backend` is empty/dead
2. **Module architecture:** Every feature in `app/modules/{name}/` with router.py, models.py, service.py, migration SQL, README — modules NEVER import each other
3. **Database pattern:** Current code uses SQLAlchemy ORM. CLAUDE.md mandates asyncpg — alignment needed but not blocking
4. **Event bus for inter-module comms:** `app/services/event_bus.py` (currently basic publish/subscribe)
5. **Open source first:** Always check for 80%+ solution before building custom
6. **AI strategy:** FastAPI-first, Claude Sonnet for speed, Opus for complex, Max for interactive
7. **Microsoft migration:** OneDrive for docs (iCloud deprecated), Graph API for email
8. **9 agents planned:** Phase 1 = Claude Projects, Phase 2 = FastAPI endpoints, Phase 3 = autonomous
9. **Free tier deployment:** Render free (1 worker), will need upgrade for production load
10. **File naming:** ALWAYS spaces, never underscores/hyphens
11. **Currency:** R with space (R 899)
12. **Agent auth token:** FIXED — no longer hardcoded, uses generateValue + dual-token rotation
13. **VERSION string:** Centralized in settings.VERSION = "11.2.0"
14. **V1 vs V3:** V1 is the comprehensive client platform, V3 (diagnostic engine) supports it
15. **Chat consolidation:** 5 chats covering CRM/Sales, Diagnostics, Reports, AI/Agents, Dashboard/Infra

---

## ARCHITECTURE ALIGNMENT ISSUES (tracked, not blocking)

1. **ORM vs asyncpg:** CLAUDE.md mandates asyncpg, but all code uses SQLAlchemy ORM. Accept ORM for now; migrate later if performance requires it.
2. **Module structure:** CLAUDE.md mandates `app/modules/{name}/` but current code uses `app/api/` + `app/services/` + `app/models/`. New modules should use the mandated structure; existing code migrated when touched.
3. **TimescaleDB:** Requires paid Render plan. Standard PostgreSQL works for current scale.

---

## CONSOLIDATED CHAT SESSIONS

| Chat | Scope | Session File |
|------|-------|-------------|
| Chat 1 | CRM, Sales, Upsell, Investec, Check-in | `.claude/sessions/CHAT_1_CRM_SALES.md` |
| Chat 2 | Diagnostics, Scout, ISP, Monitoring | `.claude/sessions/CHAT_2_DIAGNOSTICS_MONITORING.md` |
| Chat 3 | Reports, Assessments, Guides, Medical | `.claude/sessions/CHAT_3_REPORTS_ASSESSMENTS.md` |
| Chat 4 | AI/ML, Agents, Orchestrator, Research | `.claude/sessions/CHAT_4_AI_AGENTS.md` |
| Chat 5 | Dashboard, Render, Vercel, Database | `.claude/sessions/CHAT_5_DASHBOARD_INFRA.md` |

Execution order: Chat 2 → Chat 1 → Chat 3 → Chat 4 → Chat 5 (ongoing)
