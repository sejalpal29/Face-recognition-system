# Quick Start Guide - Face Recognition System

Get up and running with the complete face recognition system in minutes!

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd backend/face_recognition_system
pip install -r requirements.txt
```

### 2. Quick Test
```python
python -c "
import cv2
import numpy as np
import torch
from cnn_architecture import FaceEmbeddingCNN

# Initialize model
model = FaceEmbeddingCNN(embedding_dim=128)
print(f'✓ Model loaded successfully on device: {\"cuda\" if torch.cuda.is_available() else \"cpu\"}')

# Test with dummy input
dummy = torch.randn(1, 3, 224, 224)
output = model(dummy)
print(f'✓ Input shape: {dummy.shape}')
print(f'✓ Output shape: {output.shape}')
print(f'✓ Output norm: {torch.norm(output).item():.4f} (should be ~1.0)')
"
```

---

## Complete Example: Register and Match Faces

### Step 1: Prepare Face Images

```
face_dataset/
├── John/
│   ├── john_001.jpg
│   ├── john_002.jpg
│   └── john_003.jpg
├── Alice/
│   ├── alice_001.jpg
│   ├── alice_002.jpg
│   └── alice_003.jpg
└── Bob/
    ├── bob_001.jpg
    └── bob_002.jpg
```

### Step 2: Create Registration Script

```python
"""register_faces.py - Register all faces in dataset"""

import cv2
import os
from preprocessing import ImagePreprocessor
from face_detection import MultiScaleFaceDetector, extract_face_regions
from cnn_architecture import FaceEmbeddingCNN
from embedding_storage import (
    FaceEmbeddingDatabase,
    EmbeddingGenerator,
    FaceRegistrationManager
)
import torch

# Initialize
device = "cuda" if torch.cuda.is_available() else "cpu"
preprocessor = ImagePreprocessor(target_size=(224, 224))
detector = MultiScaleFaceDetector()
model = FaceEmbeddingCNN(embedding_dim=128).to(device)
database = FaceEmbeddingDatabase("faces.db")
embedding_gen = EmbeddingGenerator(model, device=device)
reg_manager = FaceRegistrationManager(database, embedding_gen, preprocessor)

# Register all persons
dataset_dir = "face_dataset"

