# CHAT 3: Reports, Assessments & Knowledge Base
# Consolidated Session Context — 12/03/2026
# Load this at session start to restore full context

---

## SCOPE
This chat owns ALL output generation:
- `customer_guides` module (knowledge base)
- `medical_practice` module (HPCSA/POPIA compliance)
- `physical_assessment` module (Flipper Zero + photo pipeline)
- IT Assessment field process
- Report generation service (ReportLab Platypus, branded PDFs)
- Dr Templates integration

## AGENTS OWNED
- Agent 03: Medical Practice (POPIA/HPCSA/National Health Act, doctor-language reports)
- Agent 04: SME Business (business IT assessments, UniFi network design, proposals)
- Agent 08: Report Generation (all PDFs, ReportLab Platypus, ZA Support branding)

---

## MODULES TO BUILD

### customer_guides (`app/modules/customer_guides/`)
```
Tables:
- guides: id, title, content_md TEXT, category TEXT, tags TEXT[],
  created_by TEXT, is_public BOOL, created_at, updated_at
- guide_client_links: id, guide_id FK, client_id FK, sent_at, viewed_at
- guide_feedback: id, guide_id FK, client_id FK, helpful BOOL, comment TEXT, created_at

API: /api/v1/guides/
Endpoints:
  POST / — create guide
  GET /{id} — get guide
  GET /search?q= — search guides by keyword/tag
  GET /client/{client_id} — guides sent to specific client
  POST /{id}/send/{client_id} — send guide to client (email + dashboard link)
  POST /{id}/feedback — submit feedback (helpful: yes/no + comment)
  GET /analytics — guide effectiveness metrics

Workflow:
  1. Engineer creates guide during/after client session (or Claude generates draft)
  2. Guide saved to client profile AND shared knowledge base
  3. Next time same question arises — guide surfaced first
  4. Client receives via email/dashboard with feedback prompt
  5. "No — I still need help" → follow-up task for Courtney/Mary

Integration: guides stored/shared via OneDrive for client-visible copies
```

### medical_practice (`app/modules/medical_practice/`)
```
Tables:
- medical_practices: id, practice_name, practice_type (GP/specialist/allied),
  hpcsa_number TEXT, practitioners JSONB, software_stack JSONB,
  compliance_status JSONB, created_at, updated_at
- medical_assessments: id, practice_id FK, assessor TEXT, visit_date DATE,
  network_findings JSONB, workstation_findings JSONB, software_findings JSONB,
  storage_findings JSONB, backup_findings JSONB, remote_access_findings JSONB,
  compliance_findings JSONB, recommendations JSONB, risk_rating TEXT,
  report_url TEXT, created_at

API: /api/v1/medical/
Endpoints:
  POST /practices — register practice
  GET /practices/{id} — get practice with assessments
  POST /assessments — submit assessment
  GET /assessments/{id}/report — generate PDF report
  GET /compliance/{practice_id} — compliance status dashboard

Compliance Requirements:
  - HPCSA (Health Professions Council of South Africa)
  - POPIA (Protection of Personal Information Act)
  - National Health Act
  All reports must reference applicable regulations

Common Software: GoodX, Elixir, HealthBridge, Best Practice, Dragon Dictate, scribing tools

Assessment Must Cover:
  - Practice network, reception machines, doctor machines
  - Software stack, file storage, backup, remote access
  - Report framing: plain English, financial impact, phased recommendations
```

### physical_assessment (`app/modules/physical_assessment/`)
```
Tables:
- site_visits: id, client_id FK, visit_date DATE, assessor TEXT,
  location TEXT, duration_mins INT, photos JSONB, voice_notes JSONB,
  recording_consent BOOL, created_at
- asset_register: id, client_id FK, device_type TEXT, make TEXT,
  model TEXT, serial_number TEXT, location TEXT, condition TEXT,
  photo_url TEXT, ai_classified BOOL, ai_confidence DECIMAL, created_at, updated_at
- security_findings: id, visit_id FK, tool_used TEXT (nmap/wireshark/wifi_explorer/hibp/shodan),
  finding_type TEXT, severity TEXT (critical/high/moderate/low),
  description TEXT, recommendation TEXT, created_at

API: /api/v1/assessments/
Endpoints:
  POST /visits — create site visit
  POST /visits/{id}/photos — upload photos (triggers AI classification)
  GET /assets/{client_id} — client asset register
  POST /security-findings — log Flipper Zero / red-team findings
  GET /visits/{id}/report — generate assessment report

Photo-to-Asset Pipeline:
  1. Photos taken on-site of all devices
  2. Upload to OneDrive via mobile app OR drag-drop to dashboard
  3. Claude Sonnet multimodal auto-classifies device type, reads make/model
  4. Asset register auto-populated in client profile
  5. Client can view live asset register via dashboard (read-only)

Flipper Zero Integration:
  - RFID/NFC vulnerabilities
  - Sub-GHz signal analysis
  - IR device inventory
  - BadUSB exposure
  - Bluetooth device enumeration
  Results in "Physical Security" section of every assessment report

Red Team Tools (open source only):
  - Nmap: device discovery, open ports, services
  - Wireshark: demonstrate unencrypted traffic
  - WiFi Explorer: signal strength, WPA2 vs WPA3
  - Have I Been Pwned API: check practice emails
  - Shodan (free tier): internet-exposed services
  - macOS built-in: airport -s, arp -a
  RULES: NEVER disrupt operations, NEVER access patient data, ALWAYS explain
```

---

## REPORT GENERATION (Agent 08)

### ReportLab Platypus Standards
- ZA Support brand standards
- PDF output for all reports
- Input: processed agent data + client profile + template specs

### Report Types
1. Device Diagnostic Report (from Scout data)
2. IT Assessment Report (from site visit data) — 12-15 pages for medical practices
3. Monthly Health Check Report
4. 6-Month Delta Report (improvement/regression from check-in trigger)
5. CyberShield Security Report
6. Client Equipment Report (asset register)

### Report Delivery
- Email to primary contact with shareable read-only link
- Track who views (decision-maker identification via link analytics)
- Auto follow-up: "We noticed [name] also reviewed — would a call help?"
- TARGET: within 1 hour of leaving site

---

## IT ASSESSMENT FIELD PROCESS

### Pre-Visit
- Client Intelligence Agent prepares brief
- Assessment checklist generated per audience type
- Recording consent form prepared

### On-Site (60-90 mins)
- Photos: network closet, router, switch, cabling, workstations, printers, reception, server/NAS, WiFi APs, physical security
- Voice notes: AI-transcribed
- Red team assessment with open-source tools

### Post-Visit
- Report generated within 1 hour
- Instant activation flow: tier selection → DocuSeal e-signature → PayFast/Peach/Netcash payment → Scout + CyberShield deployment → welcome email

## CROSS-CHAT DEPENDENCIES
- Receives diagnostic data from Chat 2 (Scout) for report content
- Receives client profiles from Chat 1 (CRM) for personalization
- AI classification powered by Chat 4 (AI/ML) for photo pipeline
- Reports displayed in Chat 5 (Dashboard)
