#!/usr/bin/env python3
"""
Populate the face_recognition.db with demo persons and dummy embeddings
"""
from embedding_storage import FaceEmbeddingDatabase
import numpy as np
import os

db_path = "face_recognition.db"
db = FaceEmbeddingDatabase(db_path)

demo_names = [
    "Rajesh Kumar",
    "Priya Sharma",
    "Vikram Singh",
    "Anjali Patel",
    "Arjun Reddy",
]

print("Populating face_recognition.db with demo persons and embeddings...")
for name in demo_names:
    person_id = db.register_person(name=name, status="registered", metadata={"demo": True})
    # store a placeholder face image path in the consolidated backend faces directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    face_dir = os.path.join(base_dir, "faces")
    face_path = os.path.join(face_dir, f"{person_id}.jpg")
    os.makedirs(face_dir, exist_ok=True)
    with open(face_path, "wb") as f:
        f.write(b"")
    face_id = db.store_face_image(person_id, face_path)
    # create a random embedding (128-d)
    embedding = np.random.rand(128).astype(np.float32)
    db.store_embedding(face_id, person_id, embedding)
    print(f"Added person: {name} (person_id={person_id}) with dummy embedding")

print("Done. Restart the API server if needed and refresh the dashboard.")
