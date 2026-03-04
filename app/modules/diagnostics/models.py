from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Index

from app.core.database import Base


class WorkshopDiagnostic(Base):
    __tablename__ = "workshop_diagnostics"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    serial_number = Column(String(64), nullable=False, index=True)
    hostname = Column(String(256), nullable=True)
    client_id = Column(String(128), nullable=True, index=True)
    diagnostic_version = Column(String(16), nullable=True)
    mode = Column(String(16), nullable=True)

    # Hardware summary
    chip_type = Column(String(32), nullable=True)
    model_name = Column(String(128), nullable=True)
    model_identifier = Column(String(64), nullable=True)
    ram_gb = Column(Integer, nullable=True)
    ram_upgradeable = Column(String(128), nullable=True)
    cpu_name = Column(String(128), nullable=True)
    cores_physical = Column(Integer, nullable=True)
    cores_logical = Column(Integer, nullable=True)

    # macOS
    macos_version = Column(String(32), nullable=True)
    macos_build = Column(String(32), nullable=True)
    uptime_seconds = Column(Integer, nullable=True)

    # Security
    sip_enabled = Column(Boolean, nullable=True)
    filevault_on = Column(Boolean, nullable=True)
    firewall_on = Column(Boolean, nullable=True)
    gatekeeper_on = Column(Boolean, nullable=True)
    xprotect_version = Column(String(32), nullable=True)
    password_manager = Column(String(64), nullable=True)
    av_edr = Column(String(128), nullable=True)

    # Battery
    battery_health_pct = Column(Float, nullable=True)
    battery_cycles = Column(Integer, nullable=True)
    battery_design_capacity = Column(Integer, nullable=True)
    battery_max_capacity = Column(Integer, nullable=True)
    battery_condition = Column(String(32), nullable=True)

    # Storage
    disk_used_pct = Column(Integer, nullable=True)
    disk_free_gb = Column(Integer, nullable=True)

    # OCLP
    oclp_detected = Column(Boolean, default=False)
    oclp_version = Column(String(32), nullable=True)
    oclp_root_patched = Column(Boolean, default=False)
    third_party_kexts = Column(Integer, default=0)

    # Diagnostics summary
    kernel_panics = Column(Integer, default=0)
    total_processes = Column(Integer, nullable=True)

    # Intelligence engine output
    recommendations = Column(JSON, nullable=True)
    recommendation_count = Column(Integer, default=0)

    # Full payload
    raw_json = Column(JSON, nullable=True)
    runtime_seconds = Column(Integer, nullable=True)

    # Timestamps
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_diag_serial_captured", "serial_number", "captured_at"),
        Index("ix_diag_client_captured", "client_id", "captured_at"),
    )
