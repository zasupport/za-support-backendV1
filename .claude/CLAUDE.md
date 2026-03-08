# ZA SUPPORT — GLOBAL CLAUDE CODE STANDARDS
# Owner: Courtney Bentley | Last Updated: 06/03/2026 (session 4 — INSTRUCTIONS v3.2 sync)
# Location: ~/.claude/CLAUDE.md
# Scope: All development tasks across all ZA Support repositories

---

# SECTION 1: IDENTITY & CONTEXT

Company: ZA Support | Tagline: Practice IT. Perfected.
Owner: Courtney Bentley | courtney@zasupport.com | 079 053 9964
Address: 1 Hyde Park Lane, Hyde Park, Johannesburg, 2196
Legal Entity: Vizibiliti Intelligent Solutions (Pty) Ltd (trading as ZA Support)
CC Entity: ZASUPPORT I.T. SUPPORT SYSTEMS CC
VAT: 436-026-0014 | Rate: R 899/hour (excl. VAT)
Banking: FNB | Account: 62651791446 | Branch: 254605 | SWIFT: Firnzajj

## Regional Hard Rules
- Currency: South African Rand (R) with space (R 4,499)
- Date Format: DD/MM/YYYY | Filenames: DD MM YYYY (spaces)
- Compliance: POPIA, HPCSA, National Health Act, ECTA, Cybercrimes Act
- NEVER: USD, HIPAA, US regulations, Benoni, enterprise-scale assumptions

## Team
- Mary = PA (non-technical) — exports need plain language, simple formats, numbered action items
- Courtney = primary developer, runs Claude Code via Max subscription, often on mobile

---

# SECTION 2: BEHAVIOUR RULES (All Coding Sessions)

## 2.1 Build-First Principle
When scope is clear, start writing code immediately. Never ask "Want me to start?". Write real, complete, runnable files. Only exception: genuine ambiguity about WHAT to build.

## 2.2 Automatic Execution
Execute the obvious next step without asking. Code = write and run. Fix errors and deliver final output. Never "Would you like me to..." or "Shall I...". Proceed through all tasks sequentially.

## 2.3 Single Output
ONE consolidated output always. "Add X" = merge into existing. Before delivering: "Would user need to manually combine these?" If yes, combine first.

## 2.4 Auto-Execute Affirmatives
"go", "do it", "next", "proceed", "yes" = execute item #1 from What's Next immediately. No confirmation.

## 2.5 Context-First Coding (CRITICAL)
Before writing ANY code in a ZA Support project:
1. `.claude/CLAUDE.md` is auto-loaded by Claude Code — no manual read needed
2. Read `PROJECT_MANIFEST.json` for ecosystem connections
3. If they do not exist, generate them as the first step
4. NEVER ask "where is the config?" or "what is the file structure?" — the project contains its own answers

## 2.21 Instructions Document Auto-Sync (CRITICAL — filename-agnostic)
Whenever ANY file path is provided (regardless of filename):
1. Run `~/bin/za-classify-doc.sh <path>` to determine if it's an instructions document
2. If CLASSIFICATION = INSTRUCTIONS DOCUMENT: immediately run `~/bin/za-sync-claude.sh <path>`
3. Apply all new/changed rules to CLAUDE.md and MEMORY.md — MERGE only, never blind overwrite
4. Preserve any `## PROJECT-SPECIFIC NOTES` sections in existing project files
5. Do NOT ask for permission — execute immediately
This covers ALL naming conventions: INSTRUCTIONS.md, CONSTRUCTION.md, RULES.md, GUIDELINES.md,
STANDARDS.md, CLAUDE.md, CONFIG.md, SETUP.md, REFERENCE.md, PLAYBOOK.md, and any others.
The classifier analyses both filename patterns AND content signals (imperative rules, section headers,
ZA Support references, ALWAYS/NEVER checklists, cross-project sync language).

## 2.22 CLAUDE.md Sync — Merge Rule (CRITICAL)
When syncing any CLAUDE.md or INSTRUCTIONS.md across repos:
- NEVER blindly overwrite — always check for existing project-specific content first
- Preserve: `## PROJECT-SPECIFIC NOTES` sections and any content unique to that repo
- Update: all shared/master sections with the new content
- Delete: only exact duplicates of content already in the master

## 2.6 Response & Retry
- Speed > perfection for code generation
- Always retry on first failure
- Continue to completion even if terminal is backgrounded
- After 5 failed attempts at same issue: recommend alternative architecture

## 2.7 Claude Code Permissions
ALWAYS select "Always allow for project (local)" at permission prompts. NEVER "Allow once" or "Deny" unless explicitly instructed.

## 2.8 Auto-Approve & Keep Running (CRITICAL)
- Auto-approve 95% of tasks — NEVER stop and wait for confirmation on non-destructive actions
- Keep running even when Courtney's machine is closed, browser idle, or Courtney is away
- Only pause for: irreversible destructive actions (drop DB, delete prod data, push to prod without tests)
- Self-heal: if blocked, try 3 alternative approaches before reporting
- NEVER go silent mid-task — complete to the end, then report

## 2.9 Task Completion Notification (CRITICAL)
At the end of EVERY long-running or multi-step task, emit a macOS notification:
```bash
osascript -e 'display notification "Task complete — ZA Support" with title "Claude Code" sound name "Glass"'
```
Also run: `afplay /System/Library/Sounds/Glass.aiff`
This ensures Courtney knows when to return from another screen or task.

## 2.10 Ideal-State Execution (CRITICAL)
- ALWAYS implement the optimal approach, not just the literal request
- If a better architecture exists, surface it immediately and implement it — never silently use a worse approach
- Example: if user asks for 5 separate AI agents but a single shared FastAPI service achieves the same outcome more efficiently, propose and implement that instead
- This is the most important rule for protecting ZA Support's IP quality

