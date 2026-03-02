from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import Base, engine, SessionLocal
from app.models import User, UserRole
from app.auth import hash_password
from app.routes import api_router
from app.config import PORT
from app.services.isp_scheduler import start_isp_scheduler, stop_isp_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # --- Startup ---
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        _seed_admin()
    except Exception as e:
        logger.warning(f"Startup DB init skipped (DB may not be ready): {e}")

    # Start ISP monitor background scheduler
    try:
        start_isp_scheduler()
    except Exception as e:
        logger.warning(f"ISP scheduler startup skipped: {e}")

    yield

    # --- Shutdown ---
    try:
        stop_isp_scheduler()
    except Exception:
        pass
    logger.info("ZA Support Backend shutting down")


def _seed_admin():
    """Create a default admin user if none exists."""
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


app = FastAPI(
    title="ZA Support Backend API",
    description="Complete support backend with tickets, real-time chat, health monitoring, and diagnostics",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "ZA Support Backend API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "tickets": "/api/v1/tickets",
            "chat": "/api/v1/chat",
            "health_monitoring": "/api/v1/health",
            "network_monitoring": "/api/v1/network",
            "diagnostics": "/api/v1/diagnostics",
            "dashboard": "/api/v1/dashboard",
            "devices": "/api/v1/devices",
            "alerts": "/api/v1/alerts",
            "isp_monitor": "/api/v1/isp",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ZA Support Backend", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn

    logger.info("ZA SUPPORT BACKEND v2.0 STARTING")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
