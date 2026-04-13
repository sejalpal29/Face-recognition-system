"""
Face Recognition API Server (FastAPI)

Provides REST API endpoints for:
1. Face registration
2. Face matching
3. Person management
4. Face database operations

This server uses FastAPI for high-performance async operations and automatic API documentation.

Author: Face Recognition System
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import base64
import os
import logging
import io
from PIL import Image
import json
import torch

try:
    # Package import when running as part of the face_recognition_system package
    from .preprocessing import ImagePreprocessor
    from .face_detection import MultiScaleFaceDetector, extract_face_regions, deduplicate_detections
    from .cnn_architecture import FaceEmbeddingCNN
    from .embedding_storage import FaceEmbeddingDatabase, EmbeddingGenerator, FaceRegistrationManager
    from .face_matching import FaceMatcher, SimilarityMetrics
except ImportError:
    # Direct module import fallback when running api_server.py directly
    from preprocessing import ImagePreprocessor
    from face_detection import MultiScaleFaceDetector, extract_face_regions, deduplicate_detections
    from cnn_architecture import FaceEmbeddingCNN
    from embedding_storage import FaceEmbeddingDatabase, EmbeddingGenerator, FaceRegistrationManager
    from face_matching import FaceMatcher, SimilarityMetrics

import uuid

try:
    from facenet_pytorch import InceptionResnetV1
    FACENET_PYTORCH_AVAILABLE = True
except ImportError:
    InceptionResnetV1 = None
    FACENET_PYTORCH_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Face Recognition API",
    description="Complete face recognition system with registration, matching, and management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
device = "cuda" if torch.cuda.is_available() else "cpu"
model = None
preprocessor = None
detector = None
database = None
embedding_generator = None
registration_manager = None
matcher = None
expected_embedding_dim = None

# ===================== Pydantic Models =====================

class RegisterFaceRequest(BaseModel):
    """Request model for face registration."""
    name: str
    image_base64: str
    status: str = "registered"
    metadata: Optional[Dict] = {}

class MatchFaceRequest(BaseModel):
    """Request model for face matching."""
    image_base64: str
    top_k: int = 5

class CompareFacesRequest(BaseModel):
    """Request model for comparing two faces."""
    image1_base64: str
    image2_base64: str

class UpdatePersonStatusRequest(BaseModel):
    """Request model for updating person status."""
    status: str

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    device: str
    model_initialized: bool

class RegisterFaceResponse(BaseModel):
    """Response model for face registration."""
    success: bool
    person_id: int
    face_id: int
    message: str

class PersonMatch(BaseModel):
    """Model for a single person match."""
    person_id: int
    name: str
    distance: float
    confidence: float
    status: str

class FaceDetectionResult(BaseModel):
    """Model for a detected face and its matches."""
    face_index: int
    detection_bbox: List[int]
    matches: List[Dict]

class MatchFaceResponse(BaseModel):
    """Response model for face matching."""
    success: bool
    num_faces_detected: int
    matches: List[Dict]

# ===================== Initialization =====================

def initialize_components():
    """Initialize all face recognition components."""
    global model, preprocessor, detector, database, embedding_generator, registration_manager, matcher, expected_embedding_dim
    
    logger.info("[v0] Initializing face recognition components...")
    
    try:
        # Initialize preprocessor
        preprocessor = ImagePreprocessor(target_size=(160, 160))
        logger.info("[v0] Preprocessor initialized")
        
        # Initialize detector
        detector = MultiScaleFaceDetector()
        logger.info("[v0] Face detector initialized")
        
        # Initialize database with absolute path
        db_dir = os.path.dirname(__file__)
        db_path = os.path.join(db_dir, "face_recognition.db")
        database = FaceEmbeddingDatabase(db_path)
        logger.info(f"[v0] Database initialized at {db_path}")

        # Check existing stored embedding dimensions for compatibility
        existing_dims = database.get_embedding_dimension_counts()
        use_pretrained_facenet = FACENET_PYTORCH_AVAILABLE

        if existing_dims:
            if len(existing_dims) == 1:
                existing_dim = next(iter(existing_dims))
                if existing_dim == 128:
                    use_pretrained_facenet = False
                    logger.info("[v0] Existing DB embeddings are 128-D; using custom 128-D model for compatibility.")
                elif existing_dim == 512:
                    if FACENET_PYTORCH_AVAILABLE:
                        use_pretrained_facenet = True
                        logger.info("[v0] Existing DB embeddings are 512-D; using pretrained facenet model.")
                    else:
                        use_pretrained_facenet = False
                        logger.warning("[v0] Existing DB embeddings are 512-D, but facenet-pytorch is unavailable. Using custom 128-D model; 512-D entries will be ignored during matching.")
                else:
                    use_pretrained_facenet = False
                    logger.warning(f"[v0] Existing DB embeddings use unsupported dimension {existing_dim}. Defaulting to custom 128-D model.")
            else:
                use_pretrained_facenet = False
                logger.warning(f"[v0] Mixed embedding dimensions found in DB: {existing_dims}. Defaulting to custom 128-D model and filtering by expected dimension.")
        else:
            logger.info("[v0] No embeddings in database yet; selecting model based on installed libraries.")

        # Initialize model (load pretrained face recognition model when available)
        model_path = "face_embedding_model.pth"

        if use_pretrained_facenet:
            try:
                model = InceptionResnetV1(pretrained='vggface2', classify=False).eval()
                logger.info("[v0] Loaded facenet-pytorch InceptionResnetV1 pretrained on vggface2")
            except Exception as e:
                logger.warning(f"[v0] Failed to initialize facenet-pytorch pretrained model: {e}")
                use_pretrained_facenet = False
                model = FaceEmbeddingCNN(embedding_dim=128)

        if not use_pretrained_facenet:
            model = FaceEmbeddingCNN(embedding_dim=128)
            if os.path.exists(model_path):
                model.load_state_dict(torch.load(model_path, map_location=device))
                logger.info(f"[v0] Loaded custom face embedding model from {model_path}")
            else:
                logger.warning(f"[v0] Pre-trained custom model not found at {model_path}. Using untrained custom CNN.")

        model = model.to(device)
        model.eval()
        expected_embedding_dim = 512 if use_pretrained_facenet else 128
        logger.info(f"[v0] Model moved to device: {device} with expected embedding dim: {expected_embedding_dim}")
        
        # Initialize embedding generator
        embedding_generator = EmbeddingGenerator(
            model,
            device=device,
            normalize_input=use_pretrained_facenet
        )
        logger.info("[v0] Embedding generator initialized")
        
        # Initialize registration manager
        registration_manager = FaceRegistrationManager(
            database,
            embedding_generator,
            preprocessor
        )
        logger.info("[v0] Registration manager initialized")
        
        # Initialize matcher
        matcher = FaceMatcher(distance_metric="euclidean", threshold=3.0)
        logger.info("[v0] Face matcher initialized")
        
        logger.info("[v0] All components initialized successfully!")
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[v0] Error initializing components: {str(e)}\n{error_trace}")
        raise

# Global flag to track initialization
_initialized = False

def ensure_initialized():
    """Lazy initialization - load components only when needed"""
    global model, preprocessor, detector, database, embedding_generator, registration_manager, matcher, _initialized
    
    if _initialized:
        return
    
    logger.info("[v0] Lazy loading components on first request...")
    initialize_components()
    _initialized = True

@app.on_event("startup")
async def startup_event():
    """App startup - components will load on first request"""
    logger.info("[v0] FastAPI startup - components will lazy-load on first request")

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    ensure_initialized()  # Load if not already loaded
    return {
        "status": "healthy",
        "device": device,
        "model_initialized": model is not None
    }

# ===================== Helper Functions =====================

def decode_base64_image(image_base64: str) -> Optional[np.ndarray]:
    """Decode base64 string to OpenCV image."""
    try:
        image_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        logger.error(f"[v0] Error decoding base64 image: {str(e)}")
        return None

def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    
    Args:
        obj: Object to convert (can be dict, list, or scalar)
        
    Returns:
        Object with all numpy types converted to Python types
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# ===================== API Endpoints =====================

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthCheckResponse: System status and initialization state
    """
    return {
        "status": "healthy",
        "device": device,
        "model_initialized": model is not None
    }

