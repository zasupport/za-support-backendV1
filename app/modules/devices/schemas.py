from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class DeviceRegister(BaseModel):
    machine_id: str
    hostname: Optional[str] = None
    device_type: str = "other"
    model_identifier: Optional[str] = None
    serial_number: Optional[str] = None
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    client_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    id: int
    machine_id: str
    client_id: Optional[str] = None
    hostname: Optional[str] = None
    device_type: str
    model_identifier: Optional[str] = None
    serial_number: Optional[str] = None
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    last_seen: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"from_attributes": True}
