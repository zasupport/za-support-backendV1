from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.tickets import router as tickets_router
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.network import router as network_router
from app.routes.diagnostics import router as diagnostics_router
from app.routes.dashboard import router as dashboard_router
from app.routes.devices import router as devices_router
from app.routes.alerts import router as alerts_router
from app.routes.isp import router as isp_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(tickets_router)
api_router.include_router(chat_router)
api_router.include_router(health_router)
api_router.include_router(network_router)
api_router.include_router(diagnostics_router)
api_router.include_router(dashboard_router)
api_router.include_router(devices_router)
api_router.include_router(alerts_router)
api_router.include_router(isp_router)
