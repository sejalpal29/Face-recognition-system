import cv2
import numpy as np
import pickle
import os
from pathlib import Path
import logging
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))  # Threshold for considering a match


def detect_faces(image_path: str) -> list:
    """
    Detect faces in an image using OpenCV
    Returns list of face coordinates and cropped face images
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to read image: {image_path}")
            return []
        
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if faces is None:
            logger.info("Detected 0 faces in image")
            return []

        # convert to list of tuples for safe truthiness checks elsewhere
        faces_list = [tuple(f) for f in faces]
        logger.info(f"Detected {len(faces_list)} faces in image")
        return faces_list
    except Exception as e:
        logger.error(f"Error detecting faces: {str(e)}")
        return []

def crop_face(image_path: str, face_coords: tuple) -> np.ndarray:
    """
    Crop a face from the image given coordinates
    Returns cropped face image
    """
    try:
        img = cv2.imread(image_path)
        x, y, w, h = face_coords
        # Add padding
        padding = 20
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2 * padding)
        h = min(img.shape[0] - y, h + 2 * padding)
        
        cropped_face = img[y:y+h, x:x+w]
        return cropped_face
    except Exception as e:
        logger.error(f"Error cropping face: {str(e)}")
        return None

def generate_embedding(image_path: str) -> np.ndarray:
    """
    Generate face embedding using DeepFace
    Returns embedding vector
    """
    try:
        embedding = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet512",
            enforce_detection=False
        )
        if embedding and len(embedding) > 0:
            return np.array(embedding[0]['embedding'])
    except Exception as e:
        logger.warning(f"DeepFace embedding failed: {e}")

    # Fallback: simple handcrafted embedding (grayscale resize + flatten)
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        emb = resized.astype(np.float32).flatten()
        # normalize
        if np.linalg.norm(emb) > 0:
            emb = emb / np.linalg.norm(emb)
        return emb
    except Exception as e:
        logger.error(f"Fallback embedding generation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None

def save_embedding(embedding: np.ndarray, embedding_path: str):
    """Save embedding to file"""
    try:
        with open(embedding_path, 'wb') as f:
            pickle.dump(embedding, f)
        logger.info(f"Embedding saved to {embedding_path}")
    except Exception as e:
        logger.error(f"Error saving embedding: {str(e)}")

def load_embedding(embedding_path: str) -> np.ndarray:
    """Load embedding from file"""
    try:
        if not os.path.exists(embedding_path):
            return None
        with open(embedding_path, 'rb') as f:
            embedding = pickle.load(f)
        return embedding
    except Exception as e:
        logger.error(f"Error loading embedding: {str(e)}")
        return None

def compare_embeddings(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compare two embeddings using cosine similarity
    Returns similarity score (0-1)
    """
    try:
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        similarity = cosine_similarity(
            embedding1.reshape(1, -1),
            embedding2.reshape(1, -1)
        )[0][0]
        return float(similarity)
    except Exception as e:
        logger.error(f"Error comparing embeddings: {str(e)}")
        return 0.0

def find_match(query_embedding: np.ndarray, all_embeddings: dict, threshold: float = 0.6) -> tuple:
    """
    Find best match for query embedding
    Returns (person_id, similarity_score) or (None, 0.0) if no match above threshold
    """
    best_match_id = None
    best_similarity = 0.0
    
    logger.info(f"[v0] Comparing query embedding against {len(all_embeddings)} stored embeddings")
    
    for person_id, embedding_path in all_embeddings.items():
        stored_embedding = load_embedding(embedding_path)
        if stored_embedding is None:
            fallback_path = f"embeddings/person_{person_id}.pkl"
            if fallback_path != embedding_path and os.path.exists(fallback_path):
                logger.info(f"[v0] Falling back to alternate embedding path for person ID {person_id}: {fallback_path}")
                stored_embedding = load_embedding(fallback_path)
        
        if stored_embedding is not None:
            similarity = compare_embeddings(query_embedding, stored_embedding)
            logger.debug(f"[v0] Person ID {person_id}: similarity = {similarity:.4f}")
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = person_id
        else:
            logger.warning(f"[v0] Failed to load embedding for person ID {person_id} from {embedding_path}")
    
    logger.info(f"[v0] Best match: Person ID {best_match_id}, Similarity: {best_similarity:.4f}, Threshold: {threshold}")
    
    if best_similarity >= threshold:
        return best_match_id, best_similarity
    
    return None, best_similarity
