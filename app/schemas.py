from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import UserRole, TicketStatus, TicketPriority, ChatSessionStatus, MessageType


# --- Auth ---

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class RoleUpdate(BaseModel):
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Tickets ---

class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: Optional[TicketPriority] = TicketPriority.medium


class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[int] = None


class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    user_id: int
    assigned_agent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Chat ---

class ChatSessionCreate(BaseModel):
    ticket_id: Optional[int] = None


class ChatSessionOut(BaseModel):
    id: int
    ticket_id: Optional[int]
    user_id: int
    agent_id: Optional[int]
    status: ChatSessionStatus
    created_at: datetime
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str
    message_type: Optional[MessageType] = MessageType.text


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    sender_id: int
    content: str
    message_type: MessageType
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Device Schemas (ported from old repo) ---

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


# --- Health (enhanced with old repo fields) ---

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


# --- Network (enhanced with old repo fields) ---

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


# --- Alerts (ported from old repo) ---

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


# --- Dashboard (enhanced with old repo schemas) ---

class DeviceHealthSummary(BaseModel):
    machine_id: str
    hostname: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    status: str = "unknown"
    cpu: Optional[float] = None
    memory: Optional[float] = None
    disk: Optional[float] = None
    battery: Optional[float] = None
    threat: int = 0
    last_seen: Optional[datetime] = None
    open_alerts: int = 0


class DashboardOverview(BaseModel):
    total_devices: int = 0
    active_devices: int = 0
    critical_alerts: int = 0
    warning_alerts: int = 0
    devices: List[DeviceHealthSummary] = []


# --- Diagnostic Upload (ported from old repo) ---

class DiagnosticHardware(BaseModel):
    serial: str = ""
    chip_type: str = ""
    model: str = ""
    model_id: str = ""
    hw_uuid: str = ""
    ram_gb: int = 0
    ram_upgradeable: str = ""
    cpu: str = ""
    cores_physical: int = 0
    cores_logical: int = 0


class DiagnosticMacOS(BaseModel):
    version: str = ""
    build: str = ""
    uptime_seconds: int = 0


class DiagnosticSecurity(BaseModel):
    sip_enabled: int = 0
    filevault_on: int = 0
    firewall_on: int = 0
    gatekeeper_on: int = 0
    xprotect_version: str = ""
    password_manager: str = "none"
    av_edr: str = "none"


class DiagnosticBattery(BaseModel):
    health_pct: Optional[str] = None
    cycles: Optional[str] = None
    design_capacity_mah: Optional[str] = None
    max_capacity_mah: Optional[str] = None
    condition: Optional[str] = None


class DiagnosticStorage(BaseModel):
    boot_disk_used_pct: int = 0
    boot_disk_free_gb: int = 0


class DiagnosticOCLP(BaseModel):
    detected: bool = False
    version: str = "N/A"
    root_patched: bool = False
    third_party_kexts: int = 0


class DiagnosticDiagnostics(BaseModel):
    kernel_panics: int = 0
    total_processes: int = 0


class DiagnosticRecommendation(BaseModel):
    severity: str = ""
    title: str = ""
    evidence: str = ""
    product: str = ""
    price: str = ""


class DiagnosticUpload(BaseModel):
    version: str = "3.0"
    generated: str = ""
    mode: str = "full"
    serial: str = ""
    hostname: str = ""
    client_id: str = ""
    hardware: DiagnosticHardware = DiagnosticHardware()
    macos: DiagnosticMacOS = DiagnosticMacOS()
    security: DiagnosticSecurity = DiagnosticSecurity()
    battery: DiagnosticBattery = DiagnosticBattery()
    storage: DiagnosticStorage = DiagnosticStorage()
    oclp: DiagnosticOCLP = DiagnosticOCLP()
    diagnostics: DiagnosticDiagnostics = DiagnosticDiagnostics()
    recommendations: List[DiagnosticRecommendation] = []
    recommendation_count: int = 0
    runtime_seconds: int = 0


class DiagnosticResponse(BaseModel):
    id: int
    serial_number: str
    hostname: Optional[str] = None
    client_id: Optional[str] = None
    diagnostic_version: Optional[str] = None
    mode: Optional[str] = None
    chip_type: Optional[str] = None
    model_name: Optional[str] = None
    macos_version: Optional[str] = None
    battery_health_pct: Optional[float] = None
    battery_cycles: Optional[int] = None
    disk_used_pct: Optional[int] = None
    disk_free_gb: Optional[int] = None
    sip_enabled: Optional[bool] = None
    filevault_on: Optional[bool] = None
    firewall_on: Optional[bool] = None
    kernel_panics: int = 0
    oclp_detected: bool = False
    recommendation_count: int = 0
    recommendations: Optional[List[Dict[str, Any]]] = None
    runtime_seconds: Optional[int] = None
    captured_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DiagnosticSummary(BaseModel):
    id: int
    serial_number: str
    client_id: Optional[str] = None
    mode: Optional[str] = None
    model_name: Optional[str] = None
    macos_version: Optional[str] = None
    battery_health_pct: Optional[float] = None
    disk_used_pct: Optional[int] = None
    recommendation_count: int = 0
    captured_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- ISP Outage Monitor Schemas (ported from old repo) ---

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
