"""
ZA Support — Health Check v11 Agent API Router
Handles bidirectional communication with Health Check Agent v3.0
Persistent DB-backed storage for devices, collections, commands, and results.
Generated: 02/03/2026 10:30 SAST
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgentDevice, AgentCollection, AgentCommand, AgentCommandResult

SAST = timezone(timedelta(hours=2))
logger = logging.getLogger("agent_api")
router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


# ===================================================================
# Pydantic schemas
# ===================================================================

class HeartbeatRequest(BaseModel):
    serial: str
    model: str = ""
    hostname: str = ""
    os_version: str = ""
    agent_version: str = ""
    hardware_uuid: str = ""
    uptime_seconds: int = 0


class HeartbeatResponse(BaseModel):
    status: str = "ok"
    collection_interval: int = 300
    heartbeat_interval: int = 60
    command_poll_interval: int = 60
    pending_commands: int = 0
    server_time: str = ""
    message: str = ""


class CollectionData(BaseModel):
    agent_version: str = ""
    collection_type: str = "lite"
    timestamp: str = ""
    device: Dict[str, Any] = {}
    battery: Dict[str, Any] = {}
    storage: Dict[str, Any] = {}
    memory: Dict[str, Any] = {}
    cpu: Dict[str, Any] = {}
    security: Dict[str, Any] = {}
    network: Dict[str, Any] = {}
    errors: Dict[str, Any] = {}
    uptime_seconds: int = 0
    top_processes: List[Dict[str, Any]] = []
    hardware_profile: str = ""
    storage_detail: str = ""
    smart_full: str = ""
    installed_apps: str = ""
    login_items: str = ""
    launch_agents: str = ""
    launch_daemons: str = ""
    network_interfaces: str = ""
    open_ports: str = ""
    dns_config: str = ""
    usb_devices: str = ""
    bluetooth: str = ""
    printers: str = ""
    pending_updates: str = ""
    critical_errors_24h: str = ""


class CommandType(str, Enum):
    COLLECT_LITE = "collect_lite"
    COLLECT_FULL = "collect_full"
    GET_PROCESS_LIST = "get_process_list"
    GET_DISK_USAGE = "get_disk_usage"
    GET_NETWORK_INFO = "get_network_info"
    GET_BATTERY_DETAIL = "get_battery_detail"
    GET_SYSTEM_LOG = "get_system_log"
    GET_INSTALLED_APPS = "get_installed_apps"
    GET_SECURITY_STATUS = "get_security_status"
    GET_WIFI_DIAGNOSTICS = "get_wifi_diagnostics"
    GET_LOGIN_ITEMS = "get_login_items"
    GET_THERMAL_INFO = "get_thermal_info"
    RUN_SAFE_COMMAND = "run_safe_command"
    SET_COLLECTION_INTERVAL = "set_collection_interval"
    UPDATE_AGENT = "update_agent"
    GET_AGENT_STATUS = "get_agent_status"


class CreateCommandRequest(BaseModel):
    serial: str
    type: CommandType
    payload: str = ""


class CommandResponse(BaseModel):
    id: str
    type: str
    payload: str = ""
    created_at: str = ""


class CommandResultRequest(BaseModel):
    command_id: str
    serial: str
    status: str
    result: str = ""
    duration_seconds: int = 0
    timestamp: str = ""


class DeviceInfo(BaseModel):
    serial: str
    model: str
    hostname: str
    os_version: str
    agent_version: str
    hardware_uuid: str
    last_heartbeat: str
    last_collection: str
    online: bool
    collection_interval: int
    pending_commands: int
    latest_metrics: Dict[str, Any] = {}


# ===================================================================
# Helpers
# ===================================================================

def _now_sast() -> str:
    return datetime.now(SAST).strftime("%d/%m/%Y %H:%M:%S SAST")


def _now_sast_dt() -> datetime:
    return datetime.now(SAST)


def _is_online(device: AgentDevice, threshold_seconds: int = 180) -> bool:
    if not device.last_heartbeat:
        return False
    last = device.last_heartbeat
    if last.tzinfo is None:
        last = last.replace(tzinfo=SAST)
    return (datetime.now(SAST) - last).total_seconds() < threshold_seconds


def _format_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "never"
    return dt.strftime("%d/%m/%Y %H:%M SAST")


def _next_cmd_id() -> str:
    return f"cmd_{uuid.uuid4().hex[:10]}"


# ===================================================================
# Endpoints
# ===================================================================

@router.post("/heartbeat", response_model=HeartbeatResponse)
async def receive_heartbeat(req: HeartbeatRequest, db: Session = Depends(get_db)):
    now = _now_sast_dt()
    device = db.query(AgentDevice).filter(AgentDevice.serial == req.serial).first()

    if not device:
        device = AgentDevice(
            serial=req.serial, model=req.model, hostname=req.hostname,
            os_version=req.os_version, agent_version=req.agent_version,
            hardware_uuid=req.hardware_uuid, first_seen=now, last_heartbeat=now,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        logger.info(f"New device registered: {req.serial} ({req.model})")
    else:
        device.last_heartbeat = now
        device.model = req.model or device.model
        device.hostname = req.hostname or device.hostname
        device.os_version = req.os_version or device.os_version
        device.agent_version = req.agent_version or device.agent_version
        device.hardware_uuid = req.hardware_uuid or device.hardware_uuid
        db.commit()

    pending = db.query(AgentCommand).filter(
        AgentCommand.serial == req.serial, AgentCommand.dispatched == False
    ).count()

    return HeartbeatResponse(
        status="ok",
        collection_interval=device.collection_interval,
        heartbeat_interval=device.heartbeat_interval,
        command_poll_interval=device.command_poll_interval,
        pending_commands=pending,
        server_time=_now_sast(),
        message="",
    )


@router.post("/upload")
async def receive_collection(data: CollectionData, db: Session = Depends(get_db)):
    serial = data.device.get("serial", "unknown")
    device = db.query(AgentDevice).filter(AgentDevice.serial == serial).first()

    alerts = _analyse_collection(data)

    collection = AgentCollection(
        device_id=device.id if device else None,
        serial=serial,
        collection_type=data.collection_type,
        received_at=_now_sast_dt(),
        data=data.model_dump(),
        alerts=alerts,
    )
    db.add(collection)

    if device:
        device.last_collection = _now_sast_dt()

    db.commit()
    logger.info(f"Collection received: serial={serial} type={data.collection_type}")

    if alerts:
        logger.warning(f"Alerts for {serial}: {alerts}")

    return {"status": "ok", "received": _now_sast(), "alerts": alerts}


def _analyse_collection(data: CollectionData) -> List[Dict[str, str]]:
    alerts = []
    batt_pct = data.battery.get("percentage", 100)
    if isinstance(batt_pct, (int, float)) and batt_pct < 20:
        alerts.append({"severity": "high", "category": "battery", "message": f"Battery critically low: {batt_pct}%"})
    disk_pct = data.storage.get("used_pct", 0)
    if isinstance(disk_pct, (int, float)):
        if disk_pct > 90:
            alerts.append({"severity": "critical", "category": "storage", "message": f"Disk {disk_pct}% full"})
        elif disk_pct > 80:
            alerts.append({"severity": "high", "category": "storage", "message": f"Disk {disk_pct}% full"})
    mem_press = data.memory.get("pressure_pct", 0)
    if isinstance(mem_press, (int, float)) and mem_press > 80:
        alerts.append({"severity": "high", "category": "memory", "message": f"Memory pressure at {mem_press}%"})
    sec = data.security
    if sec:
        if "disabled" in str(sec.get("firewall", "")).lower():
            alerts.append({"severity": "critical", "category": "security", "message": "Firewall is DISABLED"})
        if "off" in str(sec.get("filevault", "")).lower():
            alerts.append({"severity": "high", "category": "security", "message": "FileVault encryption is OFF"})
    smart = data.storage.get("smart", "")
    if smart and "failing" in str(smart).lower():
        alerts.append({"severity": "critical", "category": "storage", "message": "SMART status indicates drive failure imminent"})
    return alerts


@router.get("/commands/{serial}", response_model=List[CommandResponse])
async def get_pending_commands(serial: str, db: Session = Depends(get_db)):
    pending = db.query(AgentCommand).filter(
        AgentCommand.serial == serial, AgentCommand.dispatched == False
    ).order_by(AgentCommand.created_at).all()

    if not pending:
        return []

    result = []
    for cmd in pending:
        result.append(CommandResponse(
            id=cmd.command_id, type=cmd.type,
            payload=cmd.payload or "", created_at=_format_dt(cmd.created_at),
        ))
        cmd.dispatched = True

    db.commit()
    logger.info(f"Dispatched {len(result)} commands to {serial}")
    return result


@router.post("/command-result")
async def receive_command_result(req: CommandResultRequest, db: Session = Depends(get_db)):
    cmd_result = AgentCommandResult(
        command_id=req.command_id, serial=req.serial, status=req.status,
        result=req.result, duration_seconds=req.duration_seconds,
        timestamp=req.timestamp, received_at=_now_sast_dt(),
    )
    db.add(cmd_result)
    db.commit()
    logger.info(f"Command result: id={req.command_id} serial={req.serial} status={req.status}")
    return {"status": "ok", "received": _now_sast()}


@router.post("/commands")
async def create_command(req: CreateCommandRequest, db: Session = Depends(get_db)):
    device = db.query(AgentDevice).filter(AgentDevice.serial == req.serial).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {req.serial} not found")

    cmd_id = _next_cmd_id()
    cmd = AgentCommand(
        command_id=cmd_id, device_id=device.id, serial=req.serial,
        type=req.type.value, payload=req.payload, created_at=_now_sast_dt(),
    )
    db.add(cmd)
    db.commit()
    logger.info(f"Command created: id={cmd_id} serial={req.serial} type={req.type.value}")
    return {"status": "queued", "command_id": cmd_id, "device_online": _is_online(device)}


@router.get("/devices", response_model=List[DeviceInfo])
async def list_devices(db: Session = Depends(get_db)):
    devices = db.query(AgentDevice).all()
    result = []
    for dev in devices:
        latest_coll = db.query(AgentCollection).filter(
            AgentCollection.serial == dev.serial
        ).order_by(AgentCollection.received_at.desc()).first()
        latest_metrics = latest_coll.data if latest_coll else {}
        pending = db.query(AgentCommand).filter(
            AgentCommand.serial == dev.serial, AgentCommand.dispatched == False
        ).count()

        result.append(DeviceInfo(
            serial=dev.serial, model=dev.model, hostname=dev.hostname,
            os_version=dev.os_version, agent_version=dev.agent_version,
            hardware_uuid=dev.hardware_uuid,
            last_heartbeat=_format_dt(dev.last_heartbeat),
            last_collection=_format_dt(dev.last_collection),
            online=_is_online(dev), collection_interval=dev.collection_interval,
            pending_commands=pending, latest_metrics=latest_metrics,
        ))
    return result


@router.get("/devices/{serial}", response_model=DeviceInfo)
async def get_device(serial: str, db: Session = Depends(get_db)):
    device = db.query(AgentDevice).filter(AgentDevice.serial == serial).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")

    latest_coll = db.query(AgentCollection).filter(
        AgentCollection.serial == serial
    ).order_by(AgentCollection.received_at.desc()).first()
    latest_metrics = latest_coll.data if latest_coll else {}
    pending = db.query(AgentCommand).filter(
        AgentCommand.serial == serial, AgentCommand.dispatched == False
    ).count()

    return DeviceInfo(
        serial=device.serial, model=device.model, hostname=device.hostname,
        os_version=device.os_version, agent_version=device.agent_version,
        hardware_uuid=device.hardware_uuid,
        last_heartbeat=_format_dt(device.last_heartbeat),
        last_collection=_format_dt(device.last_collection),
        online=_is_online(device), collection_interval=device.collection_interval,
        pending_commands=pending, latest_metrics=latest_metrics,
    )


@router.get("/devices/{serial}/collections")
async def get_device_collections(serial: str, limit: int = Query(default=50, le=288), db: Session = Depends(get_db)):
    device = db.query(AgentDevice).filter(AgentDevice.serial == serial).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")

    collections = db.query(AgentCollection).filter(
        AgentCollection.serial == serial
    ).order_by(AgentCollection.received_at.desc()).limit(limit).all()

    collections.reverse()  # oldest first
    return {
        "serial": serial,
        "count": len(collections),
        "collections": [c.data for c in collections],
    }


@router.get("/devices/{serial}/command-results")
async def get_device_command_results(serial: str, db: Session = Depends(get_db)):
    results = db.query(AgentCommandResult).filter(
        AgentCommandResult.serial == serial
    ).order_by(AgentCommandResult.received_at.desc()).all()

    return {
        "serial": serial,
        "results": [
            {
                "command_id": r.command_id, "serial": r.serial, "status": r.status,
                "result": r.result, "duration_seconds": r.duration_seconds,
                "timestamp": r.timestamp, "received_at": _format_dt(r.received_at),
            }
            for r in results
        ],
    }


@router.post("/devices/{serial}/config")
async def update_device_config(serial: str, config: Dict[str, int], db: Session = Depends(get_db)):
    device = db.query(AgentDevice).filter(AgentDevice.serial == serial).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")

    if "collection_interval" in config:
        if config["collection_interval"] < 60:
            raise HTTPException(status_code=400, detail="Minimum collection interval is 60 seconds")
        device.collection_interval = config["collection_interval"]
    if "heartbeat_interval" in config:
        if config["heartbeat_interval"] < 30:
            raise HTTPException(status_code=400, detail="Minimum heartbeat interval is 30 seconds")
        device.heartbeat_interval = config["heartbeat_interval"]
    if "command_poll_interval" in config:
        device.command_poll_interval = config["command_poll_interval"]

    db.commit()
    logger.info(f"Config updated for {serial}: ci={device.collection_interval} hi={device.heartbeat_interval}")
    return {
        "status": "ok",
        "config": {
            "collection_interval": device.collection_interval,
            "heartbeat_interval": device.heartbeat_interval,
            "command_poll_interval": device.command_poll_interval,
        },
        "effective": "next heartbeat",
    }


@router.get("/status")
async def agent_api_status(db: Session = Depends(get_db)):
    devices = db.query(AgentDevice).all()
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if _is_online(d))
    total_collections = db.query(AgentCollection).count()
    total_commands_pending = db.query(AgentCommand).filter(AgentCommand.dispatched == False).count()
    total_results = db.query(AgentCommandResult).count()
    return {
        "status": "ok",
        "server_time": _now_sast(),
        "stats": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "total_collections_stored": total_collections,
            "pending_commands": total_commands_pending,
            "completed_commands": total_results,
        },
    }
