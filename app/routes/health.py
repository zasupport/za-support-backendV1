from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import HealthData, Device
from app.schemas import HealthSubmission, HealthOut
from app.config import API_KEY

router = APIRouter(prefix="/health", tags=["Health Monitoring"])


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


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
def list_machines(db: Session = Depends(get_db)):
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
