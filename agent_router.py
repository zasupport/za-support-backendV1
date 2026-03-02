"""
ZA Support — Health Check v11 Agent API Router
Handles bidirectional communication with Health Check Agent v3.0
Generated: 02/03/2026 10:30 SAST
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import logging
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
SAST = timezone(timedelta(hours=2))
logger = logging.getLogger("agent_api")
router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
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
_devices: Dict[str, Dict[str, Any]] = {}
_collections: Dict[str, List[Dict]] = {}
_commands: Dict[str, List[Dict]] = {}
_command_results: Dict[str, Dict] = {}
_device_config: Dict[str, Dict[str, int]] = {}
DEFAULT_CONFIG = {
    "collection_interval": 300,
    "heartbeat_interval": 60,
    "command_poll_interval": 60,
}
_cmd_counter = 0
def _next_cmd_id() -> str:
    global _cmd_counter
    _cmd_counter += 1
    return f"cmd_{_cmd_counter:06d}"
def _now_sast() -> str:
    return datetime.now(SAST).strftime("%d/%m/%Y %H:%M:%S SAST")
def _is_online(serial: str, threshold_seconds: int = 180) -> bool:
    device = _devices.get(serial)
    if not device:
        return False
    last_hb = device.get("last_heartbeat_ts")
    if not last_hb:
        return False
    return (datetime.now(SAST) - last_hb).total_seconds() < threshold_seconds
@router.post("/heartbeat", response_model=HeartbeatResponse)
async def receive_heartbeat(req: HeartbeatRequest):
    now = datetime.now(SAST)
    if req.serial not in _devices:
        _devices[req.serial] = {
            "serial": req.serial, "model": req.model, "hostname": req.hostname,
            "os_version": req.os_version, "agent_version": req.agent_version,
            "hardware_uuid": req.hardware_uuid, "first_seen": now,
            "last_heartbeat_ts": now, "last_collection_ts": None,
        }
        logger.info(f"New device registered: {req.serial} ({req.model})")
    else:
        device = _devices[req.serial]
        device["last_heartbeat_ts"] = now
        device["model"] = req.model or device["model"]
        device["hostname"] = req.hostname or device["hostname"]
        device["os_version"] = req.os_version or device["os_version"]
        device["agent_version"] = req.agent_version or device["agent_version"]
        device["hardware_uuid"] = req.hardware_uuid or device["hardware_uuid"]
    config = _device_config.get(req.serial, DEFAULT_CONFIG)
    pending = len(_commands.get(req.serial, []))
    return HeartbeatResponse(
        status="ok", collection_interval=config.get("collection_interval", 300),
        heartbeat_interval=config.get("heartbeat_interval", 60),
        command_poll_interval=config.get("command_poll_interval", 60),
        pending_commands=pending, server_time=_now_sast(), message="",
    )
@router.post("/upload")
async def receive_collection(data: CollectionData):
    serial = data.device.get("serial", "unknown")
    if serial not in _collections:
        _collections[serial] = []
    _collections[serial].append({"received_at": _now_sast(), "received_ts": datetime.now(SAST), "data": data.dict()})
    if len(_collections[serial]) > 288:
        _collections[serial] = _collections[serial][-288:]
    if serial in _devices:
        _devices[serial]["last_collection_ts"] = datetime.now(SAST)
    logger.info(f"Collection received: serial={serial} type={data.collection_type}")
    alerts = _analyse_collection(data)
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
async def get_pending_commands(serial: str):
    pending = _commands.get(serial, [])
    if not pending:
        return []
    result = [CommandResponse(id=cmd["id"], type=cmd["type"], payload=cmd.get("payload", ""), created_at=cmd.get("created_at", "")) for cmd in pending]
    _commands[serial] = []
    logger.info(f"Dispatched {len(result)} commands to {serial}")
    return result
@router.post("/command-result")
async def receive_command_result(req: CommandResultRequest):
    _command_results[req.command_id] = {
        "command_id": req.command_id, "serial": req.serial, "status": req.status,
        "result": req.result, "duration_seconds": req.duration_seconds,
        "timestamp": req.timestamp, "received_at": _now_sast(),
    }
    logger.info(f"Command result: id={req.command_id} serial={req.serial} status={req.status}")
    return {"status": "ok", "received": _now_sast()}
@router.post("/commands")
async def create_command(req: CreateCommandRequest):
    if req.serial not in _devices:
        raise HTTPException(status_code=404, detail=f"Device {req.serial} not found")
    cmd_id = _next_cmd_id()
    cmd = {"id": cmd_id, "type": req.type.value, "payload": req.payload, "created_at": _now_sast()}
    if req.serial not in _commands:
        _commands[req.serial] = []
    _commands[req.serial].append(cmd)
    logger.info(f"Command created: id={cmd_id} serial={req.serial} type={req.type.value}")
    return {"status": "queued", "command_id": cmd_id, "device_online": _is_online(req.serial)}
@router.get("/devices", response_model=List[DeviceInfo])
async def list_devices():
    result = []
    for serial, dev in _devices.items():
        collections = _collections.get(serial, [])
        latest = collections[-1]["data"] if collections else {}
        config = _device_config.get(serial, DEFAULT_CONFIG)
        result.append(DeviceInfo(
            serial=serial, model=dev.get("model", ""), hostname=dev.get("hostname", ""),
            os_version=dev.get("os_version", ""), agent_version=dev.get("agent_version", ""),
            hardware_uuid=dev.get("hardware_uuid", ""),
            last_heartbeat=dev["last_heartbeat_ts"].strftime("%d/%m/%Y %H:%M SAST") if dev.get("last_heartbeat_ts") else "never",
            last_collection=dev["last_collection_ts"].strftime("%d/%m/%Y %H:%M SAST") if dev.get("last_collection_ts") else "never",
            online=_is_online(serial), collection_interval=config.get("collection_interval", 300),
            pending_commands=len(_commands.get(serial, [])), latest_metrics=latest,
        ))
    return result
@router.get("/devices/{serial}", response_model=DeviceInfo)
async def get_device(serial: str):
    if serial not in _devices:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    dev = _devices[serial]
    collections = _collections.get(serial, [])
    latest = collections[-1]["data"] if collections else {}
    config = _device_config.get(serial, DEFAULT_CONFIG)
    return DeviceInfo(
        serial=serial, model=dev.get("model", ""), hostname=dev.get("hostname", ""),
        os_version=dev.get("os_version", ""), agent_version=dev.get("agent_version", ""),
        hardware_uuid=dev.get("hardware_uuid", ""),
        last_heartbeat=dev["last_heartbeat_ts"].strftime("%d/%m/%Y %H:%M SAST") if dev.get("last_heartbeat_ts") else "never",
        last_collection=dev["last_collection_ts"].strftime("%d/%m/%Y %H:%M SAST") if dev.get("last_collection_ts") else "never",
        online=_is_online(serial), collection_interval=config.get("collection_interval", 300),
        pending_commands=len(_commands.get(serial, [])), latest_metrics=latest,
    )
@router.get("/devices/{serial}/collections")
async def get_device_collections(serial: str, limit: int = Query(default=50, le=288)):
    if serial not in _devices:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    collections = _collections.get(serial, [])
    return {"serial": serial, "count": len(collections[-limit:]), "collections": [c["data"] for c in collections[-limit:]]}
@router.get("/devices/{serial}/command-results")
async def get_device_command_results(serial: str):
    results = {k: v for k, v in _command_results.items() if v.get("serial") == serial}
    return {"serial": serial, "results": list(results.values())}
@router.post("/devices/{serial}/config")
async def update_device_config(serial: str, config: Dict[str, int]):
    if serial not in _devices:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    current = _device_config.get(serial, dict(DEFAULT_CONFIG))
    if "collection_interval" in config:
        if config["collection_interval"] < 60:
            raise HTTPException(status_code=400, detail="Minimum collection interval is 60 seconds")
        current["collection_interval"] = config["collection_interval"]
    if "heartbeat_interval" in config:
        if config["heartbeat_interval"] < 30:
            raise HTTPException(status_code=400, detail="Minimum heartbeat interval is 30 seconds")
        current["heartbeat_interval"] = config["heartbeat_interval"]
    if "command_poll_interval" in config:
        current["command_poll_interval"] = config["command_poll_interval"]
    _device_config[serial] = current
    logger.info(f"Config updated for {serial}: {current}")
    return {"status": "ok", "config": current, "effective": "next heartbeat"}
@router.get("/status")
async def agent_api_status():
    total_devices = len(_devices)
    online_devices = sum(1 for s in _devices if _is_online(s))
    total_collections = sum(len(c) for c in _collections.values())
    total_commands_pending = sum(len(c) for c in _commands.values())
    total_results = len(_command_results)
    return {
        "status": "ok", "server_time": _now_sast(),
        "stats": {
            "total_devices": total_devices, "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "total_collections_stored": total_collections,
            "pending_commands": total_commands_pending, "completed_commands": total_results,
        },
    }
