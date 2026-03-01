from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import Base, engine
from app.routes import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZA Support Backend API",
    description="Complete support backend with tickets, real-time chat, health monitoring, and diagnostics",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all database tables on startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
except Exception as e:
    logger.warning(f"Could not create tables on startup (DB may not be available yet): {e}")

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
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ZA Support Backend", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    from app.config import PORT

    logger.info("ZA SUPPORT BACKEND v2.0 STARTING")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
