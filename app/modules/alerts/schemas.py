from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    machine_id: str
    timestamp: datetime
    severity: str
    category: str
    message: str
    resolved: bool
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
