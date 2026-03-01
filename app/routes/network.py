from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NetworkData
from app.schemas import NetworkSubmission, NetworkOut
from app.config import API_KEY

router = APIRouter(prefix="/network", tags=["Network Monitoring"])


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


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
def list_controllers(db: Session = Depends(get_db)):
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
