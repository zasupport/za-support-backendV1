# CHAT 1: CRM, Sales & Client Management
# Consolidated Session Context — 12/03/2026
# Load this at session start to restore full context

---

## SCOPE
This chat owns ALL client-facing business logic:
- `sales_crm` module (full build)
- `checkin_trigger` module (6-month re-engagement)
- Device lifecycle tracking
- Upsell recommendation engine
- Investec client scanner
- Customer segmentation (medical_practice / sme / individual / family)

## AGENTS OWNED
- Agent 02: Client Intelligence (CRM, segmentation, Investec detection)
- Agent 06: Upsell & Recommendation (product-to-problem mapping, conversion learning)
- Agent 09: Warranty & Pricing (eligibility, repair-vs-replace, bundles)

---

## MODULES TO BUILD

### sales_crm (`app/modules/sales_crm/`)
```
Tables:
- crm_contacts: id, name, email, phone, company, segment (medical_practice/sme/individual/family),
  investec_client BOOL, referral_source, created_at, updated_at
- crm_opportunities: id, contact_id FK, title, stage, value_rand, probability,
  expected_close, created_at, updated_at
- crm_activities: id, contact_id FK, opportunity_id FK, activity_type,
  summary, scheduled_at, completed_at
- upsell_products: id, name, category, margin_pct, failure_band (green/yellow/orange/red),
  price_rand, description
- upsell_recommendations: id, contact_id FK, product_id FK, diagnostic_id FK,
  trigger_type (direct/profile/lifecycle/ecosystem), confidence, status, created_at
- sales_outcomes: id, recommendation_id FK, converted BOOL, revenue_rand, notes, created_at

API: /api/v1/sales/
Endpoints:
  POST /contacts — create contact
  GET /contacts — list (paginated, filterable by segment)
  GET /contacts/{id} — get with opportunities + activities
  POST /opportunities — create opportunity
  PATCH /opportunities/{id} — update stage
  POST /activities — log activity
  GET /recommendations/{contact_id} — get upsell recommendations
  POST /recommendations/{id}/outcome — log conversion result
  GET /dashboard — sales overview metrics
```

### Investec Scanner (inside sales_crm)
```
Job: investec_scanner — runs daily 08:00
Method: Microsoft Graph API read access to courtney@zasupport.com + mary@zasupport.com
Detect: Investec bank references in proof of payment emails
Action: Flag client as investec_client: true, auto-trigger assessment offer within 24h
Requires: MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET env vars
```

### checkin_trigger (`app/modules/checkin_trigger/`)
```
Tables:
- checkin_schedule: id, client_id FK, last_visit_date, next_checkin_date,
  reminder_30d_sent BOOL, reminder_14d_sent BOOL, escalated BOOL, booking_url
- checkin_reports: id, client_id FK, current_scan_id FK, previous_scan_id FK,
  delta_json JSONB, improvement_areas[], regression_areas[]

Job: checkin_scheduler — runs daily
Logic:
  T-30 days: email "Your 6-month health check is coming up"
  T-14 days: reminder
  T=0: escalate to Courtney task if not booked

API: /api/v1/checkin/
Endpoints:
  GET /schedule — list upcoming check-ins
  POST /schedule — create/update check-in for client
  GET /delta/{client_id} — get delta report (current vs previous)
```

---

## UPSELL PRODUCT CATALOG (seed data)

| Product | Category | Margin | Failure Band |
|---------|----------|--------|-------------|
| Battery replacement | Repair | 40-60% | RED (>10%) — NEVER warranty |
| Screen protector | Accessory | 60%+ | N/A |
| Laptop cover/shell | Accessory | 60%+ | N/A |
| Laptop bag/sleeve | Accessory | 60%+ | N/A |
| AppleCare+ | Warranty | 10-15% | GREEN components only |
| Keyboard replacement | Repair | 50-70% | GREEN (<1%) |
| Trackpad replacement | Repair | 50-70% | GREEN (<1%) |
| MagSafe port repair | Repair | 40-60% | GREEN (<1%) |
| Logic board repair | Repair | 60-80% | ORANGE (3-8%) |
| SSD upgrade | Upgrade | 40-60% | YELLOW (1-3%) |
| RAM upgrade (Intel only) | Upgrade | 50-70% | N/A (M-series soldered) |

## WARRANTY COLOUR BANDS
- GREEN (<1%): Trackpad, Speakers, MagSafe, Display, USB-C, WiFi, Touch ID, Camera
- YELLOW (1-3%): Keyboard (scissor), Fan, SSD
- ORANGE (3-8%): Logic Board (Apple Silicon)
- RED (>10% — NEVER warranty): Battery, Cable, Butterfly keyboard

## REPAIR VS REPLACE FRAMEWORK
```
IF repair_cost > 50% of current_machine_value:
  Present BOTH options:
  Option A: Repair — Cost, machine age, 12-month ZA Support warranty
  Option B: New Machine (through ZA Support) — Cost, includes migration + setup + 3-month trial
```

## CUSTOMER SEGMENTS
| Segment | Tag | Profile |
|---------|-----|---------|
| Medical Practice | medical_practice | Doctors, high income, non-technical, HPCSA regulated |
| SME | sme | 7+ employees, high-cashflow, need full IT ownership |
| Individual | individual | Single professional, personal MacBook, light touch |
| Family | family | Multi-device household, parental controls, shared storage |

## EXISTING CLIENTS (seed into CRM)
- Dr Evan Shoul — medical_practice, Stem ISP, gateway 192.168.1.252
- Dr Anton Meyberg — medical_practice, "Dr's Pieterse, Hunt, Meyberg, Laher & Associates"
- Charles Chemel — sme, NTT Data ISP, UniFi Site Manager
- Gillian Pearson — individual, MacBook Pro 13" Mid 2012, ESET, Movie Magic 6.2
- Neil Brandt, Roger Naidoo, Kim Ayoub, Steve Pillinger, Richard Meade, Linda Forrest, Zoë Jewell

## CROSS-CHAT DEPENDENCIES
- Receives diagnostic data from Chat 2 (Scout/diagnostics) to trigger upsell recommendations
- Sends client profiles to Chat 3 (Reports) for assessment generation
- Sends client data to Chat 4 (AI) for profiling and segmentation ML
- Dashboard metrics consumed by Chat 5 (Dashboard)
