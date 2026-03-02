"""
ZA Support V1 — Full Health Check Software
Entry point for the support-desk session: tickets, chat, dashboard.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import Base, engine, SessionLocal
from app.models import User, UserRole
from app.auth import hash_password
from app.config import PORT

from app.routes.auth import router as auth_router
from app.routes.tickets import router as tickets_router
from app.routes.chat import router as chat_router
from app.routes.dashboard import router as dashboard_router
from app.routes.diagnostics import router as diagnostics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        _seed_admin()
    except Exception as e:
        logger.warning(f"Startup DB init skipped (DB may not be ready): {e}")
    yield
    logger.info("ZA Support V1 shutting down")


def _seed_admin():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == UserRole.admin).first():
            return
        admin = User(
            email="admin@zasupport.com",
            username="admin",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        logger.info("Default admin user created (admin@zasupport.com / admin123)")
    finally:
        db.close()


# -- V1 router: only support-desk routes --
v1_api = APIRouter(prefix="/api/v1")
v1_api.include_router(auth_router)
v1_api.include_router(tickets_router)
v1_api.include_router(chat_router)
v1_api.include_router(dashboard_router)
v1_api.include_router(diagnostics_router)

app = FastAPI(
    title="ZA Support V1 — Full Health Check",
    description="Support desk: tickets, real-time chat, user management, dashboard",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_api)


@app.get("/")
async def root():
    return {
        "service": "ZA Support V1 — Full Health Check",
        "version": "2.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "tickets": "/api/v1/tickets",
            "chat": "/api/v1/chat",
            "dashboard": "/api/v1/dashboard",
            "diagnostics": "/api/v1/diagnostics",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ZA Support V1", "version": "2.1.0"}


if __name__ == "__main__":
    import uvicorn

    logger.info("ZA SUPPORT V1 — FULL HEALTH CHECK — STARTING")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
