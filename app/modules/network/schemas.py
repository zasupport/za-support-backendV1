from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class NetworkSubmission(BaseModel):
    controller_id: str
    total_clients: Optional[int] = None
    total_devices: Optional[int] = None
    wan_status: Optional[str] = None
    wan_latency_ms: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None


class NetworkOut(BaseModel):
    id: int
    controller_id: str
    timestamp: datetime
    total_clients: int
    total_devices: int

    model_config = {"from_attributes": True}