@app.post("/api/register")
def register_face(request: RegisterFaceRequest):
    """
    Register a new face in the database.
    
    Args:
        request: RegisterFaceRequest containing name and base64-encoded image
        
    Returns:
        RegisterFaceResponse with person_id, face_id, and success status
        
    Raises:
        HTTPException: If face detection fails or input is invalid
    """
    try:
        try:
            ensure_initialized()
            logger.info("[v0] Components initialized")

            name = request.name
            image_base64 = request.image_base64
            status = request.status
            metadata = request.metadata or {}
            logger.info(f"[v0] Registration request for: {name}")
            
            if not name or not image_base64:
                raise HTTPException(status_code=400, detail="Missing name or image")
            
            # Decode image
            logger.info("[v0] Decoding image...")
            image = decode_base64_image(image_base64)
            if image is None:
                raise HTTPException(status_code=400, detail="Invalid image")
            logger.info(f"[v0] Image decoded: shape={image.shape}")
            
            # Detect faces
            logger.info("[v0] Detecting faces...")
            detections = detector.detect_faces(image)
            logger.info(f"[v0] Detected {len(detections)} faces")

            detections = [
                det for det in detections
                if det.get("confidence", 0.0) >= 0.6
                and det["width"] >= 40
                and det["height"] >= 40
            ]
            detections = deduplicate_detections(detections, iou_threshold=0.45)
            logger.info(f"[v0] Face detections after confidence/size filtering and deduplication: {len(detections)}")

            if len(detections) == 0:
                raise HTTPException(status_code=400, detail="No face detected in image")

            if len(detections) > 1:
                sorted_by_area = sorted(detections, key=lambda d: d['width'] * d['height'], reverse=True)
                largest = sorted_by_area[0]
                logger.warning("[v0] Multiple detections found; selecting the largest detected face for registration")
                detections = [largest]

            # Extract face
            logger.info("[v0] Extracting face region...")
            faces = extract_face_regions(image, detections)
            face_image = faces[0]
            logger.info(f"[v0] Face extracted: shape={face_image.shape}")

            # Generate a unique filename for the stored face image
            image_filename = f"face_{uuid.uuid4().hex}.jpg"
            faces_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "faces"))
            os.makedirs(faces_dir, exist_ok=True)
            image_path = os.path.join(faces_dir, image_filename)
            relative_path = os.path.relpath(image_path, os.path.dirname(__file__))
            logger.info(f"[v0] Image filename: {image_path} (relative: {relative_path})")

            # Register face (registration_manager will create person/face ids)
            logger.info("[v0] Calling registration_manager.register_face()...")
            person_id, face_id, embedding = registration_manager.register_face(
                name,
                face_image,
                relative_path,
                status,
                metadata
            )
            logger.info(f"[v0] Registration returned: person_id={person_id}, face_id={face_id}, embedding_shape={embedding.shape if embedding is not None else None}")
            
            # Check if embedding generation failed
            if face_id is None:
                raise HTTPException(status_code=500, detail="Failed to process face image")
            
            if embedding is None:
                logger.warning(f"[v0] Warning: No embedding generated for {name}, but registration succeeded (person_id: {person_id}, face_id: {face_id})")
            
            logger.info(f"[v0] Successfully registered face for {name}")
            
            response = {
                "success": True,
                "person_id": person_id,
                "face_id": face_id,
                "message": f"Face registered for {name}"
            }
            logger.info(f"[v0] Returning response: {response}")
            return response
        
        except HTTPException:
            logger.error("[v0] HTTPException raised")
            raise
        except Exception as inner_e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"[v0] Inner exception in register_face: {str(inner_e)}\n{error_trace}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(inner_e)}")
    
    except Exception as outer_e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[v0] Outer exception in register_face: {str(outer_e)}\n{error_trace}")
        raise

