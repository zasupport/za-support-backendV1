from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import Base, engine, SessionLocal
from app.models import User, UserRole
from app.auth import hash_password
from app.routes import api_router
from app.config import PORT
from agent_router import router as agent_router
from router_networking import router as networking_router, manager, correlator, bind_scheduler
from scheduler import ISPMonitorScheduler, AlertStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared alert store + scheduler instance
alert_store = AlertStore()
isp_scheduler = ISPMonitorScheduler(
    manager=manager,
    correlator=correlator,
    alert_store=alert_store,
    interval_seconds=300,
)
bind_scheduler(alert_store, isp_scheduler)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # --- Startup ---
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        _seed_admin()
    except Exception as e:
        logger.warning(f"Startup DB init skipped (DB may not be ready): {e}")
    await isp_scheduler.start()
    yield
    # --- Shutdown ---
    await isp_scheduler.stop()
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
    description="Complete support backend with tickets, real-time chat, health monitoring, ISP outage correlation, alerts, and background scheduling",
    version="3.0.0",
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
app.include_router(agent_router)
app.include_router(networking_router)


@app.get("/")
async def root():
    return {
        "service": "ZA Support Backend API",
        "version": "3.0.0",
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
            "agent": "/api/v1/agent",
            "isp_networking": "/api/v1/isp",
            "isp_alerts": "/api/v1/isp/alerts",
            "isp_correlation": "/api/v1/isp/isps/{isp_slug}/correlate",
            "scheduler_status": "/api/v1/isp/scheduler-status",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ZA Support Backend", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn

    logger.info("ZA SUPPORT BACKEND v3.0 STARTING")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
