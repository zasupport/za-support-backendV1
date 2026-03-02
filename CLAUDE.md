# Preferences

- Always proceed with next steps autonomously. Do not ask "should I proceed?", "would you like me to...", or "shall I..." — just do it.
- When multiple tasks are identified, work through all of them sequentially without pausing for approval between steps.
- Create PRs, commit, push, and deploy without confirmation prompts.
- If a decision needs to be made between approaches, pick the most practical one and move forward.
- When files need to be created or modified, execute immediately without asking for permission first.

# Project

- **Stack**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL (Render), JWT auth
- **Live service**: `za-support-backend` on Render (Starter plan, Oregon)
- **Database**: `za-support-db` (Postgres Basic 1GB, Oregon)
- **Deploy branch**: `main` (auto-deploy on push)
- **Environment variables** (required): `SECRET_KEY`, `API_KEY`, `DATABASE_URL`, `ADMIN_PASSWORD`, `ALLOWED_ORIGINS`, `ENVIRONMENT`
- **Rate limiting**: slowapi on `/auth/login` (10/min) and `/auth/register` (5/min)
- **CORS**: controlled via `ALLOWED_ORIGINS` env var (comma-separated)
- **Swagger docs**: disabled when `ENVIRONMENT=production`
- **Tests**: pytest with in-memory SQLite; env vars set in `tests/conftest.py` before app import
