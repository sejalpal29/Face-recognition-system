"""
Testing and Validation Module

Comprehensive testing suite for face recognition system including:
1. Unit tests for each component
2. Integration tests
3. Performance benchmarks
4. Validation metrics

Run tests with:
    python -m pytest testing.py -v
    
Or for benchmarks:
    python testing.py --benchmark

Author: Face Recognition System
"""

import numpy as np
import torch
import cv2
import time
import logging
from typing import Dict, List, Tuple
import json
from pathlib import Path

from preprocessing import ImagePreprocessor
from face_detection import MultiScaleFaceDetector, extract_face_regions
from cnn_architecture import FaceEmbeddingCNN, ConvBlock, ResidualBlock
from embedding_storage import FaceEmbeddingDatabase, EmbeddingGenerator
from face_matching import FaceMatcher, SimilarityMetrics, MultiFrameFaceMatching
from training import TripletLoss, ContrastiveLoss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPreprocessor:
    """Test image preprocessing module."""
    
    @staticmethod
    def test_grayscale_conversion():
        """Test grayscale conversion."""
        logger.info("[v0] Testing grayscale conversion...")
        preprocessor = ImagePreprocessor()
        
        # Create dummy BGR image
        image = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        
        # Convert to grayscale
        gray = preprocessor.to_grayscale(image)
        
        assert gray.shape == (224, 224), "Grayscale shape incorrect"
        assert gray.dtype == np.uint8 or gray.dtype == np.float32, "Grayscale dtype incorrect"
        logger.info("[v0] ✓ Grayscale conversion passed")
    
    @staticmethod
    def test_normalization():
        """Test image normalization."""
        logger.info("[v0] Testing normalization...")
        preprocessor = ImagePreprocessor()
        
        # Create dummy image
        image = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8).astype(np.float32)
        
        # Z-score normalization
        normalized = preprocessor.normalize_image(image, method="zscore")
        assert abs(np.mean(normalized)) < 0.1, "Z-score mean not centered"
        assert abs(np.std(normalized) - 1.0) < 0.1, "Z-score std not 1.0"
        logger.info("[v0] ✓ Z-score normalization passed")
        
        # Min-max normalization
        normalized = preprocessor.normalize_image(image, method="minmax")
        assert np.min(normalized) >= -0.1, "Min-max min value incorrect"
        assert np.max(normalized) <= 1.1, "Min-max max value incorrect"
        logger.info("[v0] ✓ Min-max normalization passed")
    
    @staticmethod
    def test_resize():
        """Test image resizing."""
        logger.info("[v0] Testing image resizing...")
        preprocessor = ImagePreprocessor(target_size=(224, 224))
        
        # Test various input sizes
        for h, w in [(112, 112), (448, 448), (640, 480)]:
            image = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
            resized = preprocessor.resize_image(image)
            assert resized.shape[:2] == (224, 224), f"Resize failed for {h}x{w}"
        
        logger.info("[v0] ✓ Image resizing passed")


class TestFaceDetection:
    """Test face detection module."""
    
    @staticmethod
    def test_haar_cascade_detector():
        """Test Haar Cascade detector."""
        logger.info("[v0] Testing Haar Cascade detector...")
        from face_detection import HaarCascadeDetector
        
        detector = HaarCascadeDetector()
        
        # Create dummy image
        image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Detect
        detections = detector.detect_faces(image)
        
        assert isinstance(detections, list), "Detections should be a list"
        for det in detections:
            assert "bbox" in det, "Detection missing bbox"
            assert "confidence" in det, "Detection missing confidence"
        
        logger.info(f"[v0] ✓ Haar Cascade detector passed (found {len(detections)} faces)")
    
    @staticmethod
    def test_iou_calculation():
        """Test IoU calculation for NMS."""
        logger.info("[v0] Testing IoU calculation...")
        from face_detection import MultiScaleFaceDetector
        
        detector = MultiScaleFaceDetector()
        
        # Same boxes should have IoU = 1.0
        box1 = (100, 100, 50, 50)
        iou = detector._calculate_iou(box1, box1)
        assert abs(iou - 1.0) < 1e-5, "IoU for identical boxes should be 1.0"
        
        # Completely separate boxes should have IoU = 0.0
        box2 = (200, 200, 50, 50)
        iou = detector._calculate_iou(box1, box2)
        assert abs(iou) < 1e-5, "IoU for separate boxes should be 0.0"
        
        logger.info("[v0] ✓ IoU calculation passed")


