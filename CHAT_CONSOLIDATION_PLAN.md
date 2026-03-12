# ZA SUPPORT — CHAT CONSOLIDATION PLAN
# Date: 12/03/2026
# Purpose: Reduce chat sprawl to 5 focused, comprehensive sessions

---

## CURRENT STATE

The ZA Support ecosystem spans 21 CLAUDE.md sections, 9 planned agents, 8+ planned modules,
and multiple active services. Work is currently scattered across multiple chat sessions covering
overlapping topics. This plan consolidates everything into **5 focused chats**.

### What Exists (Built)
- Health Check v11 backend (FastAPI, deployed on Render)
- ISP Outage Monitor (4-layer detection, 13 SA ISPs seeded)
- Agent Router (heartbeat telemetry, diagnostic uploads, device status)
- Automation Layer (event bus, scheduler, monitors, notifications)
- Core infrastructure (auth, encryption, database, config)
- API endpoints: diagnostics, devices, dashboard, network, ISP, alerts, health, agent

### What's Planned (Not Yet Built)
- customer_guides module
- ai_profiling module (ML segmentation)
- physical_assessment module (Flipper Zero + photo pipeline)
- research_module (weekly tech digest)
- checkin_trigger (6-month re-engagement)
- sales_crm module (CRM + upsell engine + Investec scanner)
- medical_practice module
- deduplication module
- 9 AI agents (Phase 2: FastAPI endpoints, Phase 3: autonomous)
- Dashboard (separate Next.js repo)

---

## THE 5 CHATS

### CHAT 1: CRM, Sales & Client Management
**Scope:** Everything client-facing from first contact to ongoing relationship

**Covers:**
- `sales_crm` module — full build (crm_contacts, crm_opportunities, crm_activities, upsell_products, upsell_recommendations, sales_outcomes)
- Investec client scanner (daily email scan via Microsoft Graph API)
- Customer segmentation (medical_practice / sme / individual / family)
- Upsell recommendation engine (diagnostic findings → product mapping → conversion tracking)
- Warranty colour bands and repair-vs-replace framework
- Device lifecycle tracking and replacement alerts
- 6-month check-in trigger (`checkin_trigger` module)
- Client profile management and opportunity tracking
- Agent 02 (Client Intelligence), Agent 06 (Upsell & Recommendation), Agent 09 (Warranty & Pricing)

**Key Tables:** crm_contacts, crm_opportunities, crm_activities, upsell_products, upsell_recommendations, sales_outcomes, device_lifecycle

**API Prefix:** /api/v1/sales/, /api/v1/checkin/

**Priority:** HIGH — directly serves current clients and revenue

---

### CHAT 2: Diagnostics, Scout & Monitoring
**Scope:** All data collection, monitoring, and diagnostic intelligence

**Covers:**
- Health Check Scout (19 phases) — diagnostic engine integration
- ISP Outage Monitor (already built — maintain and extend)
- Agent Router (already built — heartbeat, telemetry, device status)
- Automation layer (event bus, scheduler, monitors, notifications)
- Backup monitor, patch monitor
- `deduplication` module (rmlint/jdupes, duplicate_gb_recoverable metric)
- Deep Security Intelligence (Phase 19 — process ancestry, code signing, DNS, firmware)
- Competitive intelligence framework (ESET/Norton/etc analysis)
- CyberShield integration points
- Agent 01 (Scout)

**Key Existing Files:** app/services/isp_monitor.py, event_bus.py, automation_scheduler.py, backup_monitor.py, patch_monitor.py, alert_engine.py, notification_engine.py, app/api/isp.py, agent.py, diagnostics.py, alerts.py

**API Prefix:** /api/v1/isp/, /api/v1/diagnostics/, /api/v1/agent/, /api/v1/alerts/

**Priority:** HIGH — core value proposition, already partially built

---

### CHAT 3: Reports, Assessments & Knowledge Base
**Scope:** All output generation — reports, assessments, guides, templates

**Covers:**
- `customer_guides` module (knowledge base, guide_feedback, guide_client_links)
- `medical_practice` module (HPCSA/POPIA compliance, GoodX/Elixir integrations, 12-15 page assessment PDFs)
- `physical_assessment` module (photo→asset register pipeline, Flipper Zero red-team results)
- IT Assessment field process (pre-visit, on-site, report delivery, instant activation)
- Report generation service (ReportLab Platypus, branded PDFs)
- Dr Templates integration
- Agent 03 (Medical Practice), Agent 04 (SME Business), Agent 08 (Report Generation)

