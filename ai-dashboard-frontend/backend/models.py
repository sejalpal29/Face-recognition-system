from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Person's name")
    age: Optional[int] = Field(None, ge=0, le=150, description="Person's age")
    case_no: str = Field(..., min_length=1, description="Unique case number")
    status: str = Field(default="missing", description="Status: missing, wanted, found, registered")

class PersonResponse(BaseModel):
    id: int
    name: str
    age: Optional[int]
    case_no: str
    status: str
    face_image_path: Optional[str]
    embedding_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FaceMatch(BaseModel):
    person_id: Optional[int] = None
    name: Optional[str] = None
    similarity: float
    confidence: str  # "high", "medium", "low", "unknown"

class ScanResult(BaseModel):
    match: bool
    name: Optional[str] = None
    person_id: Optional[int] = None
    similarity: Optional[float] = None
    alert: bool = False
    location: str = "CCTV-01"
    timestamp: datetime
    faces_detected: int = 0
    matches: list[FaceMatch] = []

class AlertResponse(BaseModel):
    id: int
    person_id: int
    person_name: str
    similarity: float
    location: str
    created_at: datetime

class CCTVConfigCreate(BaseModel):
    name: str
    location: str
    stream_url: str

class CCTVConfigResponse(BaseModel):
    id: int
    name: str
    location: str
    stream_url: str
    enabled: bool
    connected: bool
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_persons: int
    total_matches: int
    total_alerts: int
    total_scans: int
    recent_alerts: list[AlertResponse]
