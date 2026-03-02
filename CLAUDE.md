# ZA Support Platform — Project Instructions

## Project Identity

This repo is **ZA Support V1 — Full Health Check Software**.
It is the support-desk backend: ticketing, real-time chat, user management, dashboard.

There are exactly **two products** in the ZA Support platform:

| Session | Repo | Purpose |
|---------|------|---------|
| **V1 Full Health Check** | `za-support-backendV1` (this repo) | Support desk: tickets, chat, dashboard |
| **V3 Diagnostics** | `za-diagnostics-v3` (to be extracted) | Machine/network telemetry agent |

Both share a single **`zasupport` PostgreSQL database** on Render.
See `SESSION_MAP.json` for the full module/table mapping.

## Database

- **Name:** `zasupport`
- **Provider:** Render PostgreSQL (`za-support-db`)
- **V1 tables:** `users`, `tickets`, `chat_sessions`, `chat_messages`
- **V3 tables:** `users` (shared), `health_data`, `network_data`
- Never create a new database — both sessions use this one.

## Tech Stack

- Python 3.11 / FastAPI / SQLAlchemy / Pydantic v2
- PostgreSQL (Render) / SQLite (tests)
- JWT auth (V1) / API-Key auth (V3 health/network endpoints)
- Deployed to Render (`render.yaml`)

## Development Rules

- Run `python scripts/session_audit.py` before major changes to verify module ownership.
- Tests: `pytest tests/` (uses in-memory SQLite, no external DB needed).
- Never commit secrets. `encryption_key.txt` is legacy — use env vars.
- Default branch on GitHub is `main`, not `master`.

## Preferences

### CRITICAL — End-of-Task Next Steps

After completing ANY task (code change, analysis, fix, feature, or question), ALWAYS finish your response with a clearly formatted next-steps block. This is mandatory — never skip it.

Format:

```
---
## What's Next

**Completed:** [1-line summary of what was just done]

**Ready to execute now:**
1. [Concrete next action — be specific, not vague]
2. [Another action if applicable]

**Backlog (upcoming):**
- [Future task that feeds off the above]
- [Another future task]

**Blockers / Decisions needed:**
- [Anything that requires user input before proceeding]

> Say "go" to execute the next ready item, or pick a number.
```

Rules for the next-steps block:
- "Ready to execute now" items must be specific and actionable (e.g. "Extract health + network routes into za-diagnostics-v3 repo" not "continue working")
- "Backlog" items are things that logically follow but aren't immediate
- "Blockers" are questions or decisions only the user can answer
- If there are no blockers, omit that section
- Always offer to execute the next ready item automatically
- Reference SESSION_MAP.json and the audit tool when recommending cross-session work

### CRITICAL — Auto-Execute Next Steps

When the user says "go", execute the next ready item from the What's Next block **immediately and fully** — do not ask for confirmation, do not re-explain the plan, do not pause to ask which item. Just do it. Treat "go" as "execute item #1 from Ready to execute now, start to finish, then show the updated What's Next block."

This applies to all variations: "go", "Go", "GO", "do it", "next", "proceed", "continue", "yes", or any affirmative single-word response after a What's Next block.

**Never** respond to "go" with a question or summary. Respond with action.

### General Preferences

- Be concise. No filler.
- When writing code, run tests after changes.
- Commit and push completed work without being asked.
- Use the todo list for multi-step tasks.
- When in doubt about V1 vs V3 ownership, run `python scripts/session_audit.py`.
