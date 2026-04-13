"""
Face Embedding Generation and Storage Module

This module handles:
1. Generating embeddings from face images
2. Storing embeddings in SQLite database
3. Retrieving embeddings for matching
4. Managing face database CRUD operations

Author: Face Recognition System
"""

import torch
import numpy as np
from typing import List, Tuple, Optional, Dict
import sqlite3
import json
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceEmbeddingDatabase:
    """
    SQLite database for storing facial embeddings and metadata.
    
    Schema:
    - faces: Stores face images and metadata
    - embeddings: Stores face embeddings (fixed-length vectors)
    - persons: Stores person information (ID, name, status)
    """
    
    def __init__(self, db_path: str = "face_recognition.db"):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._initialize_db()
        logger.info(f"[v0] FaceEmbeddingDatabase initialized at {db_path}")
    
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        cursor = self.connection.cursor()
        
        # Persons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                person_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'registered',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Faces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faces (
                face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(person_id)
            )
        """)
        
        # Embeddings table (core table for face matching)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                embedding_dim INTEGER DEFAULT 128,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (face_id) REFERENCES faces(face_id),
                FOREIGN KEY (person_id) REFERENCES persons(person_id)
            )
        """)
        
        # Create indices for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_person_id ON persons(person_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_person_faces ON faces(person_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embedding_person ON embeddings(person_id)
        """)
        
        self.connection.commit()
        logger.info("[v0] Database tables initialized")
    
    def register_person(self, name: str, status: str = "registered", metadata: Optional[Dict] = None) -> int:
        """
        Register a new person in the database.
        
        Args:
            name: Person's name
            status: Person's status ('registered', 'missing', 'wanted', etc.)
            metadata: Additional metadata as dictionary
            
        Returns:
            Person ID
        """
        cursor = self.connection.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute(
            "INSERT INTO persons (name, status, metadata) VALUES (?, ?, ?)",
            (name, status, metadata_json)
        )
        
        self.connection.commit()
        person_id = cursor.lastrowid
        
        logger.info(f"[v0] Registered person: {name} (ID: {person_id})")
        return person_id
    
    def store_face_image(self, person_id: int, image_path: str) -> int:
        """
        Store face image metadata.
        
        Args:
            person_id: ID of the person
            image_path: Path to the face image
            
        Returns:
            Face ID
        """
        cursor = self.connection.cursor()
        
        cursor.execute(
            "INSERT INTO faces (person_id, image_path) VALUES (?, ?)",
            (person_id, image_path)
        )
        
        self.connection.commit()
        face_id = cursor.lastrowid
        
        logger.info(f"[v0] Stored face image for person {person_id}: {image_path}")
        return face_id
    
    def store_embedding(
        self,
        face_id: int,
        person_id: int,
        embedding: np.ndarray
    ) -> int:
        """
        Store facial embedding in database.
        
        Args:
            face_id: ID of the face image
            person_id: ID of the person
            embedding: Embedding vector (numpy array)
            
        Returns:
            Embedding ID
        """
        cursor = self.connection.cursor()
        
        # L2-normalize embedding for consistent cosine similarity matching
        embedding_norm = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        # Convert embedding to bytes
        embedding_bytes = embedding_norm.astype(np.float32).tobytes()
        embedding_dim = embedding_norm.shape[0]
        
        cursor.execute(
            "INSERT INTO embeddings (face_id, person_id, embedding, embedding_dim) VALUES (?, ?, ?, ?)",
            (face_id, person_id, embedding_bytes, embedding_dim)
        )
        
        self.connection.commit()
        embedding_id = cursor.lastrowid
        
        logger.info(f"[v0] Stored L2-normalized embedding for face {face_id} (dim: {embedding_dim})")
        return embedding_id
    
    def get_embedding_dimension_counts(self) -> Dict[int, int]:
        """
        Get counts of stored embedding dimensions.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT embedding_dim, COUNT(*) FROM embeddings GROUP BY embedding_dim"
        )
        rows = cursor.fetchall()
        dim_counts = {int(row[0]): int(row[1]) for row in rows}
        logger.info(f"[v0] Embedding dimension counts: {dim_counts}")
        return dim_counts

    def get_person(self, person_id: int) -> Optional[Dict]:
        """
        Get person information.
        
        Args:
            person_id: ID of the person
            
        Returns:
            Dictionary with person data or None
        """
        cursor = self.connection.cursor()
        
        cursor.execute(
            "SELECT person_id, name, status, created_at, metadata FROM persons WHERE person_id = ?",
            (person_id,)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                "person_id": row[0],
                "name": row[1],
                "status": row[2],
                "created_at": row[3],
                "metadata": json.loads(row[4]) if row[4] else None
            }
        return None
    
    def get_person_by_name(self, name: str) -> Optional[Dict]:
        """Get person by name."""
        cursor = self.connection.cursor()
        
        cursor.execute(
            "SELECT person_id, name, status, created_at, metadata FROM persons WHERE name = ?",
            (name,)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                "person_id": row[0],
                "name": row[1],
                "status": row[2],
                "created_at": row[3],
                "metadata": json.loads(row[4]) if row[4] else None
            }
        return None
    
    def get_all_persons(self) -> List[Dict]:
        """Get all registered persons."""
        cursor = self.connection.cursor()
        
        cursor.execute("SELECT person_id, name, status, created_at, metadata FROM persons")
        rows = cursor.fetchall()
        
        persons = []
        for row in rows:
            persons.append({
                "person_id": row[0],
                "name": row[1],
                "status": row[2],
                "created_at": row[3],
                "metadata": json.loads(row[4]) if row[4] else None
            })
        
        return persons
    
    def get_embeddings_by_person(self, person_id: int, expected_dim: Optional[int] = None) -> List[Tuple[int, np.ndarray]]:
        """
        Get all embeddings for a person.
        
        Args:
            person_id: ID of the person
            expected_dim: Optional embedding dimension to filter by
            
        Returns:
            List of (embedding_id, embedding_vector) tuples
        """
        cursor = self.connection.cursor()
        
        if expected_dim is not None:
            cursor.execute(
                "SELECT embedding_id, embedding, embedding_dim FROM embeddings WHERE person_id = ? AND embedding_dim = ?",
                (person_id, expected_dim)
            )
        else:
            cursor.execute(
                "SELECT embedding_id, embedding, embedding_dim FROM embeddings WHERE person_id = ?",
                (person_id,)
            )
        
        rows = cursor.fetchall()
        embeddings = []
        
        for row in rows:
            embedding_id = row[0]
            embedding_bytes = row[1]
            embedding_dim = row[2]
            
            # Convert bytes back to numpy array using stored dimension
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32).reshape(embedding_dim)
            embeddings.append((embedding_id, embedding))
        
        logger.info(f"[v0] Retrieved {len(embeddings)} embeddings for person {person_id} (expected_dim={expected_dim})")
        return embeddings
    
    def get_all_embeddings(self, expected_dim: Optional[int] = None) -> Dict[int, List[np.ndarray]]:
        """
        Get all embeddings organized by person.
        
        Args:
            expected_dim: Optional embedding dimension to filter by
        
        Returns:
            Dictionary mapping person_id to list of embeddings
        """
        cursor = self.connection.cursor()
        
        if expected_dim is not None:
            cursor.execute(
                "SELECT person_id, embedding, embedding_dim FROM embeddings WHERE embedding_dim = ? ORDER BY person_id",
                (expected_dim,)
            )
        else:
            cursor.execute("""
                SELECT person_id, embedding, embedding_dim FROM embeddings
                ORDER BY person_id
            """)
        
        rows = cursor.fetchall()
        embeddings_by_person = {}
        
        for row in rows:
            person_id = row[0]
            embedding_bytes = row[1]
            embedding_dim = row[2]
            
            # Convert bytes back to numpy array using stored dimension
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32).reshape(embedding_dim)
            
            if person_id not in embeddings_by_person:
                embeddings_by_person[person_id] = []
            
            embeddings_by_person[person_id].append(embedding)
        
        if expected_dim is not None:
            skipped_count = 0
            cursor.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_dim != ?", (expected_dim,))
            skipped_count = cursor.fetchone()[0]
            if skipped_count > 0:
                logger.warning(f"[v0] Skipped {skipped_count} stored embeddings with mismatched dimension {expected_dim}")
        
        logger.info(f"[v0] Retrieved embeddings for {len(embeddings_by_person)} persons (expected_dim={expected_dim})")
        return embeddings_by_person
    
    def delete_person(self, person_id: int):
        """Delete person and associated data."""
        cursor = self.connection.cursor()
        
        # Delete embeddings
        cursor.execute("DELETE FROM embeddings WHERE person_id = ?", (person_id,))
        
        # Delete faces
        cursor.execute("DELETE FROM faces WHERE person_id = ?", (person_id,))
        
        # Delete person
        cursor.execute("DELETE FROM persons WHERE person_id = ?", (person_id,))
        
        self.connection.commit()
        logger.info(f"[v0] Deleted person {person_id} and associated data")
    
    def update_person_status(self, person_id: int, status: str):
        """Update person's status."""
        cursor = self.connection.cursor()
        
        cursor.execute(
            "UPDATE persons SET status = ? WHERE person_id = ?",
            (status, person_id)
        )
        
        self.connection.commit()
        logger.info(f"[v0] Updated person {person_id} status to {status}")
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("[v0] Database connection closed")


