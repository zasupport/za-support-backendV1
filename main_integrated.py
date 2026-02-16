from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZA Support Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/zasupport")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class HealthData(Base):
    __tablename__ = "health_data"
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    battery_percent = Column(Float, nullable=True)
    threat_score = Column(Integer)
    raw_data = Column(JSON)

class NetworkData(Base):
    __tablename__ = "network_data"
    id = Column(Integer, primary_key=True, index=True)
    controller_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_clients = Column(Integer)
    total_devices = Column(Integer)
    raw_data = Column(JSON)

Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables created")

class HealthSubmission(BaseModel):
    machine_id: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: Optional[float] = None
    threat_score: int
    raw_data: dict

class NetworkSubmission(BaseModel):
    controller_id: str
    total_clients: int
    total_devices: int
    raw_data: dict

API_KEY = os.getenv("API_KEY", "demo_key")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ZA Support Backend"}

@app.get("/")
async def root():
    return {"message": "ZA Support Backend API", "status": "running"}

@app.post("/api/v1/health/submit")
async def submit_health(data: HealthSubmission, api_key: str = Header(..., alias="X-API-Key")):
    verify_api_key(api_key)
    db = SessionLocal()
    try:
        record = HealthData(**data.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"status": "success", "id": record.id}
    finally:
        db.close()

@app.post("/api/v1/network/submit")
async def submit_network(data: NetworkSubmission, api_key: str = Header(..., alias="X-API-Key")):
    verify_api_key(api_key)
    db = SessionLocal()
    try:
        record = NetworkData(**data.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"status": "success", "id": record.id}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 ZA SUPPORT BACKEND STARTING")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
