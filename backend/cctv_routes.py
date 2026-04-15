from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
import uuid
import logging
import threading
import time
import io
from datetime import datetime, timedelta
from typing import Optional, List

import cv2
import numpy as np

from db import get_db, SessionLocal
from tables import Person, Alert, ScanStats, CCTVCamera
from models import ScanResult, CCTVConfigCreate, CCTVConfigResponse
from face_recognition_utils import crop_face, generate_embedding, find_match

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cctv"])

ALERT_THRESHOLD = float(os.getenv('ALERT_THRESHOLD', '0.65'))
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))


class CameraManager:
    def __init__(self):
        self.registry = {}
        self.lock = threading.Lock()
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def _parse_stream_source(self, stream_url: str):
        if stream_url.isdigit():
            return int(stream_url)
        return stream_url

    def _detect_faces(self, frame: np.ndarray):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return [tuple(face) for face in faces] if faces is not None else []

    def _embed_face(self, face_frame: np.ndarray):
        temp_path = f"temp_live_face_{uuid.uuid4()}.jpg"
        cv2.imwrite(temp_path, face_frame)
        embedding = generate_embedding(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return embedding

    def _load_all_embeddings(self):
        with SessionLocal() as session:
            persons = session.query(Person).all()
            return {p.id: p.embedding_path for p in persons}

    def _annotate_frame(self, frame: np.ndarray):
        faces = self._detect_faces(frame)
        embeddings = self._load_all_embeddings()

        for face_coords in faces:
            x, y, w, h = face_coords
            face_crop = frame[y:y + h, x:x + w]
            embedding = self._embed_face(face_crop)
            label = 'Unknown'
            if embedding is not None and embeddings:
                matched_person_id, similarity = find_match(embedding, embeddings, SIMILARITY_THRESHOLD)
                if matched_person_id:
                    with SessionLocal() as session:
                        matched_person = session.query(Person).filter(Person.id == matched_person_id).first()
                        if matched_person:
                            label = f"{matched_person.name} ({round(similarity * 100)}%)"
                        else:
                            label = f"Unknown ({round(similarity * 100)}%)"
                else:
                    label = 'No match'
            else:
                label = 'No faces'

            cv2.rectangle(frame, (x, y), (x + w, y + h), (16, 185, 129), 2)
            cv2.putText(
                frame,
                label,
                (x, max(y - 10, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return frame

    def add_or_update(self, camera: CCTVCamera):
        with self.lock:
            entry = self.registry.get(camera.id)
            if entry:
                entry.update({
                    'name': camera.name,
                    'location': camera.location,
                    'stream_url': camera.stream_url,
                    'enabled': bool(camera.enabled),
                    'connected': bool(camera.connected),
                    'last_seen': camera.last_seen,
                    'status': camera.status or 'offline'
                })
            else:
                self.registry[camera.id] = {
                    'name': camera.name,
                    'location': camera.location,
                    'stream_url': camera.stream_url,
                    'enabled': bool(camera.enabled),
                    'connected': bool(camera.connected),
                    'frame': None,
                    'capture': None,
                    'thread': None,
                    'status': camera.status or 'offline',
                    'last_seen': camera.last_seen,
                    'last_db_update': time.time()
                }

    def update_state(self, camera_id: int, *, enabled: Optional[bool] = None, connected: Optional[bool] = None):
        with self.lock:
            camera = self.registry.get(camera_id)
            if not camera:
                return
            if enabled is not None:
                camera['enabled'] = enabled
            if connected is not None:
                camera['connected'] = connected
            if not camera['enabled'] or not camera['connected']:
                camera['status'] = 'offline'
                self._release_camera(camera_id)

    def _release_camera(self, camera_id: int):
        camera = self.registry.get(camera_id)
        if camera and camera.get('capture') is not None:
            try:
                camera['capture'].release()
            except Exception:
                pass
            camera['capture'] = None
        if camera:
            camera['thread'] = None
            camera['frame'] = None

    def start_stream(self, camera: CCTVCamera):
        self.add_or_update(camera)
        with self.lock:
            camera_state = self.registry.get(camera.id)
            if not camera_state or not camera_state['enabled'] or not camera_state['connected']:
                return
            if camera_state['thread'] and camera_state['thread'].is_alive():
                return

            def capture_loop():
                while True:
                    with self.lock:
                        current = self.registry.get(camera.id)
                        if not current or not current['enabled'] or not current['connected']:
                            break
                        stream_url = current['stream_url']
                        capture = current.get('capture')

                    if capture is None or not capture.isOpened():
                        source = self._parse_stream_source(stream_url)
                        capture = cv2.VideoCapture(source)
                        with self.lock:
                            if not capture.isOpened():
                                self.registry[camera.id]['status'] = 'offline'
                                time.sleep(2)
                                continue
                            self.registry[camera.id]['capture'] = capture
                            self.registry[camera.id]['status'] = 'streaming'

                    ret, frame = capture.read()
                    if not ret or frame is None:
                        with self.lock:
                            self.registry[camera.id]['status'] = 'offline'
                        time.sleep(1)
                        continue

                    try:
                        processed = self._annotate_frame(frame)
                        _, buffer = cv2.imencode('.jpg', processed)
                        if buffer is not None:
                            with self.lock:
                                self.registry[camera.id]['frame'] = buffer.tobytes()
                                self.registry[camera.id]['last_seen'] = datetime.utcnow()
                                self.registry[camera.id]['status'] = 'streaming'
                    except Exception as exc:
                        logger.warning(f"Error processing video frame for camera {camera.id}: {exc}")

                    time.sleep(0.05)

                self._release_camera(camera.id)

            thread = threading.Thread(target=capture_loop, daemon=True)
            self.registry[camera.id]['thread'] = thread
            thread.start()

    def stop_stream(self, camera_id: int):
        with self.lock:
            camera = self.registry.get(camera_id)
            if camera:
                camera['enabled'] = False
                camera['status'] = 'offline'
                self._release_camera(camera_id)

    def get_camera_state(self, camera_id: int):
        with self.lock:
            camera = self.registry.get(camera_id)
            if not camera:
                return None
            return {
                'status': camera.get('status', 'offline'),
                'last_seen': camera.get('last_seen')
            }

    def frame_generator(self, camera_id: int):
        boundary = b"--frame\r\n"
        while True:
            with self.lock:
                camera = self.registry.get(camera_id)
                if not camera or not camera['enabled'] or not camera['connected']:
                    break
                frame_bytes = camera.get('frame')
                status = camera.get('status', 'offline')

            if frame_bytes:
                yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            else:
                if status == 'offline':
                    time.sleep(0.5)
                else:
                    time.sleep(0.1)

    def get_status(self, camera: CCTVCamera):
        state = self.get_camera_state(camera.id)
        now = datetime.utcnow()
        if not camera.connected:
            return 'disconnected', None
        if not camera.enabled:
            return 'stopped', None
        if state and state['last_seen'] and (now - state['last_seen']) < timedelta(seconds=5):
            return state['status'], state['last_seen']
        return 'offline', state['last_seen'] if state else None


camera_manager = CameraManager()


def _camera_response(camera: CCTVCamera):
    status, last_seen = camera_manager.get_status(camera)
    return {
        'id': camera.id,
        'name': camera.name,
        'location': camera.location,
        'stream_url': camera.stream_url,
        'enabled': bool(camera.enabled),
        'connected': bool(camera.connected),
        'status': status,
        'last_seen': last_seen,
        'created_at': camera.created_at,
        'updated_at': camera.updated_at
    }


@router.get("/cctv", response_model=List[CCTVConfigResponse])
def list_cctv(db: Session = Depends(get_db)):
    cameras = db.query(CCTVCamera).order_by(desc(CCTVCamera.created_at)).all()
    return [_camera_response(camera) for camera in cameras]


@router.post("/connect-cctv", response_model=CCTVConfigResponse)
def connect_cctv(camera: CCTVConfigCreate, db: Session = Depends(get_db)):
    existing = db.query(CCTVCamera).filter(CCTVCamera.stream_url == camera.stream_url).first()
    if existing:
        existing.name = camera.name
        existing.location = camera.location
        existing.enabled = True
        existing.connected = True
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        camera_manager.add_or_update(existing)
        camera_manager.start_stream(existing)
        return _camera_response(existing)

    new_camera = CCTVCamera(
        name=camera.name,
        location=camera.location,
        stream_url=camera.stream_url,
        enabled=1,
        connected=1,
        status='offline',
        last_seen=None
    )
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    camera_manager.add_or_update(new_camera)
    camera_manager.start_stream(new_camera)
    return _camera_response(new_camera)


@router.patch("/cctv/{camera_id}", response_model=CCTVConfigResponse)
def update_cctv(
    camera_id: int,
    enabled: Optional[bool] = None,
    connected: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    camera = db.query(CCTVCamera).filter(CCTVCamera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="CCTV camera not found")

    if enabled is not None:
        camera.enabled = 1 if enabled else 0
    if connected is not None:
        camera.connected = 1 if connected else 0
    camera.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(camera)
    camera_manager.add_or_update(camera)
    if camera.enabled and camera.connected:
        camera_manager.start_stream(camera)
    else:
        camera_manager.stop_stream(camera.id)
    return _camera_response(camera)


@router.delete("/cctv/{camera_id}")
def delete_cctv(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(CCTVCamera).filter(CCTVCamera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="CCTV camera not found")
    camera_manager.stop_stream(camera.id)
    db.delete(camera)
    db.commit()
    return {"message": "CCTV camera disconnected successfully", "id": camera_id}


@router.get("/video-feed/{camera_id}")
def video_feed(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(CCTVCamera).filter(CCTVCamera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="CCTV camera not found")
    if not camera.enabled or not camera.connected:
        raise HTTPException(status_code=400, detail="Camera must be connected and enabled to stream")

    camera_manager.add_or_update(camera)
    camera_manager.start_stream(camera)
    return StreamingResponse(camera_manager.frame_generator(camera_id), media_type='multipart/x-mixed-replace; boundary=frame')
