import platform
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.modules.auth.models import User, UserRole

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/")
def full_diagnostics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete system diagnostics — database, system, and application health. Admin/agent only."""
    if current_user.role not in (UserRole.agent, UserRole.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": _check_database(db),
        "system": _get_system_info(),
        "application": _get_app_info(db),
    }


@router.get("/db")
def database_diagnostics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Database connectivity and table diagnostics. Admin/agent only."""
    if current_user.role not in (UserRole.agent, UserRole.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    return _check_database(db)


@router.get("/system")
def system_diagnostics(current_user: User = Depends(get_current_user)):
    """System-level diagnostics (OS, platform, environment). Admin/agent only."""
    if current_user.role not in (UserRole.agent, UserRole.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    return _get_system_info()


@router.get("/deploy")
def deploy_status(db: Session = Depends(get_db)):
    """Quick deploy verification — returns OK if DB is connected and tables exist."""
    try:
        db.execute(text("SELECT 1")).fetchone()
        from app.modules.auth.models import User
        user_count = db.query(User).count()
        return {
            "status": "ok",
            "database": "connected",
            "users": user_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def _check_database(db: Session) -> dict:
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        connected = result is not None

        # Get table info (works with both PostgreSQL and SQLite)
        dialect = db.bind.dialect.name if db.bind else "unknown"
        if dialect == "postgresql":
            tables_result = db.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )).fetchall()
        else:
            tables_result = db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )).fetchall()
        tables = [row[0] for row in tables_result]

        # Get row counts
        table_counts = {}
        for table in tables:
            count = db.execute(text(f"SELECT COUNT(*) FROM \"{table}\"")).fetchone()
            table_counts[table] = count[0] if count else 0

        return {
            "status": "connected" if connected else "disconnected",
            "dialect": dialect,
            "tables": tables,
            "row_counts": table_counts,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def _get_system_info() -> dict:
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "port": os.getenv("PORT", "8080"),
    }


def _get_app_info(db: Session) -> dict:
    from app.modules.auth.models import User
    from app.modules.tickets.models import Ticket
    from app.modules.chat.models import ChatSession, ChatMessage
    from app.modules.health.models import HealthData
    from app.modules.network.models import NetworkData
    from app.modules.devices.models import Device
    from app.modules.alerts.models import Alert
    from app.modules.isp.models import ISPProvider, ISPOutage
    from app.modules.diagnostics.models import WorkshopDiagnostic

    try:
        return {
            "version": "2.0.0",
            "users": db.query(User).count(),
            "tickets": db.query(Ticket).count(),
            "chat_sessions": db.query(ChatSession).count(),
            "chat_messages": db.query(ChatMessage).count(),
            "health_records": db.query(HealthData).count(),
            "network_records": db.query(NetworkData).count(),
            "devices": db.query(Device).count(),
            "alerts": db.query(Alert).count(),
            "isp_providers": db.query(ISPProvider).count(),
            "isp_outages": db.query(ISPOutage).count(),
            "workshop_diagnostics": db.query(WorkshopDiagnostic).count(),
        }
    except Exception as e:
        return {"version": "2.0.0", "error": str(e)}
