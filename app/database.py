# Backward-compat shim — all database now lives in app.core.database
from app.core.database import *  # noqa: F401,F403
from app.core.database import Base, engine, SessionLocal, get_db, get_session_factory  # noqa: F401