@app.post("/api/match", response_model=MatchFaceResponse)
async def match_face(request: MatchFaceRequest):
    """
    Match a face against all registered faces in the database.
    
    Args:
        request: MatchFaceRequest containing base64-encoded image and top_k
        
    Returns:
        MatchFaceResponse with matches for each detected face
    """
    try:
        ensure_initialized()  # Load components if not already loaded
        
        image_base64 = request.image_base64
        top_k = request.top_k
        
        if not image_base64:
            raise HTTPException(status_code=400, detail="Missing image")
        
        # Decode image
        image = decode_base64_image(image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Detect faces
        detections = detector.detect_faces(image)
        detections = [
            det for det in detections
            if det.get("confidence", 0.0) >= 0.6
            and det["width"] >= 40
            and det["height"] >= 40
        ]
        detections = deduplicate_detections(detections, iou_threshold=0.45)

        if len(detections) == 0:
            return {
                "success": True,
                "num_faces_detected": 0,
                "matches": []
            }

        matches_list = []
        
        # Process each detected face independently
        for det_idx, detection in enumerate(detections):
            logger.info(f"[v0] ========== Processing Face #{det_idx + 1} ==========")
            faces = extract_face_regions(image, [detection])
            face_image = faces[0]
            logger.info(f"[v0] Face {det_idx}: bbox={detection['bbox']}, shape={face_image.shape}")
            
            # Preprocess
            if preprocessor:
                face_image = preprocessor.preprocess_face(face_image)
            
            # Generate embedding for THIS face
            embedding = embedding_generator.generate_embedding(face_image)
            logger.info(f"[v0] Face {det_idx}: embedding shape={embedding.shape if embedding is not None else None}, norm={np.linalg.norm(embedding) if embedding is not None else None}")
            
            if embedding is None:
                logger.warning(f"[v0] Face {det_idx}: Failed to generate embedding, skipping")
                continue
            
            # IMPORTANT: Ensure embedding is L2-normalized for consistent cosine similarity
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            logger.info(f"[v0] Face {det_idx}: After L2-normalization, norm={np.linalg.norm(embedding)}")
            
            # Get all reference embeddings from database (also L2-normalized)
            reference_embeddings = database.get_all_embeddings(expected_dim=embedding.shape[0])
            logger.info(f"[v0] Face {det_idx}: Comparing against {len(reference_embeddings)} registered persons with embedding dim {embedding.shape[0]}")
            
            # Find matches using cosine similarity and enforce the recognition threshold
            matches = matcher.find_matches_by_cosine_similarity(
                embedding,
                reference_embeddings,
                threshold=0.55,
                top_k=1
            )
            
            # Log top similarity scores for debugging
            if len(reference_embeddings) > 0:
                all_similarities = []
                for person_id, embeddings in reference_embeddings.items():
                    embeddings_array = np.array(embeddings)
                    try:
                        from .face_matching import SimilarityMetrics
                    except ImportError:
                        from face_matching import SimilarityMetrics
                    sims = SimilarityMetrics.batch_cosine_similarities(embedding, embeddings_array)
                    best_sim = float(np.max(sims))
                    person_info = database.get_person(person_id)
                    person_name = person_info['name'] if person_info else f'Person {person_id}'
                    all_similarities.append((person_name, person_id, best_sim))
                all_similarities.sort(key=lambda x: x[2], reverse=True)
                logger.info(f"[v0] Face {det_idx}: Top similarity scores: {[(name, f'{sim:.3f}') for name, _, sim in all_similarities[:3]]}")
            
            logger.info(f"[v0] Face {det_idx}: Found {len(matches)} matches above threshold")
            
            # Enrich matches with person info
            enriched_matches = []
            for match_idx, match in enumerate(matches):
                person_info = database.get_person(match["person_id"])
                if person_info:
                    match["name"] = person_info["name"]
                    match["status"] = person_info["status"]
                    threshold_status = "ABOVE" if match["similarity"] >= 0.55 else "BELOW"
                    logger.info(f"[v0] Face {det_idx} Match #{match_idx + 1}: {person_info['name']} (ID: {match['person_id']}, similarity: {match['similarity']:.3f}, {threshold_status} threshold)")
                enriched_matches.append(match)
            
            if len(enriched_matches) == 0:
                logger.warning(f"[v0] Face {det_idx}: No matches found above threshold")
                best_match = {
                    "person_id": -1,
                    "name": "Unknown",
                    "similarity": 0.0,
                    "confidence": 0.0,
                    "status": "unknown"
                }
            else:
                best_match = {
                    "person_id": enriched_matches[0]["person_id"],
                    "name": enriched_matches[0]["name"],
                    "similarity": enriched_matches[0]["similarity"],
                    "confidence": enriched_matches[0]["confidence"],
                    "status": enriched_matches[0].get("status", "registered")
                }
            
            # Create result for this specific face
            face_result = {
                "face_index": det_idx,
                "detection_bbox": [int(x) for x in detection["bbox"]],
                "matches": enriched_matches,
                "best_match": best_match,
                "status": "matched" if best_match["person_id"] != -1 else "unknown",
                "best_similarity": best_match["similarity"]
            }
            matches_list.append(face_result)
            logger.info(f"[v0] ========== Face #{det_idx + 1} Complete ==========")
        
        logger.info(f"[v0] Face matching completed. Processed {len(detections)} detected faces, returned {len(matches_list)} face results")
        
        return convert_numpy_types({
            "success": True,
            "num_faces_detected": len(detections),
            "matches": matches_list
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Error in /match: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/persons")
async def get_persons():
    """
    Get all registered persons in the database.
    
    Returns:
        JSON with list of all persons and face counts
    """
    try:
        ensure_initialized()  # Load components if not already loaded
        
        persons = database.get_all_persons()
        
        # Add face count for each person
        enriched_persons = []
        for person in persons:
            embeddings = database.get_embeddings_by_person(person["person_id"])
            person["face_count"] = len(embeddings)
            enriched_persons.append(person)
        
        return convert_numpy_types({
            "success": True,
            "persons": enriched_persons,
            "total_count": len(enriched_persons)
        })
    
    except Exception as e:
        logger.error(f"[v0] Error in /persons: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/person/{person_id}")
async def get_person(person_id: int):
    """
    Get details for a specific person.
    
    Args:
        person_id: ID of the person
        
    Returns:
        JSON with person details and face count
    """
    try:
        ensure_initialized()  # Load components if not already loaded
        
        person = database.get_person(person_id)
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Get embeddings
        embeddings = database.get_embeddings_by_person(person_id)
        person["face_count"] = len(embeddings)
        
        return convert_numpy_types({
            "success": True,
            "person": person
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Error in /person/<id>: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/person/{person_id}/status")
async def update_person_status(person_id: int, request: UpdatePersonStatusRequest):
    """
    Update a person's status.
    
    Args:
        person_id: ID of the person
        request: UpdatePersonStatusRequest with new status
        
    Returns:
        JSON with success message
    """
    try:
        status = request.status
        
        if not status:
            raise HTTPException(status_code=400, detail="Missing status")
        
        database.update_person_status(person_id, status)
        
        return {
            "success": True,
            "message": f"Updated person {person_id} status to {status}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Error in /person/<id>/status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/person/{person_id}")
async def delete_person(person_id: int):
    """
    Delete a person and all associated data.
    
    Args:
        person_id: ID of the person to delete
        
    Returns:
        JSON with success message
    """
    try:
        database.delete_person(person_id)
        
        return {
            "success": True,
            "message": f"Deleted person {person_id}"
        }
    
    except Exception as e:
        logger.error(f"[v0] Error in DELETE /person/<id>: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    """
    Get system statistics including total persons and embeddings.
    
    Returns:
        JSON with system statistics
    """
    try:
        ensure_initialized()  # Load components if not already loaded
        
        persons = database.get_all_persons()
        total_persons = len(persons)
        
        total_embeddings = 0
        for person in persons:
            embeddings = database.get_embeddings_by_person(person["person_id"])
            total_embeddings += len(embeddings)
        
        stats = {
            "total_registered_persons": total_persons,
            "total_facial_embeddings": total_embeddings,
            "device": device,
            "embedding_dimension": 128,
            "distance_metric": "euclidean",
            "match_threshold": 0.6
        }
        
        return convert_numpy_types({
            "success": True,
            "statistics": stats
        })
    
    except Exception as e:
        logger.error(f"[v0] Error in /statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare")
async def compare_faces(request: CompareFacesRequest):
    """
    Compare two faces directly.
    
    Args:
        request: CompareFacesRequest with two base64-encoded images
        
    Returns:
        JSON with comparison results including distance and confidence
    """
    try:
        ensure_initialized()  # Load components if not already loaded
        
        image1_base64 = request.image1_base64
        image2_base64 = request.image2_base64
        
        if not image1_base64 or not image2_base64:
            raise HTTPException(status_code=400, detail="Missing images")
        
        # Decode both images
        image1 = decode_base64_image(image1_base64)
        image2 = decode_base64_image(image2_base64)
        
        if image1 is None or image2 is None:
            raise HTTPException(status_code=400, detail="Invalid images")
        
        # Detect and extract faces
        det1 = detector.detect_faces(image1)
        det2 = detector.detect_faces(image2)
        
        if len(det1) == 0 or len(det2) == 0:
            raise HTTPException(status_code=400, detail="No face detected in one or both images")
        
        faces1 = extract_face_regions(image1, det1)
        faces2 = extract_face_regions(image2, det2)
        
        # Preprocess and generate embeddings
        if preprocessor:
            face1 = preprocessor.preprocess_face(faces1[0])
            face2 = preprocessor.preprocess_face(faces2[0])
        else:
            face1 = faces1[0]
            face2 = faces2[0]
        
        embedding1 = embedding_generator.generate_embedding(face1)
        embedding2 = embedding_generator.generate_embedding(face2)
        
        if embedding1 is None or embedding2 is None:
            raise HTTPException(status_code=500, detail="Failed to generate embeddings")
        
        # Compare
        result = matcher.compare_faces(embedding1, embedding2)
        
        return convert_numpy_types({
            "success": True,
            "comparison": result
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Error in /compare: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process_video")
async def process_video(video: UploadFile = File(...)):
    """
    Process a video file to detect and match faces across frames.

    Args:
        video: Video file upload

    Returns:
        JSON with processing results for each frame
    """
    try:
        ensure_initialized()  # Load components if not already loaded
        
        if not video.filename:
            raise HTTPException(status_code=400, detail="No video file provided")

        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov']
        file_ext = os.path.splitext(video.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")

        # Read video file and save to temporary location
        video_content = await video.read()
        temp_video_path = f"/tmp/temp_video_{uuid.uuid4()}{file_ext}"
        os.makedirs("/tmp", exist_ok=True)

        with open(temp_video_path, "wb") as f:
            f.write(video_content)

        try:
            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_video_path)

            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="Failed to open video file")

            results = []
            frame_count = 0
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_interval = max(1, int(fps))  # Process every frame, or adjust for performance

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Skip frames for performance (process every Nth frame)
                if frame_count % frame_interval != 0:
                    continue

                try:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Detect faces in the frame
                    detections = detector.detect_faces(frame_rgb)

                    if len(detections) > 0:
                        # Extract face regions
                        faces = extract_face_regions(frame_rgb, detections)

                        frame_faces = []
                        for face_idx, face_img in enumerate(faces):
                            try:
                                # Preprocess face
                                if preprocessor:
                                    processed_face = preprocessor.preprocess_face(face_img)
                                else:
                                    processed_face = face_img

                                # Generate embedding
                                embedding = embedding_generator.generate_embedding(processed_face)

                                if embedding is not None:
                                    # Get all reference embeddings
                                    reference_embeddings = database.get_all_embeddings(expected_dim=embedding.shape[0])
                                    logger.info(f"[v0] Video face {face_idx}: Comparing against {len(reference_embeddings)} registered persons with embedding dim {embedding.shape[0]}")
                                    
                                    # Find matches using cosine similarity
                                    matches = matcher.find_matches_by_cosine_similarity(
                                        embedding, 
                                        reference_embeddings, 
                                        threshold=0.65,
                                        top_k=1
                                    )

                                    face_result = {
                                        "face_index": face_idx,
                                        "detection_bbox": detections[face_idx]["bbox"] if isinstance(detections[face_idx], dict) else detections[face_idx].tolist() if hasattr(detections[face_idx], 'tolist') else list(detections[face_idx]),
                                        "match": None
                                    }

                                    if matches and len(matches) > 0:
                                        best_match = matches[0]
                                        # Enrich with person info
                                        person_info = database.get_person(best_match.get('person_id'))
                                        if person_info:
                                            face_result["match"] = {
                                                "person_id": best_match.get('person_id'),
                                                "name": person_info.get('name', 'Unknown'),
                                                "similarity": best_match.get('similarity', 0),
                                                "confidence": best_match.get('confidence', 0)
                                            }
                                        else:
                                            face_result["match"] = {
                                                "name": "Unknown",
                                                "similarity": 0,
                                                "confidence": 0
                                            }
                                    else:
                                        face_result["match"] = {
                                            "name": "Unknown",
                                            "similarity": 0,
                                            "confidence": 0
                                        }

                                    frame_faces.append(face_result)

                            except Exception as e:
                                logger.warning(f"Error processing face {face_idx} in frame {frame_count}: {str(e)}")
                                continue

                        if frame_faces:
                            success, frame_buffer = cv2.imencode('.jpg', frame)
                            frame_image_b64 = ''
                            if success:
                                frame_image_b64 = base64.b64encode(frame_buffer).decode('utf-8')

                            results.append({
                                "frame_number": frame_count,
                                "timestamp": f"{frame_count / fps:.2f}s",
                                "frame_image": f"data:image/jpeg;base64,{frame_image_b64}",
                                "frame_width": int(frame.shape[1]),
                                "frame_height": int(frame.shape[0]),
                                "faces": frame_faces
                            })

                except Exception as e:
                    logger.warning(f"Error processing frame {frame_count}: {str(e)}")
                    continue

            cap.release()

            # Clean up temporary file
            try:
                os.remove(temp_video_path)
            except:
                pass

        except Exception as e:
            # Clean up temporary file in case of error
            try:
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
            except:
                pass
            logger.error(f"[v0] Error in /process_video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        return convert_numpy_types({
            "success": True,
            "total_frames_processed": len(results),
            "results": results
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Error in /process_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== Root Endpoint =====================

@app.get("/face_recognition")
async def root():
    """Root endpoint with API documentation links for face recognition only."""
    return {
        "message": "Face Recognition API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/api/health",
            "register": "POST /api/register",
            "match": "POST /api/match",
            "compare": "POST /api/compare",
            "process_video": "POST /api/process_video",
            "persons": "GET /api/persons",
            "person": "GET /api/person/{id}",
            "update_status": "PUT /api/person/{id}/status",
            "delete": "DELETE /api/person/{id}",
            "statistics": "GET /api/statistics"
        }
    }

# ===================== Main =====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("[v0] Starting Face Recognition API Server with FastAPI...")
    logger.info("[v0] API Documentation available at http://localhost:8000/docs")
    logger.info("[v0] ReDoc available at http://localhost:8000/redoc")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
