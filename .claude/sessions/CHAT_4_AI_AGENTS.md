# CHAT 4: AI/ML, Agents & Automation
# Consolidated Session Context — 12/03/2026
# Load this at session start to restore full context

---

## SCOPE
This chat owns ALL AI-powered features and agent orchestration:
- `ai_profiling` module (ML customer segmentation)
- `research_module` (tech digest)
- 9-Agent Registry architecture (Phase 1 → 2 → 3)
- Agent orchestrator and event routing
- FastAPI-first AI service
- Claude API integration strategy
- Microsoft Graph API integration
- Cross-client pattern detection

## AGENTS OWNED
- Agent 05: Consumer & Family (workshop upsells, CyberShield Home, child safety)
- Agent 07: Marketing & Outreach (email/WhatsApp/call scripts, campaigns)
- Orchestrator: Event routing to all 9 agents

---

## MODULES TO BUILD

### ai_profiling (`app/modules/ai_profiling/`)
```
Open Source Stack:
  - scikit-learn (clustering)
  - pgvector (semantic search in PostgreSQL)
  - sentence-transformers (embeddings)

Tables:
- ai_profiles: id, client_id FK, segment TEXT, cluster_id INT,
  risk_score DECIMAL, device_age_avg DECIMAL, os_version_spread JSONB,
  backup_compliance BOOL, common_issues JSONB, embedding VECTOR(384),
  last_profiled TIMESTAMPTZ, created_at, updated_at
- cross_client_patterns: id, pattern_type TEXT, description TEXT,
  affected_clients UUID[], confidence DECIMAL, recommendation TEXT,
  detected_at TIMESTAMPTZ
- profiling_digests: id, digest_date DATE, content_md TEXT,
  patterns_found INT, recommendations JSONB, sent_to TEXT[]

API: /api/v1/ai/
Endpoints:
  POST /profile/{client_id} — trigger profiling for client
  GET /profile/{client_id} — get client AI profile
  GET /patterns — list cross-client patterns
  GET /similar/{client_id} — find similar clients
  POST /digest — generate monthly profiling digest
  GET /digest/latest — get latest digest

What It Does:
  - Segments clients by: practice size, device age, risk profile, OS spread, backup compliance
  - Detects cross-client patterns: "4/5 clients on macOS 12 have same mail issue"
  - Feeds dashboard with "Similar Client Insights"
  - Monthly digest for Courtney

POPIA Compliance: No PII in embeddings — use anonymised client_id only
Data Sources: diagnostic JSON/TXT, client_setup, interaction_analytics, reports
```

### research_module (`app/modules/research/`)
```
Sources (open source scrapers + APIs):
  - Hacker News API (free)
  - ArXiv (free)
  - ProductHunt (free)
  - GitHub trending (free)
  - Crunchbase public data (free tier)

Tables:
- research_items: id, source TEXT, title TEXT, url TEXT, summary TEXT,
  relevance_score DECIMAL, focus_area TEXT, published_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ
- research_digests: id, digest_date DATE, items JSONB, highlights JSONB,
  za_support_relevance JSONB, created_at
- focus_areas: id, name TEXT, keywords TEXT[], active BOOL

API: /api/v1/research/
Endpoints:
  GET /latest — latest research items (paginated)
  GET /digest/weekly — weekly digest
  POST /digest/generate — trigger digest generation
  GET /focus-areas — list focus areas
  POST /focus-areas — add focus area

Focus Areas:
  - Voice AI
  - Autonomous agents
  - AI-native business tools
  - Investment flows

Weekly Digest: summarised by Claude, delivered via email + dashboard widget
Relevance Scoring: highlights tech that could improve ZA Support or be sold to clients
```

---

## 9-AGENT REGISTRY ARCHITECTURE

### Phase 1 (NOW): Claude Projects
- Domain-specific system prompts
- No code
- Courtney routes manually

### Phase 2 (3-6 months): FastAPI Endpoints
- Each agent = FastAPI endpoint with specialised system prompt
- Claude API (Sonnet for speed, Opus for complex)
- Automated event routing via orchestrator
- Structured JSON outputs

### Phase 3 (6-12 months): Autonomous Agents
- Full autonomy + MCP (Gmail, Calendar, Canva)
- Redis event bus
- Self-triggering based on events

### Agent Definitions
| # | Name | Inputs | Outputs | Triggers |
|---|------|--------|---------|----------|
| 01 | Scout | Raw Mac data | Diagnostic_Results.txt + JSON | Manual, curl |
| 02 | Client Intelligence | Diagnostics, payments, email | Client profile, opportunity flags | New diagnostic/payment/client |
| 03 | Medical Practice | Site visit, diagnostics, profile | 12-15 page assessment PDF | New medical client, site visit |
| 04 | SME Business | Business assessment, diagnostics | Business IT Assessment + proposal | SME created, assessment requested |
| 05 | Consumer & Family | Diagnostics, repair data, family indicators | Workshop upsells, CyberShield | Repair done, family detected |
| 06 | Upsell & Recommendation | Diagnostic, profile, repair history, catalog | Product recommendations | Diagnostic uploaded, repair done |
| 07 | Marketing & Outreach | Campaign data, client profile | Email/WhatsApp/call scripts | Campaign step, new client, milestone |
| 08 | Report Generation | Processed agent data, profile, template | Branded PDFs | Diagnostic processed, assessment done |
| 09 | Warranty & Pricing | Diagnostic manifest, model/age, repair history | Warranty eligibility, pricing | Diagnostic done, repair quoted |

### Orchestrator Event Routing
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

### Orchestrator Database Tables
```sql
agent_events: event_id, event_type, source_agent, payload JSONB, client_id, status, created_at
agent_tasks: task_id, event_id, agent, task_type, input_data JSONB, output_data JSONB, status, priority
agent_logs: log_id, agent, task_id, level, message, metadata JSONB
```

---

## AI STRATEGY

### FastAPI-First Approach
- Single shared FastAPI service with specialised system prompts per use case
- Structured JSON outputs for all AI responses
- No separate agent processes needed initially

### Claude Model Selection
- **Sonnet:** Speed tasks — diagnostics, guides, summaries
- **Opus:** Complex tasks — assessments, profiling, analysis
- **Max (this session):** Interactive development, one-off analysis

### Cost Control
- Estimated: under R 500/month at 50 clients via API
- Track token usage per module — alert if any exceeds R 200/month
- Decision rule: if runs in Claude Code chat = use Max; if unattended/automated = use API

### Microsoft Graph API Integration
- Email: M365 primary (not SMTP)
- Documents: OneDrive Business (iCloud deprecated)
- Auth: OAuth2 client credentials (daemon) for backend, delegated for user-facing
- Env vars: MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET, MS_ONEDRIVE_ROOT_FOLDER

## CROSS-CHAT DEPENDENCIES
- Receives diagnostic data from Chat 2 (Scout) for profiling
- Receives client data from Chat 1 (CRM) for segmentation
- Provides AI classification to Chat 3 (Reports) for photo pipeline
- Orchestrator routes events to all other chats