class TestCNNArchitecture:
    """Test CNN architecture."""
    
    @staticmethod
    def test_conv_block():
        """Test ConvBlock."""
        logger.info("[v0] Testing ConvBlock...")
        
        block = ConvBlock(3, 64, kernel_size=3, stride=1, padding=1)
        
        # Test forward pass
        x = torch.randn(2, 3, 224, 224)
        y = block(x)
        
        assert y.shape == (2, 64, 224, 224), "ConvBlock output shape incorrect"
        logger.info("[v0] ✓ ConvBlock passed")
    
    @staticmethod
    def test_residual_block():
        """Test ResidualBlock."""
        logger.info("[v0] Testing ResidualBlock...")
        
        block = ResidualBlock(64, kernel_size=3)
        
        # Test forward pass
        x = torch.randn(2, 64, 224, 224)
        y = block(x)
        
        assert y.shape == x.shape, "ResidualBlock output shape incorrect"
        logger.info("[v0] ✓ ResidualBlock passed")
    
    @staticmethod
    def test_face_embedding_cnn():
        """Test FaceEmbeddingCNN."""
        logger.info("[v0] Testing FaceEmbeddingCNN...")
        
        model = FaceEmbeddingCNN(embedding_dim=128)
        model.eval()
        
        # Test forward pass
        x = torch.randn(4, 3, 224, 224)
        embeddings = model(x)
        
        assert embeddings.shape == (4, 128), "Embedding shape incorrect"
        
        # Check L2 normalization
        norms = torch.norm(embeddings, dim=1)
        assert torch.allclose(norms, torch.ones(4), atol=1e-5), "Embeddings not L2-normalized"
        
        logger.info("[v0] ✓ FaceEmbeddingCNN passed")


class TestLossFunctions:
    """Test loss functions."""
    
    @staticmethod
    def test_triplet_loss():
        """Test Triplet Loss."""
        logger.info("[v0] Testing Triplet Loss...")
        
        loss_fn = TripletLoss(margin=0.5, distance_metric="euclidean")
        
        # Create embeddings
        anchor = torch.randn(4, 128)
        positive = anchor + torch.randn(4, 128) * 0.1  # Similar to anchor
        negative = torch.randn(4, 128)  # Different from anchor
        
        loss = loss_fn(anchor, positive, negative)
        
        assert loss.item() > 0, "Triplet loss should be positive"
        assert not torch.isnan(loss), "Triplet loss is NaN"
        
        logger.info(f"[v0] ✓ Triplet Loss passed (loss value: {loss.item():.4f})")
    
    @staticmethod
    def test_contrastive_loss():
        """Test Contrastive Loss."""
        logger.info("[v0] Testing Contrastive Loss...")
        
        loss_fn = ContrastiveLoss(margin=1.0, distance_metric="euclidean")
        
        # Similar pair (label=0)
        emb1 = torch.randn(4, 128)
        emb2 = emb1 + torch.randn(4, 128) * 0.1
        labels = torch.zeros(4)
        
        loss = loss_fn(emb1, emb2, labels)
        
        assert loss.item() > 0, "Contrastive loss should be positive"
        assert not torch.isnan(loss), "Contrastive loss is NaN"
        
        logger.info(f"[v0] ✓ Contrastive Loss passed (loss value: {loss.item():.4f})")


