"""
ZA Support V3 — Diagnostic Software
Entry point for the diagnostics session: machine health, network monitoring.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import Base, engine
from app.config import PORT

from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.network import router as network_router
from app.routes.diagnostics import router as diagnostics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.warning(f"Startup DB init skipped (DB may not be ready): {e}")
    yield
    logger.info("ZA Support V3 shutting down")


# -- V3 router: only diagnostic routes --
v3_api = APIRouter(prefix="/api/v1")
v3_api.include_router(auth_router)
v3_api.include_router(health_router)
v3_api.include_router(network_router)
v3_api.include_router(diagnostics_router)

app = FastAPI(
    title="ZA Support V3 — Diagnostics",
    description="Diagnostic agent: machine health telemetry, network monitoring",
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

app.include_router(v3_api)


@app.get("/")
async def root():
    return {
        "service": "ZA Support V3 — Diagnostics",
        "version": "2.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "health_monitoring": "/api/v1/health",
            "network_monitoring": "/api/v1/network",
            "diagnostics": "/api/v1/diagnostics",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ZA Support V3", "version": "2.1.0"}


if __name__ == "__main__":
    import uvicorn

    logger.info("ZA SUPPORT V3 — DIAGNOSTICS — STARTING")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
