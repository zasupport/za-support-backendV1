from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.modules.network.models import NetworkData
from app.modules.network.schemas import NetworkSubmission, NetworkOut

router = APIRouter(prefix="/network", tags=["Network Monitoring"])


@router.post("/submit", status_code=201)
def submit_network(
    data: NetworkSubmission,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    record = NetworkData(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"status": "success", "id": record.id}


@router.get("/latest/{controller_id}", response_model=NetworkOut)
def get_latest_network(
    controller_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    record = (
        db.query(NetworkData)
        .filter(NetworkData.controller_id == controller_id)
        .order_by(NetworkData.timestamp.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No network data found for this controller")
    return record


@router.get("/history/{controller_id}", response_model=list[NetworkOut])
def get_network_history(
    controller_id: str,
    api_key: str = Depends(verify_api_key),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    records = (
        db.query(NetworkData)
        .filter(NetworkData.controller_id == controller_id)
        .order_by(NetworkData.timestamp.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/controllers")
def list_controllers(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """List all known controller IDs with their latest network data."""
    from sqlalchemy import distinct

    controller_ids = db.query(distinct(NetworkData.controller_id)).all()
    controllers = []
    for (controller_id,) in controller_ids:
        latest = (
            db.query(NetworkData)
            .filter(NetworkData.controller_id == controller_id)
            .order_by(NetworkData.timestamp.desc())
            .first()
        )
        controllers.append({
            "controller_id": controller_id,
            "last_seen": latest.timestamp.isoformat(),
            "total_clients": latest.total_clients,
            "total_devices": latest.total_devices,
        })
    return controllers