class TestFaceMatching:
    """Test face matching module."""
    
    @staticmethod
    def test_euclidean_distance():
        """Test Euclidean distance calculation."""
        logger.info("[v0] Testing Euclidean distance...")
        
        # Test with known values
        emb1 = np.array([0, 0, 0], dtype=np.float32)
        emb2 = np.array([3, 4, 0], dtype=np.float32)
        
        distance = SimilarityMetrics.euclidean_distance(emb1, emb2)
        
        assert abs(distance - 5.0) < 1e-5, "Euclidean distance calculation incorrect"
        logger.info("[v0] ✓ Euclidean distance passed")
    
    @staticmethod
    def test_cosine_similarity():
        """Test cosine similarity."""
        logger.info("[v0] Testing cosine similarity...")
        
        # Identical vectors should have similarity 1.0
        emb1 = np.array([1, 0, 0], dtype=np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        
        similarity = SimilarityMetrics.cosine_similarity(emb1, emb1)
        
        assert abs(similarity - 1.0) < 1e-5, "Cosine similarity for identical vectors should be 1.0"
        logger.info("[v0] ✓ Cosine similarity passed")
    
    @staticmethod
    def test_face_matcher():
        """Test face matcher."""
        logger.info("[v0] Testing face matcher...")
        
        matcher = FaceMatcher(distance_metric="euclidean", threshold=0.6)
        
        # Create embeddings
        emb1 = np.random.randn(128).astype(np.float32)
        emb1 /= np.linalg.norm(emb1)
        
        emb2 = emb1 + np.random.randn(128).astype(np.float32) * 0.1
        emb2 /= np.linalg.norm(emb2)
        
        # Compare
        result = matcher.compare_faces(emb1, emb2)
        
        assert "is_match" in result, "Result missing is_match"
        assert "distance" in result, "Result missing distance"
        assert "confidence" in result, "Result missing confidence"
        assert 0 <= result["confidence"] <= 1, "Confidence out of range"
        
        logger.info("[v0] ✓ Face matcher passed")


class TestDatabase:
    """Test database operations."""
    
    @staticmethod
    def test_database_creation():
        """Test database creation."""
        logger.info("[v0] Testing database creation...")
        
        # Create temporary database
        db = FaceEmbeddingDatabase(":memory:")
        
        # Register person
        person_id = db.register_person("Test Person", status="registered")
        assert person_id > 0, "Person ID should be positive"
        
        # Retrieve person
        person = db.get_person(person_id)
        assert person is not None, "Person should exist"
        assert person["name"] == "Test Person", "Person name mismatch"
        
        logger.info("[v0] ✓ Database operations passed")
    
    @staticmethod
    def test_embedding_storage():
        """Test embedding storage."""
        logger.info("[v0] Testing embedding storage...")
        
        db = FaceEmbeddingDatabase(":memory:")
        
        # Register person and face
        person_id = db.register_person("Test Person")
        face_id = db.store_face_image(person_id, "test.jpg")
        
        # Create and store embedding
        embedding = np.random.randn(128).astype(np.float32)
        embedding /= np.linalg.norm(embedding)
        
        embedding_id = db.store_embedding(face_id, person_id, embedding)
        assert embedding_id > 0, "Embedding ID should be positive"
        
        # Retrieve embedding
        embeddings = db.get_embeddings_by_person(person_id)
        assert len(embeddings) == 1, "Should have 1 embedding"
        
        retrieved_embedding = embeddings[0][1]
        assert np.allclose(embedding, retrieved_embedding), "Embedding retrieval mismatch"
        
        logger.info("[v0] ✓ Embedding storage passed")


class PerformanceBenchmark:
    """Performance benchmarking."""
    
    @staticmethod
    def benchmark_preprocessing():
        """Benchmark preprocessing."""
        logger.info("[v0] Benchmarking preprocessing...")
        
        preprocessor = ImagePreprocessor()
        image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Warm up
        preprocessor.preprocess_face(image)
        
        # Benchmark
        num_runs = 100
        start = time.time()
        for _ in range(num_runs):
            preprocessor.preprocess_face(image)
        elapsed = time.time() - start
        
        time_per_image = elapsed / num_runs
        logger.info(f"[v0] Preprocessing: {time_per_image*1000:.2f}ms per image")
    
    @staticmethod
    def benchmark_embedding_generation():
        """Benchmark embedding generation."""
        logger.info("[v0] Benchmarking embedding generation...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = FaceEmbeddingCNN(embedding_dim=128).to(device)
        embedding_gen = EmbeddingGenerator(model, device=device)
        
        # Create dummy face
        face = np.random.randn(224, 224, 3).astype(np.float32)
        
        # Warm up
        embedding_gen.generate_embedding(face)
        
        # Benchmark
        num_runs = 100
        start = time.time()
        for _ in range(num_runs):
            embedding_gen.generate_embedding(face)
        elapsed = time.time() - start
        
        time_per_embedding = elapsed / num_runs
        logger.info(f"[v0] Embedding generation: {time_per_embedding*1000:.2f}ms per face ({device})")
    
    @staticmethod
    def benchmark_face_matching():
        """Benchmark face matching."""
        logger.info("[v0] Benchmarking face matching...")
        
        matcher = FaceMatcher()
        
        # Create embeddings
        test_embedding = np.random.randn(128).astype(np.float32)
        reference_embeddings = {
            i: [np.random.randn(128).astype(np.float32) for _ in range(5)]
            for i in range(100)
        }
        
        # Benchmark
        num_runs = 100
        start = time.time()
        for _ in range(num_runs):
            matcher.find_matches(test_embedding, reference_embeddings, top_k=5)
        elapsed = time.time() - start
        
        time_per_match = elapsed / num_runs
        logger.info(f"[v0] Face matching: {time_per_match*1000:.2f}ms (100 reference persons, 5 faces each)")


def run_all_tests():
    """Run all tests."""
    logger.info("[v0] ========== Running Face Recognition System Tests ==========")
    
    # Preprocessing tests
    logger.info("\n[v0] --- Preprocessing Tests ---")
    TestPreprocessor.test_grayscale_conversion()
    TestPreprocessor.test_normalization()
    TestPreprocessor.test_resize()
    
    # Face detection tests
    logger.info("\n[v0] --- Face Detection Tests ---")
    TestFaceDetection.test_haar_cascade_detector()
    TestFaceDetection.test_iou_calculation()
    
    # CNN architecture tests
    logger.info("\n[v0] --- CNN Architecture Tests ---")
    TestCNNArchitecture.test_conv_block()
    TestCNNArchitecture.test_residual_block()
    TestCNNArchitecture.test_face_embedding_cnn()
    
    # Loss function tests
    logger.info("\n[v0] --- Loss Function Tests ---")
    TestLossFunctions.test_triplet_loss()
    TestLossFunctions.test_contrastive_loss()
    
    # Face matching tests
    logger.info("\n[v0] --- Face Matching Tests ---")
    TestFaceMatching.test_euclidean_distance()
    TestFaceMatching.test_cosine_similarity()
    TestFaceMatching.test_face_matcher()
    
    # Database tests
    logger.info("\n[v0] --- Database Tests ---")
    TestDatabase.test_database_creation()
    TestDatabase.test_embedding_storage()
    
    logger.info("\n[v0] ✓ All tests passed!")


def run_benchmarks():
    """Run performance benchmarks."""
    logger.info("[v0] ========== Running Performance Benchmarks ==========")
    
    PerformanceBenchmark.benchmark_preprocessing()
    PerformanceBenchmark.benchmark_embedding_generation()
    PerformanceBenchmark.benchmark_face_matching()
    
    logger.info("[v0] ✓ Benchmarks completed!")


if __name__ == "__main__":
    import sys
    
    if "--benchmark" in sys.argv:
        run_benchmarks()
    else:
        run_all_tests()
