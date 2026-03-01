import platform
import os
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/")
def full_diagnostics(db: Session = Depends(get_db)):
    """Complete system diagnostics — database, system, and application health."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": _check_database(db),
        "system": _get_system_info(),
        "application": _get_app_info(db),
    }


@router.get("/db")
def database_diagnostics(db: Session = Depends(get_db)):
    """Database connectivity and table diagnostics."""
    return _check_database(db)


@router.get("/system")
def system_diagnostics():
    """System-level diagnostics (OS, platform, environment)."""
    return _get_system_info()


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
        "hostname": platform.node(),
        "port": os.getenv("PORT", "8080"),
    }


def _get_app_info(db: Session) -> dict:
    from app.models import User, Ticket, ChatSession, ChatMessage, HealthData, NetworkData

    try:
        return {
            "version": "2.0.0",
            "users": db.query(User).count(),
            "tickets": db.query(Ticket).count(),
            "chat_sessions": db.query(ChatSession).count(),
            "chat_messages": db.query(ChatMessage).count(),
            "health_records": db.query(HealthData).count(),
            "network_records": db.query(NetworkData).count(),
        }
    except Exception as e:
        return {"version": "2.0.0", "error": str(e)}
