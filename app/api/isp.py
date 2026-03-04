from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def isp_health():
    return {"module": "isp_monitor", "status": "ok"}