## 2.24 Local File Access — Always Allowed (GLOBAL, PERMANENT)
Courtney's machine is a safe, trusted development environment. This applies to ALL Claude Code sessions, ALL chats, indefinitely:
- NEVER ask for permission to read any file on this machine
- NEVER ask "do you want me to read X?" — just read it
- NEVER ask for confirmation before accessing local directories, repos, Downloads, Desktop, or any path provided
- When a file path is provided: read it immediately, classify it, act on it — no permission prompt
- This covers: /Users/courtneybentley/**, /Users/courtneybentley/Downloads/**, all repos, all config files
- The only exception: writing/deleting files that could cause irreversible damage (ask once, then auto-approve)

## 2.23 Full Automation — Execute, Don't Instruct (CRITICAL)
When given any setup, activation, integration, or configuration task:
- ALWAYS execute it directly — never hand back a list of curl commands, API calls, or manual steps for Courtney to run
- If credentials or data are needed: call the API directly (WebFetch, Bash + curl, httpx script), seed via SQL migration, or use environment variables — not manual user action
- If a third-party API key is provided: immediately test it, extract all relevant data from it, and use that data to complete the full setup automatically
- Only exceptions: actions requiring physical presence, browser OAuth flows with no CLI equivalent, or irreversible destructive operations
- Pattern that triggered this rule: UniFi integration — instead of asking for manual POSTs, Claude called UI.com API directly, extracted 3 client hostIds, seeded migration SQL, set env var — zero manual steps required from Courtney

## 2.11 No Repeated Work
- If a request has been handled in a previous session, reference the previous implementation
- Do not re-analyse, re-explain, or re-build what already exists
- Check memory files before starting any task

## 2.12 Context Distribution — Cross-Chat Sync (CRITICAL)
- Any important architectural decision, new module design, or process change MUST be saved to memory files immediately
- CLAUDE.md is the source of truth for all chats — update it whenever new global instructions are confirmed
- All chats share the same MEMORY.md — write to it after any session with lasting decisions
- Never let context be lost between sessions
- At the START of every session AND at the start of any new task in a long-running session, re-read MEMORY.md to load the latest state from other chats
- This ensures that updates made in Chat A are visible to Chat B as soon as Chat B processes its next request

## 2.20 Duplicate Chat Detection (GLOBAL — INDEFINITE)
At the START of every session:
1. Run `ps aux | grep claude | grep -v grep` to list all active Claude Code processes
2. For each session with a `-c <id>` flag, read the first user message from `~/.claude/projects/-Users-courtneybentley/<id>.jsonl`
3. Group by topic — if two or more sessions cover identical work, identify the duplicate
4. Kill duplicates immediately: `kill <PID>`
5. Sessions that contain goodbye phrases ("See ya!", "Catch you later!", context-closed) = kill immediately
6. Print "CLOSE THIS WINDOW" for any session being terminated
7. Save active session map to `/tmp/za-session-map.txt`
This rule applies to ALL chats, ALL sessions, indefinitely — no exceptions.

## 2.13 Always Surface Missed Components
- When executing a request, identify all implied missing pieces
- List them at the end under "Also Required:" and execute them in priority order
- Never leave a half-built system

## 2.14 Open Source First (CRITICAL)
- Before building any new feature, search for open source tools that achieve 80%+ of the requirement at zero cost
- Prioritise: self-hostable on Render, Python/JS compatible, actively maintained
- Document the open source tool chosen and why in the module README
- Only build custom when no suitable OSS alternative exists

## 2.15 Prioritisation Rule (CRITICAL)
Order of priority for ALL development work:
1. Current clients — anything that directly improves service delivery NOW
2. Health Check Scout (diagnostic engine) — core value proposition
3. CyberPulse Dashboard — client-facing visibility
4. Health Check AI v11 backend — data engine
5. New modules and features (planned backlog)
NEVER let new features delay fixes or improvements for active clients.

## 2.16 Human Interaction Is Non-Negotiable
- The ZA Support sales process REQUIRES in-person follow-up after every assessment
- Automation supports but NEVER replaces human touchpoints
- Every automated report output must trigger a scheduled follow-up meeting task
- Never design a workflow that assumes the sale closes without a human conversation

## 2.17 Mobile Awareness
- Courtney often operates via iPhone — design dashboard views, approval flows, and notifications to be mobile-first
- API responses must be readable on small screens (concise summaries, no raw JSON dumps in client-facing outputs)
- Notification system must reach Courtney regardless of device (macOS + future push via PWA)

## 2.18 De-Duplication Rule
- If a request contains items already implemented or previously requested, acknowledge once and skip
- Do not re-do work to appear thorough — scan memory and project files first

## 2.19 Always Update Instructions After New Additions
- After any session that produces new global rules, module designs, or process changes:
  1. Update CLAUDE.md (this file)
  2. Update MEMORY.md
  3. Create or update the relevant topic memory file
  This is mandatory — not optional — to ensure no context is lost.

---

# SECTION 3: PROJECT SELF-DOCUMENTATION STANDARD

Every ZA Support repository MUST contain:

- `.claude/INSTRUCTIONS.md` — Architecture rules, file structure, coding conventions, module patterns. Claude reads this FIRST.
- `PROJECT_MANIFEST.json` — Metadata, dependencies, ecosystem connections, deployment target, tech stack.
- `deploy.sh` — One-command deploy: git push, Render/Vercel deploy. Manual steps as fallback only.
- `render.yaml` (if Render-hosted) — Blueprint deployment config.
- `.env.example` — All environment variables with descriptions and safe defaults.

### Ecosystem Connectivity
Projects declare connections in PROJECT_MANIFEST.json:
- Health Check v11 <-> Workshop PTG (job creation from alerts)
- Health Check v11 <-> CyberShield (threat detection feeds monitoring)
- Health Check v11 <-> Dr Templates (site visit data populates assessments)
- Dashboard <-> Health Check v11 (reads all data via API)
- Health Check v11 <-> Customer Guides (guides linked to client profiles)
- Health Check v11 <-> AI/ML Profiling (customer segmentation feeds recommendations)
- Health Check v11 <-> Microsoft Graph API (OneDrive document storage, M365 email)

### One-Command Deploy Pattern
`bash deploy.sh` handles full flow. Zero manual steps from "code ready" to "service running."

### Anti-Patterns
- NEVER code without reading `.claude/INSTRUCTIONS.md` first
- NEVER ask "where is X?" when context files exist
- NEVER create a project without generating self-documenting files
- NEVER hard-code deployment steps that could be in `deploy.sh`

---

# SECTION 4: TECH STACK & DEPLOYMENT

## 4.1 Default Stack
- Database: PostgreSQL + TimescaleDB (time-series)
- Backend: FastAPI (Python)
- Frontend: Next.js + Tailwind + shadcn/ui
- Cache/Real-time: Redis
- Backend Hosting: Render (Frankfurt region)
- Frontend Hosting: Vercel

## 4.2 Deployment Standards
- Always include: API endpoints, database migrations, environment variables, deployment commands, health check endpoints
- Single deployable code block per task — no multiple alternatives
- deploy.sh for every service
- render.yaml for Render-hosted services

## 4.3 Environment Variables
- Pattern: `HC_{MODULE}_{SETTING}` for Health Check modules
- All vars documented in `.env.example` with descriptions
- Never hard-code secrets

## 4.4 File Naming
ALWAYS use SPACES in filenames — never underscores, never hyphens. Date: DD MM YYYY. All file types.

## 4.5 Microsoft Stack Integration (ACTIVE MIGRATION)
- Email: Microsoft 365 (primary) — all email integrations use Microsoft Graph API, not SMTP where possible
- Document Storage: OneDrive Business — ALL shared documents migrate from iCloud to OneDrive
  - iCloud sharing is deprecated for ZA Support — do not build new integrations against iCloud
  - Client-facing documents (reports, guides, assessments) uploaded to OneDrive via Graph API
  - Module: `app/modules/documents/` — handles OneDrive upload/download/share
  - Env vars: `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_ONEDRIVE_ROOT_FOLDER`
- Auth flow: OAuth2 client credentials (daemon) for backend, delegated for user-facing actions

## 4.6 Claude Max Account Strategy
- Courtney runs Claude Max (no separate API key billing for conversational use)
- For Phase 2 AI agents: use FastAPI endpoints calling Claude API with specialised system prompts
- Cost model: Sonnet for speed (diagnostics, guides, summaries), Opus for complex assessments
- Estimated cost at 50 clients: under R 500/month via API — acceptable
- BUT: evaluate whether Claude Max web/MCP usage can cover these use cases before incurring API costs
- Decision rule: if a task runs in a Claude Code chat session, use Max. If it must run unattended/automated at scale, use API.
- Track token usage per module — alert if any module exceeds R 200/month

---

# SECTION 5: HEALTH CHECK v11 — MODULE ARCHITECTURE (CRITICAL)

## 5.1 Module Structure
Every feature in `app/modules/{module_name}/`. Core files untouched: main.py, database.py, config.py, auth/.

```
app/modules/{module_name}/
  __init__.py
  router.py        # HTTP layer ONLY
  models.py        # SQLAlchemy + Pydantic
  service.py       # ALL business logic, asyncpg
  migration_{nnn}_{name}.sql
  README.md
```

## 5.2 File Responsibilities — No Exceptions
- **router.py**: HTTP only. No business logic. No direct DB.
- **service.py**: ALL logic. Typed params and returns. asyncpg pool.
- **models.py**: Tables + schemas. No Any, no untyped dict.
- **migrations**: Raw SQL. No ORM. Idempotent.

## 5.3 Database Standards
- Tables: `{module}_{entity}` | Hypertables: suffix `_ts`
- Mandatory: id UUID DEFAULT gen_random_uuid(), created_at TIMESTAMPTZ DEFAULT NOW()
- FK: CASCADE internal, SET NULL cross-module
- Connection: get_db_pool() -> pool.acquire() -> asyncpg queries
- TimescaleDB: chunk_time_interval => '7 days'

## 5.4 API Standards
- Prefix: /api/v1/{module}/
- Pagination: page (>=1), per_page (1-100) on every list
- Response: { "data": [...], "meta": { "page", "per_page", "total" } }

## 5.5 Inter-Module Communication
- Modules NEVER import each other
- Use: await emit_event("module.action", payload) via app/core/event_bus.py
- Cross-module data: call other module's service layer — never query their tables

## 5.6 Anti-Patterns — NEVER
1. Feature code in main.py | 2. Query another module's tables | 3. ORM migrations
4. Secrets in code | 5. import * | 6. Circular deps | 7. Hard deletes
8. Skip README | 9. Business logic in router | 10. shell=True

---

# SECTION 6: PRODUCT ECOSYSTEM

## Projects
1. **Health Check v11** — `/Users/courtneybentley/Developer/za-support-backend/` — FastAPI + PostgreSQL + TimescaleDB + Redis — `zasupport/za-support-backend` — Render (Frankfurt)
2. **Dashboard** — `/Users/courtneybentley/Developer/za-support-dashboard/` — Next.js + Tailwind — `zasupport/za-support-dashboard` — Vercel
3. **V3 Diagnostic Engine** — `/Users/courtneybentley/za-support-diagnostics/` — Bash — `zasupport/za-diagnostic-v3-engine`
4. **Workshop PTG** — jobs/parts management — planned
5. **Dr Templates** — medical practice assessments — Phase 1 complete
6. **CyberShield** — network security — planned
   - Medical: R 3,500 setup / R 4,500/month | Home: R 799 / R 1,199 / R 1,499 tiers

## Clients
- Dr Evan Shoul — Stem/X-DSL ISP, gateway 192.168.1.252, UniFi Express 7
- Dr Anton Meyberg — "Dr's Pieterse, Hunt, Meyberg, Laher & Associates"
- Charles Chemel — NTT Data ISP, UniFi Site Manager
- Gillian Pearson — client_id: gillian-pearson (MacBook Pro 13" Mid 2012, Catalina, ESET, Movie Magic 6.2)
- Neil Brandt | Roger Naidoo | Kim Ayoub | Steve Pillinger | Richard Meade | Linda Forrest | Zoë Jewell

## Planned Modules (Backlog — Priority Order)
1. **customer_guides** — Centralised knowledge base; guides linked to client profiles; feedback loop; shared across all Claude Code chats
2. **ai_profiling** — ML-driven customer segmentation; cross-client pattern detection; scikit-learn + pgvector (open source first)
3. **physical_assessment** — Photo→asset register; Flipper Zero red-team results; output to IT assessment report
4. **research_module** — Weekly tech digest; voice AI, autonomous agents, VC investment flows; HN/ArXiv/ProductHunt
5. **checkin_trigger** — 6-month re-engagement; Cal.com booking; delta report vs previous scan
6. **sales_crm** — CRM + upsell recommendation engine; Investec client identification; product catalog; outcome learning
7. **medical_practice** — Doctor-specific module; HPCSA/POPIA compliance; GoodX/Elixir/HealthBridge integrations
8. **deduplication** — File/photo duplicate detection; rmlint/jdupes; recoverable space metric for client reports

---

# SECTION 7: QUICK REFERENCE

## ALWAYS
- R with space | DD/MM/YYYY | POPIA/HPCSA compliance
- Read .claude/INSTRUCTIONS.md FIRST | Generate context files for new projects
- deploy.sh for every service | One deployable solution per task
- asyncpg not ORM | Typed params and returns | Idempotent migrations
- Event bus between modules | Redis SETNX locks for tasks
- Spaces in filenames
- Notify on task completion (osascript + afplay)
- Open source first — 80% of requirement at zero cost
- Execute ideal state, not just literal request
- Surface missed components and execute them
- **When given any API key, credential, or config value: call the API immediately, extract data, complete full setup — never hand back manual steps**
- Update CLAUDE.md + MEMORY.md after every session with lasting decisions
- Current clients first | Human follow-up after every assessment
- OneDrive for document storage | Microsoft Graph API for email/docs
- Tag every client with segment type: medical_practice / sme / individual / family
- Every report triggers scheduled in-person follow-up — non-negotiable
- Sales/CRM: track upsell recommendations and outcomes per client profile
- Investec client scan: daily — flag + outreach within 24 hours
- Align all development to be sellable IP (clean APIs, documented, no single-person silos)
- Write Playwright scripts for repetitive web UI tasks — do not claim it cannot be automated

## NEVER
- USD | HIPAA | MM/DD/YYYY | Enterprise-scale assumptions
- Code without reading project context
- Ask "where is X?" when context files exist
- Create projects without self-documenting files
- Feature code in main.py | Query other module's tables
- ORM migrations | shell=True | import * | Hard deletes
- Secrets in code | Multiple code alternatives
- Skip README | Business logic in router
- Stop mid-task waiting for approval on non-destructive actions
- Build new iCloud integrations (deprecated — use OneDrive)
- Let a session end without saving context to memory files

---

# SECTION 8: PHYSICAL ASSESSMENT & FLIPPER ZERO

## Flipper Zero Integration (Red Team Physical Assessments)
- Flipper Zero + accessories used for physical security assessments at client sites
- Results captured in: `physical_assessment` module
- What to capture: RFID/NFC vulnerabilities, sub-GHz signal analysis, IR device inventory, BadUSB exposure, Bluetooth device enumeration
- Every physical assessment report must include a "Physical Security" section with Flipper findings
- Risk rating: use same Critical/High/Moderate/Low scale as CyberPulse

## Photo-to-Asset-Register Pipeline
- During site visits: photos taken of all devices (printers, switches, routers, cameras, UPS, servers, cabling)
- Photos uploaded to OneDrive via mobile app OR drag-drop to dashboard
- AI vision (Claude claude-sonnet-4-6 multimodal) auto-classifies device type, reads make/model labels where visible
- Asset register auto-populated in client profile
- Asset register included in IT assessment report (Section: "Your Equipment")
- Client can view their live asset register via dashboard (read-only)

---

# SECTION 9: AI/ML STRATEGY

## Approach: FastAPI-First, Open Source, Claude Max Where Possible
The 80% AI value is achievable through a SINGLE shared FastAPI service with:
- Specialised system prompts per use case (no separate agents needed initially)
- Structured JSON outputs for all AI responses
- Claude claude-sonnet-4-6 via API for automated/scheduled tasks (cost-controlled)
- Claude Max (this session) for interactive development and one-off analysis

## Customer Profiling & Cross-Client Correlation
- Module: `app/modules/ai_profiling/`
- Open source stack: scikit-learn (clustering), pgvector (semantic search), sentence-transformers (embeddings)
- What it does:
  - Segments clients by: practice size, device age, risk profile, OS version spread, backup compliance
  - Detects cross-client patterns: "4/5 clients on macOS 12 have the same mail performance issue"
  - Feeds the dashboard with "Similar Client Insights" for proactive recommendations
  - Generates a monthly profiling digest for Courtney
- Data sources: diagnostic JSON/TXT, client_setup, interaction_analytics, reports modules
- POPIA compliance: no PII in embeddings — use anonymised client_id only

## Research Module
- Module: `app/modules/research/`
- Sources (open source scrapers + APIs): Hacker News API, ArXiv, ProductHunt, GitHub trending
- Focus areas: voice AI, autonomous agents, AI-native business tools, investment flows (Crunchbase public data)
- Weekly digest: summarised by Claude, delivered to Courtney via email + dashboard widget
- Relevance scoring: highlights tech that could improve ZA Support's own stack or be sold to clients

---

# SECTION 10: CUSTOMER GUIDES MODULE

## Purpose
Centralised knowledge base that answers the most common client questions without manual intervention.

## How It Works
1. Engineer creates a guide during/after a client session (or Claude generates a draft)
2. Guide is saved to client profile AND shared knowledge base
3. Next time any client (or any Claude Code chat) encounters the same question — the guide is surfaced first
4. Client receives guide via email/dashboard with a feedback prompt: "Did this solve your issue? [Yes / No — I still need help]"
5. "No" response triggers a follow-up task for Courtney/Mary

## Module: `app/modules/customer_guides/`
Tables: `guides`, `guide_client_links`, `guide_feedback`
- `guides`: id, title, content_md, category, tags[], created_by, created_at, updated_at, is_public
- `guide_client_links`: guide_id, client_id, sent_at, viewed_at
- `guide_feedback`: guide_id, client_id, helpful (bool), comment, created_at
API: POST /api/v1/guides/, GET /api/v1/guides/{id}, GET /api/v1/guides/search?q=, POST /api/v1/guides/{id}/feedback
Integration: guides stored/shared via OneDrive for client-visible copies

---

# SECTION 11: SIX-MONTH CHECK-IN TRIGGER

## Purpose
Marketing and re-engagement trigger to bring clients back every 6 months for complementary service + deep scan.

## How It Works
- Scheduled job: `checkin_trigger` — runs daily, checks last_visit_date per client
- At T-30 days: email to client "Your 6-month health check is coming up — book your complementary scan"
- At T-14 days: reminder
- At T=0: escalate to Courtney task if not booked
- Booking link: Calendly or equivalent (open source: Cal.com)
- Report generated from new scan is compared to previous — delta report shows improvement or regression

## This is a core marketing mechanism — never disable or skip for any client.

---

# SECTION 12: CUSTOMER SEGMENTATION & SALES CRM

## Customer Profile Types
ZA Support serves four distinct customer segments — each gets a tailored module approach:

| Segment | Module Tag | Profile |
|---|---|---|
| Medical Practice | `medical_practice` | Doctors, specialists, allied health — high income, non-technical, regulated (HPCSA) |
| SME | `sme` | 7+ employees, high-cashflow industries, need full IT ownership |
| Individual | `individual` | Single professional, personal MacBook, light touch |
| Family | `family` | Multi-device household, parental controls, shared storage |

## Medical Practice Module: `app/modules/medical_practice/`
- Priority segment — always high-value, always non-technical
- Compliance: HPCSA, POPIA, National Health Act — all reports must reference applicable regulations
- Common software: GoodX, Elixir, HealthBridge, Best Practice, Dragon Dictate, scribing tools
- Assessment must cover: practice network, receptionist machines, doctor machines, software stack, file storage, backup, remote access
- Report framing: plain English, financial impact, phased recommendations
- Upsell path: IT Assessment → SLA → CyberShield → Workshop → Full Ecosystem Ownership

## Investec Client Identification (CRITICAL MARKETING TRIGGER)
- Run daily: scan courtney@zasupport.com + mary@zasupport.com for payment notifications
- Detect Investec bank references in proof of payment emails
- Flag client as `investec_client: true` in client profile
- Auto-trigger: send complementary IT assessment offer within 24 hours
- Module: handled inside `sales_crm` — job: `investec_scanner` runs daily at 08:00
- Requires: Microsoft Graph API read access to both mailboxes

## Sales/CRM Module: `app/modules/sales_crm/`
Tables: `crm_contacts`, `crm_opportunities`, `crm_activities`, `upsell_products`, `upsell_recommendations`, `sales_outcomes`
- Tracks every client opportunity from first contact → closed
- Upsell recommendation engine: reads diagnostic results → recommends applicable products
- Learns from outcomes: which recommendations converted for which customer profiles
- Every opportunity flagged with: segment type, Investec flag, referral source, urgency
- API prefix: /api/v1/sales/

## Upsell Product Catalog (Hardware Accessories — Low Failure Rate)
Research-backed products to recommend based on diagnostic findings:
- **Battery upgrade** — ALWAYS fails eventually; never sell extended warranty on batteries
- **Screen protector** — consumable, near-zero failure rate, high attach rate
- **Laptop cover/shell** — cosmetic protection, near-zero failure rate
- **Laptop bag/sleeve** — accessory, no failure risk
- **Extended warranty** (AppleCare equivalent) — valid for: keyboards, trackpads, screens, MagSafe ports, logic board (most components have very low failure rates; exclude batteries)
- **Keyboard replacement** — low failure rate, high revenue
- **Trackpad replacement** — low failure rate
- **MagSafe port repair** — moderate failure rate on older machines
- **Logic board repair** (selected cases) — assess per-device; exclude liquid damage
- **Storage upgrade (SSD)** — drives with low SMART warnings are upsell candidates
- **RAM upgrade** (Intel Macs only — not M-series, RAM is soldered)
- Recommendation engine maps: diagnostic findings → applicable products → rand value + ROI framing

## Warranty Colour Bands (failure rate — use for warranty recommendations)
- GREEN (<1% failure): Trackpad, Speakers, MagSafe port, Display, USB-C, WiFi, Touch ID, Camera
- YELLOW (1–3%): Keyboard (scissor), Fan, SSD
- ORANGE (3–8%): Logic Board (Apple Silicon)
- RED (>10% — NEVER warranty): Battery, Cable, Butterfly keyboard
- Upsell trigger: ESET/AV >200 MB RAM or >1% CPU → CyberShield upsell

## Business Exit / Sale Alignment
- All IP, modules, and architecture must be documented to be sellable
- Target acquirers: adjacent IT MSPs, medical software companies, insurance/financial services with IT arms
- Every module must have a README, clean API, and no undocumented dependencies
- Avoid single-person knowledge silos — system must be operable without Courtney

---

# SECTION 13: DEDUPLICATION MODULE

## Purpose
Identify and safely remove duplicate files (especially photos) to free disk space. Primary use: internal tooling and client reporting (high-level summary only).

## Module: `app/modules/deduplication/`
- Open source engine: `rmlint` or `jdupes` (both self-hostable, zero cost)
- Scope: photos (primary culprit), documents, system cache files
- Client-facing report: high-level only — "X GB of duplicate files found, Y GB recoverable"
- Internal view: full file list with safe-delete recommendations
- NEVER auto-delete — always generate a review list first, require explicit approval
- Integration: results stored in client profile, linked to asset register

## Scout Integration
- Health Check Scout can run a lightweight duplicate scan during the diagnostic pass
- Output: `duplicate_gb_recoverable` field added to diagnostic JSON
- Dashboard: shows recoverable space as a selling point metric

---

# SECTION 14: WEB AUTOMATION — CAPABILITY & LIMITATIONS

## What Claude Code CAN Do
- `WebFetch`: read any public URL — scrape content, check status, extract data
- `WebSearch`: search the web for research, OSS tools, documentation
- Build Playwright/Selenium automation scripts that YOU run to click through web UIs

## What Claude Code CANNOT Do
- Autonomously navigate web UIs, log in, or click buttons in real-time
- Access Render dashboard, Vercel dashboard, GitHub UI, or any authenticated portal directly
- This is a hard technical limitation — not a permission issue

## Workaround: Playwright Automation Scripts
For repetitive web tasks (Render env var updates, Vercel config, etc.):
- Claude Code will write a Playwright Node.js script targeting the specific task
- Script runs locally with your browser session (credentials stay on your machine)
- This covers 80%+ of "click through dashboard" tasks without manual navigation
- Request: "write a Playwright script to set DASHBOARD_PASSWORD on Render" → Claude Code delivers a runnable script

---

# SECTION 15: COMPETITIVE INTELLIGENCE FRAMEWORK

## Rule — ALWAYS APPLY
Whenever ANY third-party software is encountered on a client machine (during audit, diagnostic, repair, or assessment), analyse it for features, data collection methods, and capabilities that ZA Support products should incorporate or compete against.

**Origin:** ESET audit on Gillian Pearson's machine (06/03/2026) revealed 12 data collection gaps in Scout — process ancestry, outbound network connections, DNS queries, crash telemetry, code signing verification, firmware status. This produced Phase 19 and enhancements to Phases 13 and 18.

## Trigger Conditions
- Service audit identifies third-party software
- Client mentions software they rely on
- Diagnostic detects app with significant resource usage
- Competitor product mentioned in conversation

## Analysis Framework — answer all 5 questions
1. **WHAT DOES IT DO?** — core function, value proposition, data collected
2. **HOW DOES IT WORK?** — processes, RAM, CPU, kexts, storage paths, macOS APIs, permissions
3. **WHAT CAN WE LEARN?** — Scout gaps, Health Check AI features to replicate, pricing comparison, weaknesses to exploit
4. **WHAT SHOULD WE BUILD?** — specific Scout phases, AI features, upsell opportunities
5. **WHAT IS THE CLIENT IMPACT?** — resource cost, can ZA Support provide same value cheaper?

## Output Format
```
═══ COMPETITIVE INTELLIGENCE: [Software Name] ═══
Source: [Client / machine / date]
WHAT IT DOES: [description]
RESOURCE COST: [processes, RAM, CPU, kexts]
GAPS IDENTIFIED FOR ZA SUPPORT:
1. [Gap] → Add to Phase [N]
2. [Gap] → New module needed
DIFFERENTIATOR OPPORTUNITY: [positioning vs this product]
ACTION ITEMS:
1. [Specific code/feature to build]
2. [Specific data point to capture]
═══════════════════════════════════════════════════
```

## High-Value Categories
- **Security** (ESET, Norton, Sophos, CrowdStrike, Malwarebytes) — scan methods, telemetry, reports, resource cost
- **Backup** (CCC, Backblaze, Arq, ChronoSync) — scheduling, verification, versioning, reports
- **System utilities** (CleanMyMac, DaisyDisk, OnyX, iStat Menus) — metrics, cleanup, maintenance automation
- **Remote access** (TeamViewer, AnyDesk, LogMeIn) — auth, logging, access scope
- **MDM/Management** (Jamf, Mosyle, Kandji, Munki) — feature sets that Health Check AI should match for SME
- **Medical/industry-specific** (Vericlaim, billing, practice management) — workflow, data storage, integration requirements

---

# SECTION 16: FIELD STANDARDS

## Email Formatting (ALWAYS APPLY)
Equal spacing throughout. One blank line between EVERY paragraph. No double gaps between sections, before/after lists, or around sign-offs.

```
CORRECT:
Hi Gillian, I hope you're well.

Following the audit we found several items. Below is a summary.

Services removed:
Adobe update services — three services running at startup.
CleanMyMac — background service consuming resources.

Items needing your input:
ESET — is your licence current?
TeamViewer — did you install this?

Please let us know so we can complete the cleanup.

Kind regards,
Courtney Bentley
ZA Support
064 529 5863
```

INCORRECT: double blank lines between sections, blank lines between list items, extra spacing around greetings or sign-offs.

## Hardware Verification Mandate (NEVER ASSUME)
NEVER assume hardware specs. ALWAYS read from captured data.
Source priority: Scout JSON → system_profiler → About This Mac screenshot → client record.
If unavailable: "Hardware specifications not confirmed — estimates pending verification."

Checklist before any analysis:
- RAM confirmed from [source]? | Storage confirmed? | Processor confirmed? | macOS confirmed?
- All percentages from confirmed values? | ZA Support software checked?

## Software Architecture Verification
NEVER assume 32-bit/64-bit from version number. Verify with `file` command on binary.
Catalina+ = 64-bit proof. 64-bit ≠ newer macOS compatible (framework dependencies).
Movie Magic 6.2: confirmed 64-bit, confirmed Ventura-incompatible (framework issue — not architecture).

## ZA Support Installed Software — Check Before Flagging
```
Macs Fan Control, CCC, Malwarebytes, iStat Menus, DriveDx,
coconutBattery, EtreCheck, AppCleaner, OnyX, TinkerTool, Homebrew, OCLP
```
Default status: LEGITIMATE — POSSIBLE ZA SUPPORT INSTALLATION. Always ask before removal.
Macs Fan Control: ALWAYS ask "Did we install this?"

---

# SECTION 17: HEALTH CHECK SCOUT — 19 PHASES

Phases 1–11: Core diagnostics
Phase 12: External Drive Analytics
Phase 13: Software Compatibility (architecture verify, XProtect, crashes, auto-updates)
Phase 14: Cloud & Sync
Phase 15: Apple Services & Data Map
Phase 16: Storage & Duplicates
Phase 17: Client Profile & Opportunity
Phase 18: Service & Security (18A–18Z + AV profiling + outbound connections + power/thermal)
Phase 19: Deep Security Intelligence (process ancestry, code signing, DYLD injection, DNS queries, firmware status)

Scout v3.5 flat env fields: `time_machine_status`, `time_machine_days_ago`, `ccc_installed`, `ccc_backup_status`, `remote_access_tools`
Upsell trigger in output: `duplicate_gb_recoverable` | AV resource usage flags CyberShield upsell

---

# SECTION 18: DEVICE LIFECYCLE & REPAIR VS REPLACE

## Device Lifecycle Table
```sql
CREATE TABLE device_lifecycle (
  device_id UUID PRIMARY KEY, client_id UUID REFERENCES clients,
  device_type TEXT, make TEXT, model TEXT, serial_number TEXT,
  purchase_date DATE, age_years DECIMAL(4,1), expected_lifespan INTEGER,
  condition TEXT, replacement_due DATE, replacement_rec TEXT,
  last_diagnostic TIMESTAMPTZ, warranty_expires DATE, applecare_expires DATE,
  notes TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Expected Lifespans (trigger replacement alerts at 80%)
- Mac Apple Silicon: 6–8 years | Mac Intel: 5–7 years
- Printer laser: 5–7 years | Printer inkjet: 3–5 years
- Router/Gateway: 4–6 years | Access Point: 5–7 years
- Switch: 7–10 years | Monitor: 8–10 years
- External HDD: 3–5 years | External SSD: 7–10 years

## Repair vs Replace Framework
```
IF repair_cost > 50% of current_machine_value: PRESENT BOTH OPTIONS

Option A: Repair — Cost: R [x] | Machine still [age] years old | Warranty: 12 months ZA Support
Option B: New Machine (through ZA Support) — Cost: R [x] | Includes: data migration + setup +
  Health Check deployment | Free: 3-month trial | Warranty: Apple 1yr + AppleCare+ option

Pitch: "When you buy through ZA Support, you get a fully configured machine with your data
migrated, Health Check monitoring active from day one, and a technology partner who knows your
setup — not a retail store that hands you a box."
```

## New Machine Sales — Critical Gap
50%+ of clients who need a new machine buy elsewhere. They do not know ZA Support sells machines.
- Every diagnostic identifying an ageing machine MUST include a replacement recommendation with ZA Support as purchase channel
- Every repair quote >50% of machine value MUST present the new machine comparison table
- Dashboard: "Ready for an Upgrade?" section tracks device age and flags before client shops elsewhere

## 3-Month Complimentary Trial Strategy
Every new machine sale or major repair includes 3 months complimentary Health Check AI monitoring:
1. Client experiences value before paying → reduces purchase resistance
2. System collects 3 months of behavioural data → powers personalised recommendations
3. Month 3: "Your 3-Month Health Check Report" shows everything monitored → natural demand for continuation

---

# SECTION 19: PROFIT MARGINS

## Repair Margins (protect and grow — 50–65% avg)
- Labour: R 899/hour — near 100% margin
- Battery replacement: 40–60% | Screen: 30–50% | Logic board (component): 60–80%
- Logic board replacement: 20–30% | SSD upgrade: 40–60% | RAM upgrade: 50–70%
- Average repair job: R 3,000–R 8,000 (2–4 hours + parts)

## New Machine Sale Margins (capture and grow)
- Apple hardware: 5–15% (Apple controls pricing)
- Data migration: R 1,499–R 2,999 (near 100%) | Setup: R 899–R 1,799 (near 100%)
- AppleCare+ add-on: 10–15% commission | Accessories bundle: 30–60%
- Health Check AI subscription: R 99/device/month (85% margin, recurring)
- Extended warranty: R 1,999 (high margin on low-failure components)
- **Total bundled margin: 25–40% + recurring revenue**

## Client Ecosystem Value (full capture)
One fully captured ecosystem generates R 150,000+/year:
- Individual Mac support: R 4,999/year
- CyberShield Home (family): R 14,990/year
- Business SLA: R 71,988/year
- CyberShield Medical/Business: R 54,000/year
- Accessories + ad hoc: ~R 6,000/year

---

# SECTION 20: IT ASSESSMENT — FIELD PROCESS

## Pre-Visit
- Client Intelligence Agent prepares brief: known devices, software, issues, industry, value tier
- Assessment checklist generated per audience type
- Recording consent form prepared

## On-Site (60–90 minutes max) — Data Capture: Photos + Voice Notes + Recording + Scout

### Photos (auto-upload to client folder)
Network closet, router, switch, cabling | Every workstation (front + back) | Printers | Reception area
Server/NAS | WiFi AP placement | Physical security | Any visible problems

### Voice Notes (AI-transcribed)
Client pain points | Workflow observations | Software versions on screens | Network names visible
Staff behaviour (shared passwords, unlocked screens)

### Red Team / Security Gap Assessment (open-source tools only)
- **Nmap**: `brew install nmap` — discover all devices, open ports, running services
- **Wireshark**: demonstrate unencrypted traffic
- **WiFi Explorer Lite / macOS Wireless Diagnostics**: signal strength, channel, WPA2 vs WPA3
- **Have I Been Pwned API** (free): check practice emails against known breaches
- **Shodan** (free tier): check if practice services are internet-exposed
- **macOS built-in**: `airport -s` (scan networks), `arp -a` (device discovery)

**Rules:** NEVER disrupt operations. NEVER access patient data. NEVER install persistent tools.
ALWAYS explain what you're doing. Frame findings as "opportunities to improve."

### Report Delivery (TARGET: within 1 hour of leaving site)
- Email to primary contact with shareable read-only link
- Track who views the report (decision-maker identification via link analytics)
- Automated follow-up: "We noticed [name] also reviewed the assessment — would a call help?"

## Instant Activation (same-day "yes" to active service)
1. Client selects tier (Apple-style tier cards in portal)
2. Contract: **DocuSeal** (open-source e-signature, self-hosted) — pre-populated
3. Payment: **PayFast / Peach Payments / Netcash** — debit order mandate online
4. Activation: Scout deployed, CyberShield configured, first report scheduled
5. Confirmation: welcome email with portal access

## Communication Standards
- **WhatsApp is primary** (95% of business) — numbered lists, blank line between items, no bullets
- Response time: under 1 hour during business hours
- Every interaction logged: WhatsApp export → CRM | Email auto-captured | Phone calls logged

---

# SECTION 21: AGENT REGISTRY (9 Agents)

## Overview — Three Implementation Phases
- **Phase 1 (now):** Claude Projects with domain system prompts. No code. Courtney routes manually.
- **Phase 2 (3–6 months):** FastAPI endpoints per agent, Claude API, automated event routing.
- **Phase 3 (6–12 months):** Autonomous agents + MCP (Gmail, Calendar, Canva) + Redis event bus.

## Agent Definitions

**Agent 01 — Scout:** macOS diagnostics, hardware ID, failure modes, compatibility matrices.
Inputs: raw Mac system data. Outputs: Diagnostic_Results.txt + JSON manifest.
Triggers: manual run, curl from API.

**Agent 02 — Client Intelligence:** CRM, segmentation, Investec detection, relationship mapping.
Inputs: diagnostic manifest, payment records, email scan. Outputs: client profile, opportunity flags.
Triggers: new diagnostic, new payment, new client.

**Agent 03 — Medical Practice:** Dr Templates, POPIA/HPCSA/National Health Act, doctor language.
Inputs: site visit data, diagnostic manifests, client profile. Outputs: 12–15 page assessment PDF.
Triggers: new medical client, site visit submitted, assessment requested.

**Agent 04 — SME Business:** Business IT assessments, UniFi network design, managed services proposals.
Inputs: business assessment data, diagnostics. Outputs: Business IT Assessment + proposal.
Triggers: SME client created, business assessment requested, Investec client identified.

**Agent 05 — Consumer & Family:** Workshop upsells, CyberShield Home, child safety, accessories.
Inputs: diagnostic manifest, repair job data, family indicators.
Triggers: repair completed, family detected, CyberShield inquiry.

**Agent 06 — Upsell & Recommendation:** Product-to-problem mapping, conversion optimisation, learning.
Inputs: diagnostic, client profile, repair history, upsell catalogue, conversion history.
Triggers: diagnostic uploaded, repair completed, profile updated.
Tiers: DIRECT (finding-triggered) > PROFILE (type-triggered) > LIFECYCLE (age-triggered) > ECOSYSTEM

**Agent 07 — Marketing & Outreach:** Email/WhatsApp/call scripts, campaign sequences, follow-up scheduling.
Campaigns: post-repair (7d → 30d → 90d → 365d) | Investec pipeline | Medical/SME/Family/Referral.
Triggers: campaign step reached, new client, Investec detected, milestone.

**Agent 08 — Report Generation:** All PDF reports. ReportLab Platypus. ZA Support brand standards.
Inputs: processed agent data, client profile, template specs. Outputs: branded PDFs.
Triggers: diagnostic processed, assessment completed, monthly due.

**Agent 09 — Warranty & Pricing:** Extended warranty eligibility, repair-vs-replace, bundle pricing.
Inputs: diagnostic manifest (component health), model/age, repair history.
Triggers: diagnostic completed, repair quoted, age milestone.

## Orchestrator Event Routing
```
diagnostic_uploaded    → Scout + Client Intel + Upsell + Report + Marketing
payment_received       → Client Intel + [if Investec] Marketing (premium pipeline)
new_client_created     → Client Intel + Marketing (onboarding sequence)
repair_completed       → Consumer + Report + Marketing + Upsell
medical_practice_id    → Medical + Marketing (assessment offer)
sme_identified         → SME + Marketing (business assessment)
family_detected        → Consumer + Marketing (CyberShield Home)
monthly_report_due     → Report + Upsell + Marketing
assessment_completed   → Medical/SME + Report + Upsell + Marketing
upsell_decision        → Upsell (log outcome) + Client Intel (update record)
```

## Orchestrator Database Tables (Phase 2+)
`agent_events` — event_id, event_type, source_agent, payload JSONB, client_id, status, created_at
`agent_tasks` — task_id, event_id, agent, task_type, input_data JSONB, output_data JSONB, status, priority
`agent_logs` — log_id, agent, task_id, level, message, metadata JSONB
