from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from db import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer, nullable=True)
    case_no = Column(String, unique=True, nullable=False, index=True)
    status = Column(String)
    face_image_path = Column(String, nullable=True)
    embedding_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, index=True)
    person_name = Column(String)
    similarity = Column(Float)
    location = Column(String, default="CCTV-01")
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanStats(Base):
    __tablename__ = "scan_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    total_scans = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)
    total_alerts = Column(Integer, default=0)

class CCTVCamera(Base):
    __tablename__ = "cctv_cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    stream_url = Column(String, nullable=False)
    enabled = Column(Integer, default=1)
    connected = Column(Integer, default=1)
    status = Column(String, default="offline")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