**Key Tables:** guides, guide_client_links, guide_feedback, physical_assessments, asset_register

**API Prefix:** /api/v1/guides/, /api/v1/assessments/, /api/v1/medical/

**Priority:** MEDIUM-HIGH — enables service delivery and client-facing output

---

### CHAT 4: AI/ML, Agents & Automation
**Scope:** All AI-powered features, agent orchestration, and intelligent automation

**Covers:**
- `ai_profiling` module (scikit-learn clustering, pgvector, sentence-transformers)
- `research_module` (HN/ArXiv/ProductHunt scraping, weekly digest)
- 9-Agent Registry architecture (Phase 1 → Phase 2 → Phase 3 roadmap)
- Agent orchestrator and event routing
- FastAPI-first AI service (specialised system prompts, structured JSON outputs)
- Claude API integration strategy (Sonnet for speed, Opus for complex)
- Token usage tracking per module
- Cross-client pattern detection ("4/5 clients on macOS 12 have the same issue")
- Microsoft Graph API integration (OneDrive, M365 email)
- Agent 05 (Consumer & Family), Agent 07 (Marketing & Outreach)

**Key Tables:** agent_events, agent_tasks, agent_logs, ai_profiles, research_digests

**API Prefix:** /api/v1/ai/, /api/v1/research/, /api/v1/agents/

**Priority:** MEDIUM — Phase 2+ work, foundational for scale

---

### CHAT 5: Dashboard, Infrastructure & DevOps
**Scope:** Frontend, deployment, infrastructure, and operational concerns

**Covers:**
- CyberPulse Dashboard (Next.js + Tailwind + shadcn/ui — separate repo)
- Dashboard API endpoints (app/api/dashboard.py — already exists)
- Render deployment (render.yaml, deploy.sh, Frankfurt region)
- Vercel deployment (dashboard frontend)
- Database management (PostgreSQL + TimescaleDB, migrations, retention policies)
- Redis configuration (cache, real-time, SETNX locks)
- Environment variable management
- Health check endpoints and monitoring
- Mobile-first design for Courtney's iPhone
- Web automation (Playwright scripts for Render/Vercel config)
- DocuSeal (e-signature), PayFast/Peach/Netcash (payments)
- Business exit/sale alignment (clean APIs, documentation, no knowledge silos)

**Key Existing Files:** render.yaml, deploy.sh, Procfile, requirements.txt, app/core/database.py, app/core/config.py, app/api/dashboard.py, app/api/health.py

**Priority:** ONGOING — supports all other chats

---

## CROSS-CHAT RULES

1. **CLAUDE.md is the single source of truth** — all 5 chats read it at session start
2. **MEMORY.md tracks decisions** — every chat writes to it after lasting decisions
3. **Modules NEVER import each other** — use event bus (app/core/event_bus.py)
4. **No duplicate work** — check MEMORY.md before starting any task
5. **Duplicate chat detection** — run at start of every session per Rule 2.20

## CHAT-TO-AGENT MAPPING

| Chat | Agents |
|------|--------|
| Chat 1 (CRM/Sales) | Agent 02, 06, 09 |
| Chat 2 (Diagnostics) | Agent 01 |
| Chat 3 (Reports) | Agent 03, 04, 08 |
| Chat 4 (AI/Agents) | Agent 05, 07 + Orchestrator |
| Chat 5 (Dashboard/Infra) | None (infrastructure layer) |

## CHAT-TO-MODULE MAPPING

| Chat | Modules to Build |
|------|-----------------|
| Chat 1 | sales_crm, checkin_trigger |
| Chat 2 | deduplication (+ maintain ISP, agent_router, automation) |
| Chat 3 | customer_guides, medical_practice, physical_assessment |
| Chat 4 | ai_profiling, research_module |
| Chat 5 | No new modules (infra + dashboard) |

## EXECUTION ORDER

1. **Chat 2** first — diagnostics are the data source for everything else
2. **Chat 1** second — CRM/sales directly serves current clients (priority rule)
3. **Chat 3** third — reports and guides need diagnostic data + client profiles
4. **Chat 4** fourth — AI/ML builds on top of collected data
5. **Chat 5** ongoing — infrastructure supports all chats continuously
