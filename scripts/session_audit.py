#!/usr/bin/env python3
"""
ZA Support — Session & Project Consolidation Audit Tool

Analyses the current repository to identify:
  - Which modules belong to which target product
  - Database tables and their product affiliation
  - Route groupings and dependencies
  - Recommended actions (keep / archive / rename)

Target state after consolidation:
  SESSION 1 — "ZA Support V3 Diagnostics"
      Lightweight diagnostic agent that runs on client machines.
      Modules: diagnostics, health monitoring, network monitoring
      DB tables: health_data, network_data

  SESSION 2 — "ZA Support V1 Full Health Check"
      Full support-desk backend (tickets, chat, users, dashboard).
      Modules: auth, tickets, chat, dashboard
      DB tables: users, tickets, chat_sessions, chat_messages

Both share the same 'zasupport' PostgreSQL database on Render.
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Literal
from pathlib import Path

# ─── Module definitions ──────────────────────────────────────────────

@dataclass
class Module:
    name: str
    route_file: str
    api_prefix: str
    db_tables: list[str]
    description: str
    target_session: Literal["V3_DIAGNOSTICS", "V1_HEALTH_CHECK", "SHARED"]
    action: Literal["KEEP", "ARCHIVE", "RENAME", "SPLIT"]
    notes: str = ""


MODULES = [
    Module(
        name="Auth",
        route_file="app/routes/auth.py",
        api_prefix="/api/v1/auth",
        db_tables=["users"],
        description="User registration, login, JWT tokens, role-based access",
        target_session="SHARED",
        action="KEEP",
        notes="Required by both sessions — shared authentication layer",
    ),
    Module(
        name="Tickets",
        route_file="app/routes/tickets.py",
        api_prefix="/api/v1/tickets",
        db_tables=["tickets"],
        description="Support ticket CRUD, status tracking, agent assignment",
        target_session="V1_HEALTH_CHECK",
        action="KEEP",
        notes="Core of the V1 full health-check support desk",
    ),
    Module(
        name="Chat",
        route_file="app/routes/chat.py",
        api_prefix="/api/v1/chat",
        db_tables=["chat_sessions", "chat_messages"],
        description="Real-time chat sessions, WebSocket, messaging",
        target_session="V1_HEALTH_CHECK",
        action="KEEP",
        notes="Support desk live-chat — belongs to V1",
    ),
    Module(
        name="Health Monitoring",
        route_file="app/routes/health.py",
        api_prefix="/api/v1/health",
        db_tables=["health_data"],
        description="Machine health metrics (CPU, memory, disk, battery, threat score)",
        target_session="V3_DIAGNOSTICS",
        action="KEEP",
        notes="Client-side diagnostic telemetry — core of V3",
    ),
    Module(
        name="Network Monitoring",
        route_file="app/routes/network.py",
        api_prefix="/api/v1/network",
        db_tables=["network_data"],
        description="UniFi / network controller metrics (clients, devices)",
        target_session="V3_DIAGNOSTICS",
        action="KEEP",
        notes="Network diagnostic telemetry — core of V3",
    ),
    Module(
        name="Diagnostics",
        route_file="app/routes/diagnostics.py",
        api_prefix="/api/v1/diagnostics",
        db_tables=[],
        description="System self-check (DB connectivity, platform info, app stats)",
        target_session="SHARED",
        action="KEEP",
        notes="Useful for both sessions as an internal health endpoint",
    ),
    Module(
        name="Dashboard",
        route_file="app/routes/dashboard.py",
        api_prefix="/api/v1/dashboard",
        db_tables=[],
        description="Aggregated stats for tickets, chat, monitoring data",
        target_session="V1_HEALTH_CHECK",
        action="RENAME",
        notes="Currently mixes V1 + V3 data; needs splitting per session",
    ),
]


# ─── Session definitions ─────────────────────────────────────────────

SESSIONS = {
    "V3_DIAGNOSTICS": {
        "display_name": "ZA Support V3 — Diagnostic Software",
        "description": (
            "Lightweight diagnostic agent backend. Receives telemetry "
            "from client machines (CPU, memory, disk, threats) and network "
            "controllers. Provides real-time and historical monitoring."
        ),
        "primary_modules": ["Health Monitoring", "Network Monitoring"],
        "shared_modules": ["Auth", "Diagnostics"],
        "db_tables": ["users", "health_data", "network_data"],
        "api_key_auth": True,
        "jwt_auth": False,
        "render_service_name": "za-diagnostics-v3",
    },
    "V1_HEALTH_CHECK": {
        "display_name": "ZA Support V1 — Full Health Check Software",
        "description": (
            "Complete support-desk backend with ticketing, real-time chat, "
            "user management, and an admin dashboard. The central hub for "
            "customer support and issue resolution."
        ),
        "primary_modules": ["Tickets", "Chat", "Dashboard"],
        "shared_modules": ["Auth", "Diagnostics"],
        "db_tables": ["users", "tickets", "chat_sessions", "chat_messages"],
        "api_key_auth": False,
        "jwt_auth": True,
        "render_service_name": "za-support-v1",
    },
}


# ─── Git branch analysis ─────────────────────────────────────────────

GIT_BRANCHES = {
    "claude/identify-database-chat-LxAki": {
        "purpose": "PR #1 — Initial build (DB + chat identification)",
        "status": "MERGED",
        "action": "ARCHIVE — already merged into main",
    },
    "claude/complete-system-LxAki": {
        "purpose": "PR #2 — Tests, CI, JWT fixes, Railway removal",
        "status": "MERGED",
        "action": "ARCHIVE — already merged into main",
    },
    "claude/fix-render-deploy-LxAki": {
        "purpose": "PR #3 — Render deploy fix, Python version pin",
        "status": "MERGED",
        "action": "ARCHIVE — already merged into main",
    },
    "claude/consolidate-sessions-wZS7l": {
        "purpose": "Current — session consolidation work",
        "status": "ACTIVE",
        "action": "KEEP — current working branch",
    },
    "master": {
        "purpose": "Original upload (bare initial commit)",
        "status": "STALE",
        "action": "ARCHIVE — 'main' is the true default branch on GitHub",
    },
}


# ─── Database analysis ────────────────────────────────────────────────

DATABASE = {
    "name": "zasupport",
    "provider": "Render PostgreSQL",
    "render_db_name": "za-support-db",
    "status": "KEEP — single source of truth for both sessions",
    "tables": {
        "users":         {"session": "SHARED",          "rows_source": "auth",    "action": "KEEP"},
        "tickets":       {"session": "V1_HEALTH_CHECK", "rows_source": "tickets", "action": "KEEP"},
        "chat_sessions": {"session": "V1_HEALTH_CHECK", "rows_source": "chat",    "action": "KEEP"},
        "chat_messages": {"session": "V1_HEALTH_CHECK", "rows_source": "chat",    "action": "KEEP"},
        "health_data":   {"session": "V3_DIAGNOSTICS",  "rows_source": "health",  "action": "KEEP"},
        "network_data":  {"session": "V3_DIAGNOSTICS",  "rows_source": "network", "action": "KEEP"},
    },
}


# ─── Files that can be cleaned up ────────────────────────────────────

CLEANUP_CANDIDATES = [
    {
        "file": "encryption_key.txt",
        "action": "ALREADY REMOVED",
        "reason": "Removed from repo; use ENCRYPTION_KEY env var on Render instead",
    },
    {
        "file": "main_integrated.py",
        "action": "ALREADY REMOVED",
        "reason": "Was removed in PR #2 — old monolithic entry point",
    },
    {
        "file": "railway.json",
        "action": "ALREADY REMOVED",
        "reason": "Was removed in PR #2 — Railway is no longer used",
    },
]


# ─── Report generation ───────────────────────────────────────────────

SEPARATOR = "=" * 72

def print_header(title: str):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def print_section(title: str):
    print(f"\n--- {title} ---\n")


def run_audit():
    print_header("ZA SUPPORT — SESSION CONSOLIDATION AUDIT")
    print(f"  Repository: za-support-backendV1")
    print(f"  Database:   zasupport (Render PostgreSQL)")
    print(f"  Status:     NEEDS CONSOLIDATION")

    # ── Target sessions ──
    print_header("TARGET STATE: 2 SESSIONS")
    for key, session in SESSIONS.items():
        print(f"\n  [{key}]")
        print(f"  Name:     {session['display_name']}")
        print(f"  Purpose:  {session['description']}")
        print(f"  Modules:  {', '.join(session['primary_modules'])}")
        print(f"  Shared:   {', '.join(session['shared_modules'])}")
        print(f"  Tables:   {', '.join(session['db_tables'])}")
        print(f"  Service:  {session['render_service_name']}")

    # ── Module mapping ──
    print_header("MODULE → SESSION MAPPING")
    for mod in MODULES:
        indicator = {
            "V3_DIAGNOSTICS": "[V3-DIAG]",
            "V1_HEALTH_CHECK": "[V1-FULL]",
            "SHARED": "[SHARED ]",
        }[mod.target_session]
        print(f"  {indicator}  {mod.name:<20s}  {mod.action:<8s}  {mod.api_prefix}")
        if mod.db_tables:
            print(f"            Tables: {', '.join(mod.db_tables)}")
        print(f"            → {mod.notes}")

    # ── Database tables ──
    print_header("DATABASE TABLE OWNERSHIP")
    print(f"  Database: {DATABASE['name']} ({DATABASE['provider']})")
    print(f"  Status:   {DATABASE['status']}\n")
    for table, info in DATABASE["tables"].items():
        label = {
            "SHARED": "[SHARED ]",
            "V3_DIAGNOSTICS": "[V3-DIAG]",
            "V1_HEALTH_CHECK": "[V1-FULL]",
        }[info["session"]]
        print(f"  {label}  {table:<20s}  source: {info['rows_source']:<10s}  {info['action']}")

    # ── Git branches ──
    print_header("GIT BRANCH AUDIT")
    for branch, info in GIT_BRANCHES.items():
        status_icon = {"MERGED": "✓", "ACTIVE": "►", "STALE": "✗"}[info["status"]]
        print(f"  {status_icon} {branch}")
        print(f"    Purpose: {info['purpose']}")
        print(f"    Action:  {info['action']}")

    # ── Cleanup candidates ──
    print_header("FILE CLEANUP CANDIDATES")
    for item in CLEANUP_CANDIDATES:
        print(f"  [{item['action']:<16s}]  {item['file']}")
        print(f"                       {item['reason']}")

    # ── Action plan ──
    print_header("RECOMMENDED ACTION PLAN")
    steps = [
        "1. RENAME this repo session to 'ZA Support V1 — Full Health Check'",
        "   - This repo (za-support-backendV1) becomes the V1 support desk",
        "   - Keep modules: Auth, Tickets, Chat, Dashboard, Diagnostics",
        "",
        "2. CREATE a new repo/session for 'ZA Support V3 — Diagnostics'",
        "   - Extract: Health Monitoring + Network Monitoring routes",
        "   - Share: Auth module, database connection",
        "   - Own Render service: za-diagnostics-v3",
        "",
        "3. ARCHIVE old git branches (all PRs are merged):",
        "   - claude/identify-database-chat-LxAki",
        "   - claude/complete-system-LxAki",
        "   - claude/fix-render-deploy-LxAki",
        "   - master (stale — 'main' is the true default)",
        "",
        "4. KEEP the 'zasupport' database as-is:",
        "   - Both V1 and V3 connect to the same DB",
        "   - Tables are cleanly separated by domain",
        "   - 'users' table is shared for authentication",
        "",
        "5. SET ENCRYPTION_KEY env var on Render dashboard",
        "   - encryption_key.txt already removed from repo",
        "   - ENCRYPTION_KEY declared in render.yaml (set value in Render UI)",
    ]
    for step in steps:
        print(f"  {step}")

    print(f"\n{SEPARATOR}")
    print(f"  Audit complete. Run with --json for machine-readable output.")
    print(f"{SEPARATOR}\n")


def run_json_audit():
    """Output the full audit as JSON for programmatic consumption."""
    report = {
        "target_sessions": SESSIONS,
        "modules": [asdict(m) for m in MODULES],
        "database": DATABASE,
        "git_branches": GIT_BRANCHES,
        "cleanup_candidates": CLEANUP_CANDIDATES,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if "--json" in sys.argv:
        run_json_audit()
    else:
        run_audit()
