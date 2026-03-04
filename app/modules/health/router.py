from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.modules.devices.models import Device
from app.modules.health.models import HealthData
from app.modules.health.schemas import HealthSubmission, HealthOut

router = APIRouter(prefix="/health", tags=["Health Monitoring"])


@router.post("/submit", status_code=201)
def submit_health(
    data: HealthSubmission,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    # Auto-register device if not exists (required by FK constraint)
    device = db.query(Device).filter(Device.machine_id == data.machine_id).first()
    if not device:
        device = Device(machine_id=data.machine_id, device_type="other")
        db.add(device)
        db.flush()

    record = HealthData(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"status": "success", "id": record.id}


@router.get("/latest/{machine_id}", response_model=HealthOut)
def get_latest_health(
    machine_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    record = (
        db.query(HealthData)
        .filter(HealthData.machine_id == machine_id)
        .order_by(HealthData.timestamp.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No health data found for this machine")
    return record


@router.get("/history/{machine_id}", response_model=list[HealthOut])
def get_health_history(
    machine_id: str,
    api_key: str = Depends(verify_api_key),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    records = (
        db.query(HealthData)
        .filter(HealthData.machine_id == machine_id)
        .order_by(HealthData.timestamp.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/machines")
def list_machines(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """List all known machine IDs with their latest health data."""
    from sqlalchemy import func, distinct

    machine_ids = db.query(distinct(HealthData.machine_id)).all()
    machines = []
    for (machine_id,) in machine_ids:
        latest = (
            db.query(HealthData)
            .filter(HealthData.machine_id == machine_id)
            .order_by(HealthData.timestamp.desc())
            .first()
        )
        machines.append({
            "machine_id": machine_id,
            "last_seen": latest.timestamp.isoformat(),
            "threat_score": latest.threat_score,
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
        })
    return machines
