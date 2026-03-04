from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class HealthSubmission(BaseModel):
    machine_id: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    battery_percent: Optional[float] = None
    battery_cycle_count: Optional[int] = None
    battery_health: Optional[str] = None
    threat_score: int = 0
    uptime_hours: Optional[float] = None
    network_up_mbps: Optional[float] = None
    network_down_mbps: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None


class HealthOut(BaseModel):
    id: int
    machine_id: str
    timestamp: datetime
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    battery_percent: Optional[float] = None
    threat_score: int = 0

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    id: int
    machine_id: str
    timestamp: datetime
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    battery_percent: Optional[float] = None
    threat_score: int = 0

    model_config = {"from_attributes": True}