class EmbeddingGenerator:
    """
    Generate facial embeddings from images using trained model.
    """
    
    def __init__(self, model: torch.nn.Module, device: str = "cpu", normalize_input: bool = False):
        """
        Initialize embedding generator.
        
        Args:
            model: Trained face recognition model
            device: Device to run on ('cpu' or 'cuda')
            normalize_input: Whether to scale input from [0, 1] to [-1, 1]
        """
        self.model = model.to(device)
        self.model.eval()
        self.device = device
        self.normalize_input = normalize_input
        logger.info(f"[v0] EmbeddingGenerator initialized on device: {device}")
    
    def generate_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate embedding for a single face image.
        
        Args:
            face_image: Preprocessed face image in CHW format (3, 160, 160) with values in [0, 1]
            
        Returns:
            Embedding vector or None if generation fails
        """
        try:
            # Input should already be in CHW format from preprocessing
            # Add batch dimension
            face_tensor = torch.from_numpy(face_image).unsqueeze(0).float()
            face_tensor = face_tensor.to(self.device)
            
            # Apply expected normalization for pretrained facenet-pytorch models
            if self.normalize_input:
                face_tensor = (face_tensor - 0.5) * 2.0

            # Generate embedding
            with torch.no_grad():
                embedding = self.model(face_tensor)
            
            # Convert to numpy and remove batch dimension
            embedding = embedding.cpu().numpy()[0]
            
            logger.info(f"[v0] Generated embedding with shape: {embedding.shape}")
            return embedding
        
        except Exception as e:
            logger.error(f"[v0] Error generating embedding: {str(e)}")
            return None
    
    def generate_batch_embeddings(self, face_images: List[np.ndarray]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple faces.
        
        Args:
            face_images: List of face images
            
        Returns:
            List of embeddings
        """
        embeddings = []
        
        for i, face_image in enumerate(face_images):
            embedding = self.generate_embedding(face_image)
            if embedding is not None:
                embeddings.append(embedding)
            logger.info(f"[v0] Generated embedding {i+1}/{len(face_images)}")
        
        return embeddings


