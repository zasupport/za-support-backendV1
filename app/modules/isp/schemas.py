from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ISPProviderCreate(BaseModel):
    name: str
    slug: str
    status_page_url: Optional[str] = None
    downdetector_slug: Optional[str] = None
    probe_targets: Optional[List[str]] = None
    gateway_ip: Optional[str] = None
    underlying_provider: Optional[str] = None


class ISPProviderUpdate(BaseModel):
    name: Optional[str] = None
    status_page_url: Optional[str] = None
    downdetector_slug: Optional[str] = None
    probe_targets: Optional[List[str]] = None
    gateway_ip: Optional[str] = None
    underlying_provider: Optional[str] = None
    is_active: Optional[bool] = None


class ISPProviderResponse(BaseModel):
    id: int
    name: str
    slug: str
    status_page_url: Optional[str] = None
    downdetector_slug: Optional[str] = None
    probe_targets: Optional[List[str]] = None
    gateway_ip: Optional[str] = None
    underlying_provider: Optional[str] = None
    current_status: str = "operational"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StatusCheckSubmission(BaseModel):
    provider_id: int
    source: str
    status: str = "operational"
    response_time_ms: Optional[float] = None
    http_status_code: Optional[int] = None
    error_message: Optional[str] = None
    is_healthy: bool = True


class StatusCheckResponse(BaseModel):
    id: int
    provider_id: int
    timestamp: datetime
    source: str
    status: str
    response_time_ms: Optional[float] = None
    http_status_code: Optional[int] = None
    error_message: Optional[str] = None
    is_healthy: bool

    model_config = {"from_attributes": True}


class AgentHeartbeat(BaseModel):
    machine_id: str
    provider_id: int
    state: str = "connected"
    latency_ms: Optional[float] = None
    packet_loss_pct: Optional[float] = None
    gateway_reachable: Optional[bool] = None
    dns_reachable: Optional[bool] = None


class AgentConnectivityResponse(BaseModel):
    id: int
    machine_id: str
    provider_id: int
    timestamp: datetime
    state: str
    latency_ms: Optional[float] = None
    packet_loss_pct: Optional[float] = None
    gateway_reachable: Optional[bool] = None
    dns_reachable: Optional[bool] = None

    model_config = {"from_attributes": True}


class ISPOutageCreate(BaseModel):
    provider_id: int
    severity: str = "outage"
    description: Optional[str] = None


class ISPOutageResponse(BaseModel):
    id: int
    provider_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    severity: str
    confirmed: bool
    confirmation_sources: Optional[List[str]] = None
    description: Optional[str] = None
    auto_resolved: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ISPProviderStatus(BaseModel):
    provider: ISPProviderResponse
    recent_checks: List[StatusCheckResponse] = []
    active_outage: Optional[ISPOutageResponse] = None


class ISPDashboard(BaseModel):
    total_providers: int = 0
    operational_count: int = 0
    degraded_count: int = 0
    outage_count: int = 0
    unknown_count: int = 0
    active_outages: List[ISPOutageResponse] = []
    providers: List[ISPProviderStatus] = []
