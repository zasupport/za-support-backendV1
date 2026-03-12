# CHAT 2: Diagnostics, Scout & Monitoring
# Consolidated Session Context — 12/03/2026
# Load this at session start to restore full context

---

## SCOPE
This chat owns ALL data collection, monitoring, and diagnostic intelligence:
- Health Check Scout (19 phases) integration
- ISP Outage Monitor (ALREADY BUILT — maintain and extend)
- Agent Router (ALREADY BUILT — heartbeat, telemetry, device status)
- Automation layer (event bus, scheduler, monitors, notifications)
- `deduplication` module (new build)
- Deep Security Intelligence (Phase 19)
- Competitive intelligence framework
- CyberShield integration points

## AGENTS OWNED
- Agent 01: Scout (macOS diagnostics, hardware ID, failure modes, compatibility matrices)

---

## WHAT'S ALREADY BUILT

### ISP Outage Monitor (app/api/isp.py + app/services/isp_monitor.py)
- 4-layer detection: Status page scraper, Downdetector ZA, HTTP probe, agent connectivity
- 13 SA ISPs pre-seeded (Telkom, Vodacom, MTN, Rain, Afrihost, RSAWEB, Vox, Herotel, Cool Ideas, Stem, Cybersmart, Web Africa, NTT Data)
- 15 API endpoints under /api/v1/isp/
- Redis SETNX locks for alert cooldown (30 min)
- Confirmation threshold: 3 sources for outage declaration
- Degraded threshold: 10% agent failure rate

### Agent Router (app/api/agent.py)
- Bearer token auth (AGENT_AUTH_TOKEN)
- 60-second heartbeat from Mac agents: CPU, memory, disk, battery, security posture
- Diagnostic JSON upload endpoint
- Device list and status endpoints
- 6 endpoints under /api/v1/agent/

### Automation Layer (app/services/)
- event_bus.py — Central publish/subscribe
- automation_scheduler.py — APScheduler with 7 jobs:
  1. Patch monitor (6h) — macOS update tracking
  2. Backup monitor (6h) — Time Machine + 3rd-party
  3. Report generator (daily 06:00)
  4. Stale device detector (1h) — flags devices not seen in 24h
  5. Security posture scanner (12h)
  6. Event cleanup (monthly 1st @ 03:00) — 90d detailed, 2y aggregated
  7. Heartbeat rollup (daily 02:00)
- notification_engine.py — Mailgun email + Slack webhook
- alert_engine.py — Severity evaluation

### Diagnostics (app/api/diagnostics.py)
- za_diag_v3.sh JSON ingestion (215 data points)
- WorkshopDiagnostic model: security (SIP, FileVault, XProtect), battery health, storage, OCLP, kernel panics, recommendations
- Search, list, get endpoints under /api/v1/diagnostics/

### Device Management (app/api/devices.py)
- Device registration, health submission, history
- HealthData model: CPU, memory, disk, battery, threat_score, network speeds

---

## MODULE TO BUILD

### deduplication (`app/modules/deduplication/`)
```
Engine: rmlint or jdupes (open source, zero cost)
Scope: photos (primary), documents, system cache files

Tables:
- dedup_scans: id, client_id FK, device_id FK, scan_date, total_files INT,
  duplicate_files INT, duplicate_gb DECIMAL, recoverable_gb DECIMAL, status
- dedup_file_groups: id, scan_id FK, file_hash TEXT, file_size BIGINT,
  file_count INT, paths JSONB, recommended_action TEXT (keep/review/delete)

API: /api/v1/dedup/
Endpoints:
  POST /scan — trigger dedup scan for a device
  GET /scan/{id} — get scan results
  GET /scan/{id}/groups — list duplicate file groups
  POST /scan/{id}/approve — approve safe-delete list (NEVER auto-delete)
  GET /summary/{client_id} — high-level: "X GB duplicates found, Y GB recoverable"

Scout Integration:
  - Scout v3.5 runs lightweight duplicate scan during diagnostic pass
  - Output: duplicate_gb_recoverable field in diagnostic JSON
  - Dashboard: shows recoverable space as selling metric
```

---

## SCOUT 19 PHASES (reference for API integration)

| Phase | Description | Status |
|-------|-------------|--------|
| 1-11 | Core diagnostics | Active in Scout v3 |
| 12 | External Drive Analytics | Active |
| 13 | Software Compatibility (architecture, XProtect, crashes, auto-updates) | Active |
| 14 | Cloud & Sync | Active |
| 15 | Apple Services & Data Map | Active |
| 16 | Storage & Duplicates | Active |
| 17 | Client Profile & Opportunity | Active |
| 18 | Service & Security (18A-18Z + AV profiling + outbound connections + power/thermal) | Active |
| 19 | Deep Security Intelligence (process ancestry, code signing, DYLD injection, DNS, firmware) | New |

### Phase 19 Detail (triggered by ESET competitive analysis on Gillian Pearson's machine)
- Process ancestry chains
- Code signing verification
- DYLD injection detection
- DNS query monitoring
- Firmware status checks
- Outbound network connection logging

## COMPETITIVE INTELLIGENCE FRAMEWORK
When encountering third-party software on client machines, answer:
1. WHAT DOES IT DO?
2. HOW DOES IT WORK? (processes, RAM, CPU, kexts, APIs)
3. WHAT CAN WE LEARN? (Scout gaps, features to replicate)
4. WHAT SHOULD WE BUILD?
5. WHAT IS THE CLIENT IMPACT?

High-value categories: Security (ESET, Norton, CrowdStrike), Backup (CCC, Backblaze), System utilities (CleanMyMac, DaisyDisk), Remote access (TeamViewer), MDM (Jamf, Mosyle)

## CROSS-CHAT DEPENDENCIES
- Sends diagnostic data to Chat 1 (CRM) for upsell triggering
- Sends diagnostic data to Chat 3 (Reports) for assessment content
- Sends telemetry to Chat 4 (AI) for cross-client pattern detection
- Dashboard metrics consumed by Chat 5 (Dashboard)
- Event bus connects to all other chats via app/services/event_bus.py