class FaceRegistrationManager:
    """
    Manages the complete face registration process.
    """
    
    def __init__(
        self,
        database: FaceEmbeddingDatabase,
        embedding_generator: EmbeddingGenerator,
        preprocessor=None
    ):
        """
        Initialize registration manager.
        
        Args:
            database: Face embedding database
            embedding_generator: Embedding generator instance
            preprocessor: Image preprocessor instance
        """
        self.database = database
        self.embedding_generator = embedding_generator
        self.preprocessor = preprocessor
        logger.info("[v0] FaceRegistrationManager initialized")
    
    def register_face(
        self,
        person_name: str,
        face_image: np.ndarray,
        image_path: str,
        status: str = "registered",
        metadata: Optional[Dict] = None
    ) -> Tuple[int, int, np.ndarray]:
        """
        Register a new face.
        
        Args:
            person_name: Name of the person
            face_image: Face image (BGR)
            image_path: Path where image is stored
            status: Person's status
            metadata: Additional metadata
            
        Returns:
            Tuple of (person_id, face_id, embedding)
        """
        # Always create a new registered person entry for each registration.
        # This avoids reusing a previous person record when multiple people
        # are registered with the same name or when you expect distinct entries.
        person_id = self.database.register_person(person_name, status, metadata)

        # Preprocess face image
        if self.preprocessor:
            face_image = self.preprocessor.preprocess_face(face_image)
        
        # Save the cropped face image to disk for future debugging and migration
        if image_path:
            # Ensure the path is absolute
            if not os.path.isabs(image_path):
                # Assume relative to the backend directory
                backend_dir = os.path.dirname(os.path.dirname(__file__))
                image_path = os.path.join(backend_dir, image_path)
            dir_path = os.path.dirname(image_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            cv2.imwrite(image_path, face_image)

        # Store face image metadata
        face_id = self.database.store_face_image(person_id, image_path)
        
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(face_image)
        
        if embedding is None:
            logger.error("[v0] Failed to generate embedding")
            return person_id, face_id, None
        
        # Store embedding
        self.database.store_embedding(face_id, person_id, embedding)
        
        logger.info(f"[v0] Successfully registered face for {person_name}")
        return person_id, face_id, embedding
    
    def register_multiple_faces(
        self,
        person_name: str,
        face_images: List[Tuple[np.ndarray, str]],
        status: str = "registered",
        metadata: Optional[Dict] = None
    ) -> Tuple[int, List[int], List[np.ndarray]]:
        """
        Register multiple faces for the same person.
        
        Args:
            person_name: Name of the person
            face_images: List of (image, image_path) tuples
            status: Person's status
            metadata: Additional metadata
            
        Returns:
            Tuple of (person_id, list of face_ids, list of embeddings)
        """
        face_ids = []
        embeddings = []
        
        for i, (face_image, image_path) in enumerate(face_images):
            try:
                person_id, face_id, embedding = self.register_face(
                    person_name, face_image, image_path, status, metadata
                )
                face_ids.append(face_id)
                if embedding is not None:
                    embeddings.append(embedding)
                logger.info(f"[v0] Registered face {i+1}/{len(face_images)}")
            except Exception as e:
                logger.error(f"[v0] Error registering face {i}: {str(e)}")
        
        logger.info(f"[v0] Successfully registered {len(embeddings)} faces for {person_name}")
        return person_id, face_ids, embeddings