for person_name in os.listdir(dataset_dir):
    person_dir = os.path.join(dataset_dir, person_name)
    if not os.path.isdir(person_dir):
        continue
    
    print(f"\nRegistering {person_name}...")
    
    for image_file in os.listdir(person_dir):
        image_path = os.path.join(person_dir, image_file)
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ✗ Failed to load {image_file}")
            continue
        
        # Detect faces
        detections = detector.detect_faces(image)
        if len(detections) == 0:
            print(f"  ✗ No face in {image_file}")
            continue
        
        # Extract face
        faces = extract_face_regions(image, [detections[0]])
        face_image = faces[0]
        
        # Register
        try:
            person_id, face_id, embedding = reg_manager.register_face(
                person_name,
                face_image,
                image_path,
                status="registered",
                metadata={"source": image_file}
            )
            print(f"  ✓ Registered {image_file}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

print("\n✓ Registration complete!")

# Show statistics
persons = database.get_all_persons()
print(f"\nRegistered {len(persons)} persons:")
for person in persons:
    embeddings = database.get_embeddings_by_person(person["person_id"])
    print(f"  • {person['name']}: {len(embeddings)} faces")
```

Run it:
```bash
python register_faces.py
```

### Step 3: Create Matching Script

```python
"""match_faces.py - Match test faces"""

import cv2
import numpy as np
from preprocessing import ImagePreprocessor
from face_detection import MultiScaleFaceDetector, extract_face_regions
from cnn_architecture import FaceEmbeddingCNN
from embedding_storage import FaceEmbeddingDatabase, EmbeddingGenerator
from face_matching import FaceMatcher
import torch

# Initialize
device = "cuda" if torch.cuda.is_available() else "cpu"
preprocessor = ImagePreprocessor(target_size=(224, 224))
detector = MultiScaleFaceDetector()
model = FaceEmbeddingCNN(embedding_dim=128).to(device)
database = FaceEmbeddingDatabase("faces.db")
embedding_gen = EmbeddingGenerator(model, device=device)
matcher = FaceMatcher(distance_metric="euclidean", threshold=0.6)

# Test image
test_image_path = "test_face.jpg"
image = cv2.imread(test_image_path)

if image is None:
    print(f"Error: Could not load {test_image_path}")
    exit(1)

# Detect face
detections = detector.detect_faces(image)
if len(detections) == 0:
    print("No face detected!")
    exit(1)

print(f"Detected {len(detections)} face(s)")

# Extract and process
faces = extract_face_regions(image, [detections[0]])
face_image = faces[0]
face_preprocessed = preprocessor.preprocess_face(face_image)

# Generate embedding
embedding = embedding_gen.generate_embedding(face_preprocessed)
if embedding is None:
    print("Failed to generate embedding!")
    exit(1)

# Find matches
reference_embeddings = database.get_all_embeddings()
matches = matcher.find_matches(embedding, reference_embeddings, top_k=5)

# Display results
print("\n" + "="*50)
print("MATCHING RESULTS")
print("="*50)

if not matches:
    print("❌ No matches found")
else:
    for i, match in enumerate(matches, 1):
        person = database.get_person(match["person_id"])
        confidence_bar = "█" * int(match["confidence"] * 20)
        print(f"\n{i}. {person['name']}")
        print(f"   Confidence: {match['confidence']:.1%} {confidence_bar}")
        print(f"   Distance: {match['distance']:.4f}")
        print(f"   Status: {person['status']}")
```

Run it:
```bash
python match_faces.py
```

---

## Start API Server

```bash
# Terminal 1: Start server
python api_server.py
# Server running on http://localhost:8000
# API Documentation: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc

curl http://localhost:8000/api/health
curl http://localhost:8000/api/persons
curl http://localhost:8000/api/statistics
```

---

## Training Your Own Model

### Prepare Dataset

```
training_data/
├── person_001/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── 003.jpg
├── person_002/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── 003.jpg
└── ...
```

### Train Model

```bash
# Using Triplet Loss
python train_example.py \
  --loss_type triplet \
  --epochs 20 \
  --batch_size 32 \
  --dataset_path ./training_data \
  --save_path ./trained_model.pth

# Or using Contrastive Loss
python train_example.py \
  --loss_type contrastive \
  --epochs 20 \
  --batch_size 32 \
  --dataset_path ./training_data \
  --save_path ./trained_model.pth
```

---

## Component Cheatsheet

### Preprocessing
```python
from preprocessing import ImagePreprocessor

preprocessor = ImagePreprocessor(target_size=(224, 224))
processed = preprocessor.preprocess_face(
    image,
    normalize=True,
    equalize=True,
    grayscale=False
)
```

### Face Detection
```python
from face_detection import MultiScaleFaceDetector, extract_face_regions

detector = MultiScaleFaceDetector()
detections = detector.detect_faces(image)
# detections: list of {"bbox": (x,y,w,h), "confidence": float, ...}

faces = extract_face_regions(image, detections)
```

### Embedding Generation
```python
from cnn_architecture import FaceEmbeddingCNN
from embedding_storage import EmbeddingGenerator

model = FaceEmbeddingCNN(embedding_dim=128)
embedding_gen = EmbeddingGenerator(model, device="cuda")
embedding = embedding_gen.generate_embedding(preprocessed_face)
# embedding: 128-dimensional L2-normalized vector
```

### Face Matching
```python
from face_matching import FaceMatcher, SimilarityMetrics

matcher = FaceMatcher(distance_metric="euclidean", threshold=0.6)

# Compare two faces
result = matcher.compare_faces(embedding1, embedding2)
# result: {is_match: bool, distance: float, confidence: float}

# Find matches in database
matches = matcher.find_matches(embedding, reference_embeddings, top_k=5)
```

### Database Operations
```python
from embedding_storage import FaceEmbeddingDatabase

db = FaceEmbeddingDatabase("faces.db")

# Register person
person_id = db.register_person("John Doe", status="registered")

# Store embedding
db.store_embedding(face_id, person_id, embedding_vector)

# Get all embeddings by person
embeddings = db.get_embeddings_by_person(person_id)

# Get all persons
persons = db.get_all_persons()

# Update status
db.update_person_status(person_id, "wanted")

# Delete person
db.delete_person(person_id)
```

---

## Performance Tips

### Speed Up Inference
```python
# 1. Use GPU
device = "cuda"  # Much faster than CPU

# 2. Batch processing
batch_embeddings = embedding_gen.generate_batch_embeddings(face_list)

# 3. Skip preprocessing if images are clean
preprocessed = preprocessor.preprocess_face(image, equalize=False)

# 4. Reduce image size for detection
small_image = cv2.resize(image, (640, 480))
detections = detector.detect_faces(small_image)
```

### Improve Accuracy
```python
# 1. Lower threshold for stricter matching
matcher = FaceMatcher(threshold=0.5)  # 0.6 by default

# 2. Use multiple frames
from face_matching import MultiFrameFaceMatching
multi_matcher = MultiFrameFaceMatching(matcher)
agg_embedding = multi_matcher.aggregate_embeddings([emb1, emb2, emb3])

# 3. Use better preprocessing
processed = preprocessor.preprocess_face(image, normalize=True, equalize=True)
```

---

## Troubleshooting

### "No face detected"
- Ensure image is clear and at least 100x100 pixels
- Try adjusting detection parameters
- Increase min_neighbors in Haar Cascade

### "Low confidence matches"
- Preprocess images more carefully
- Check threshold value (too low = false negatives)
- Verify training data quality

### "Out of memory"
- Reduce batch size
- Reduce image resolution
- Use CPU instead of GPU

### "GPU not detected"
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # Device name
```

---

## Next Steps

1. **Integrate with Your Application**
   - Use API server for HTTP requests
   - Or import modules directly

2. **Fine-tune for Your Domain**
   - Train on your specific faces
   - Adjust thresholds for your use case

3. **Optimize Performance**
   - Profile code with profiler
   - Consider model quantization
   - Implement caching

4. **Deploy to Production**
   - Use Docker for containerization
   - Deploy API server to cloud
   - Implement monitoring and logging

---

## Resources

- **Paper**: "FaceNet: A Unified Embedding for Face Recognition and Clustering" (Schroff et al., 2015)
- **Concept**: Metric Learning, Triplet Loss, Deep Metric Learning
- **Framework**: PyTorch, OpenCV, TensorFlow

Good luck! 🚀
