from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging

from sqlalchemy import inspect, text
from app.core.database import Base, engine, SessionLocal
from app.core.auth import hash_password
from app.core.config import PORT, ALLOWED_ORIGINS, ADMIN_PASSWORD, ENVIRONMENT

# Import all module models so SQLAlchemy discovers them for create_all()
from app.modules.auth.models import User, UserRole
from app.modules.tickets.models import Ticket  # noqa: F401
from app.modules.chat.models import ChatSession, ChatMessage  # noqa: F401
from app.modules.devices.models import Device  # noqa: F401
from app.modules.health.models import HealthData  # noqa: F401
from app.modules.network.models import NetworkData  # noqa: F401
from app.modules.alerts.models import Alert  # noqa: F401
from app.modules.diagnostics.models import WorkshopDiagnostic  # noqa: F401
from app.modules.isp.models import ISPProvider, ISPStatusCheck, AgentConnectivity, ISPOutage  # noqa: F401

from app.modules import api_router
from app.modules.auth.router import limiter
from app.modules.isp.scheduler import start_isp_scheduler, stop_isp_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # --- Startup ---
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        _migrate_columns()
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


def _migrate_columns():
    """Add any missing columns to existing tables so models match the live schema."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for col in table.columns:
                if col.name not in existing:
                    col_type = col.type.compile(dialect=engine.dialect)
                    nullable = "NULL" if col.nullable else "NOT NULL"
                    default = ""
                    if col.default is not None and col.default.arg is not None:
                        val = col.default.arg
                        if isinstance(val, bool):
                            default = f" DEFAULT {str(val).upper()}"
                        elif isinstance(val, (int, float)):
                            default = f" DEFAULT {val}"
                        elif isinstance(val, str):
                            default = f" DEFAULT '{val}'"
                    stmt = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type} {nullable}{default}'
                    conn.execute(text(stmt))
                    logger.info(f"Added column {table.name}.{col.name}")

    # Ensure any orphan health_data rows have a matching device (FK constraint)
    if inspector.has_table("health_data") and inspector.has_table("devices"):
        with engine.begin() as conn:
            orphans = conn.execute(text(
                "SELECT DISTINCT h.machine_id FROM health_data h "
                "LEFT JOIN devices d ON h.machine_id = d.machine_id "
                "WHERE d.machine_id IS NULL"
            )).fetchall()
            for (mid,) in orphans:
                conn.execute(text(
                    "INSERT INTO devices (machine_id, device_type, is_active) "
                    "VALUES (:mid, 'other', true)"
                ), {"mid": mid})
                logger.info(f"Auto-registered orphan device: {mid}")


def _seed_admin():
    """Create a default admin user if none exists (requires ADMIN_PASSWORD env var)."""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == UserRole.admin).first():
            return
        if not ADMIN_PASSWORD:
            logger.warning("No ADMIN_PASSWORD set — skipping admin seed")
            return
        admin = User(
            email="admin@zasupport.com",
            username="admin",
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        logger.info("Default admin user created (admin@zasupport.com)")
    finally:
        db.close()


# Disable Swagger UI in production
docs_url = "/docs" if ENVIRONMENT != "production" else None
openapi_url = "/openapi.json" if ENVIRONMENT != "production" else None

app = FastAPI(
    title="V11 Health Check — ZA Support API",
    description="Modular backend: health monitoring, device management, support tickets, real-time chat, ISP outage detection, and diagnostics",
    version="3.0.0",
    lifespan=lifespan,
    docs_url=docs_url,
    openapi_url=openapi_url,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all module routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "V11 Health Check — ZA Support API",
        "version": "3.0.0",
        "architecture": "modular",
        "status": "running",
        "modules": {
            "core": ["auth", "devices", "health", "alerts", "diagnostics", "dashboard"],
            "support": ["tickets", "chat"],
            "monitoring": ["network", "isp"],
        },
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
    return {"status": "healthy", "service": "V11 Health Check", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn

    logger.info("V11 HEALTH CHECK — ZA SUPPORT API v3.0 STARTING")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
