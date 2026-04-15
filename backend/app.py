from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import desc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create necessary directories
os.makedirs("faces", exist_ok=True)
os.makedirs("embeddings", exist_ok=True)

# Database setup
DATABASE_URL = "sqlite:///./surveillance.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
from db import Base, get_db

# Import models after Base is defined
from tables import Person, Alert, ScanStats

# Create tables from shared metadata
Base.metadata.create_all(bind=engine)

# Initialize stats
def init_stats(db: Session):
    stats = db.query(ScanStats).first()
    if not stats:
        stats = ScanStats(total_scans=0, total_matches=0, total_alerts=0)
        db.add(stats)
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = SessionLocal()
    init_stats(db)
    db.close()
    logger.info("Application started successfully")
    yield
    # Shutdown (if needed)
    pass

# FastAPI app
app = FastAPI(title="AI Surveillance Dashboard API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics
    Returns total persons, matches, alerts, and recent alerts
    """
    try:
        total_persons = db.query(func.count(Person.id)).scalar() or 0
        stats = db.query(ScanStats).first()
        
        total_matches = stats.total_matches if stats else 0
        total_alerts = stats.total_alerts if stats else 0
        total_scans = stats.total_scans if stats else 0
        
        # Get recent alerts
        recent_alerts = db.query(Alert).order_by(desc(Alert.created_at)).limit(5).all()
        
        logger.info(f"Stats requested: Persons={total_persons}, Matches={total_matches}, Alerts={total_alerts}")
        
        return {
            "total_persons": total_persons,
            "total_matches": total_matches,
            "total_alerts": total_alerts,
            "total_scans": total_scans,
            "recent_alerts": recent_alerts
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "AI Surveillance Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }

from routes import router as person_router
from cctv_routes import router as cctv_router

# Correct way to mount full FastAPI app
try:
    from face_recognition_system import api_server
    app.mount("/face", api_server.app)
    logger.info("Face recognition API mounted at /face")
except Exception as e:
    logger.error(f"Failed to load face recognition API: {e}")

# Include your normal routers
app.include_router(person_router)
app.include_router(cctv_router)