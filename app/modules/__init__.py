"""
Module router aggregator.
Each module exposes its own APIRouter. To enable/disable a module,
comment out or add its include_router() line below.
"""
from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.tickets.router import router as tickets_router
from app.modules.chat.router import router as chat_router
from app.modules.health.router import router as health_router
from app.modules.network.router import router as network_router
from app.modules.devices.router import router as devices_router
from app.modules.alerts.router import router as alerts_router
from app.modules.diagnostics.router import router as diagnostics_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.isp.router import router as isp_router

api_router = APIRouter(prefix="/api/v1")

# ── Core modules (always included) ──
api_router.include_router(auth_router)
api_router.include_router(devices_router)
api_router.include_router(health_router)
api_router.include_router(alerts_router)
api_router.include_router(diagnostics_router)
api_router.include_router(dashboard_router)

# ── Support modules ──
api_router.include_router(tickets_router)
api_router.include_router(chat_router)

# ── Monitoring modules ──
api_router.include_router(network_router)
api_router.include_router(isp_router)
