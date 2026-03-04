from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


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
