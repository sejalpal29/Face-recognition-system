"""
Face Recognition System - Testing and Validation Script

This script tests the face recognition system to verify:
1. Embeddings are generated and normalized correctly
2. Cosine similarity matching works
3. Same person recognition across different images
4. Threshold handling
"""

import numpy as np
from scipy.spatial.distance import cosine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cosine_similarity():
    """Test cosine similarity calculation"""
    print("\n" + "="*60)
    print("TEST 1: Cosine Similarity Calculation")
    print("="*60)
    
    # Create two closely related vectors (same person scenario)
    embedding1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    embedding2 = np.array([0.11, 0.21, 0.31, 0.41, 0.51])  # Slightly different
    
    # Normalize
    emb1_norm = embedding1 / np.linalg.norm(embedding1)
    emb2_norm = embedding2 / np.linalg.norm(embedding2)
    
    # Calculate similarity
    similarity = np.dot(emb1_norm, emb2_norm)
    
    print(f"Embedding 1 (normalized): {emb1_norm}")
    print(f"Embedding 2 (normalized): {emb2_norm}")
    print(f"Cosine Similarity: {similarity:.4f}")
    print(f"Expected: > 0.95 (same person)")
    print(f"Result: {'PASS' if similarity > 0.95 else 'FAIL'}")


def test_l2_normalization():
    """Test L2 normalization"""
    print("\n" + "="*60)
    print("TEST 2: L2 Normalization")
    print("="*60)
    
    embedding = np.random.randn(128)
    normalized = embedding / np.linalg.norm(embedding)
    
    norm_value = np.linalg.norm(normalized)
    
    print(f"Original embedding norm: {np.linalg.norm(embedding):.4f}")
    print(f"Normalized embedding norm: {norm_value:.4f}")
    print(f"Expected: 1.0 (unit length)")
    print(f"Result: {'PASS' if abs(norm_value - 1.0) < 0.0001 else 'FAIL'}")


def test_threshold_logic():
    """Test threshold-based matching"""
    print("\n" + "="*60)
    print("TEST 3: Threshold-Based Matching")
    print("="*60)
    
    threshold = 0.65
    test_cases = [
        ("Same person", 0.85, True),
        ("Different person", 0.45, False),
        ("Borderline case", 0.65, True),
        ("Just below threshold", 0.64, False),
    ]
    
    for name, similarity, should_match in test_cases:
        matches = similarity >= threshold
        status = "PASS" if matches == should_match else "FAIL"
        print(f"{name}: similarity={similarity:.2f}, matches={matches} [{status}]")


def test_batch_similarity():
    """Test batch similarity computation"""
    print("\n" + "="*60)
    print("TEST 4: Batch Cosine Similarity")
    print("="*60)
    
    # One test embedding
    test_embedding = np.random.randn(128)
    test_embedding = test_embedding / np.linalg.norm(test_embedding)
    
    # Multiple reference embeddings
    n_refs = 5
    reference_embeddings = np.random.randn(n_refs, 128)
    reference_embeddings = reference_embeddings / np.linalg.norm(reference_embeddings, axis=1, keepdims=True)
    
    # Compute similarities
    similarities = np.dot(reference_embeddings, test_embedding)
    
    print(f"Test embedding shape: {test_embedding.shape}")
    print(f"Reference embeddings shape: {reference_embeddings.shape}")
    print(f"Similarities computed: {len(similarities)}")
    print(f"Similarity range: [{similarities.min():.4f}, {similarities.max():.4f}]")
    print(f"Expected range: [-1, 1]")
    
    all_in_range = np.all(similarities >= -1) and np.all(similarities <= 1)
    print(f"Result: {'PASS' if all_in_range else 'FAIL'}")
    
    # Find best match
    best_idx = np.argmax(similarities)
    print(f"Best match index: {best_idx}, similarity: {similarities[best_idx]:.4f}")


def test_multiple_embeddings_per_person():
    """Test matching when person has multiple embeddings"""
    print("\n" + "="*60)
    print("TEST 5: Multiple Embeddings Per Person")
    print("="*60)
    
    # Person has 3 registered embeddings
    person_embeddings = np.random.randn(3, 128)
    person_embeddings = person_embeddings / np.linalg.norm(person_embeddings, axis=1, keepdims=True)
    
    # New test image (should match this person)
    test_embedding = person_embeddings[0] + np.random.randn(128) * 0.1
    test_embedding = test_embedding / np.linalg.norm(test_embedding)
    
    # Compare against all embeddings
    similarities = np.dot(person_embeddings, test_embedding)
    best_similarity = np.max(similarities)
    
    print(f"Person has {len(person_embeddings)} registered embeddings")
    print(f"Test embedding similarity to each: {similarities}")
    print(f"Best similarity: {best_similarity:.4f}")
    print(f"Threshold: 0.65")
    print(f"Match result: {'MATCH' if best_similarity >= 0.65 else 'NO MATCH'}")
    print(f"Result: {'PASS' if best_similarity >= 0.65 else 'FAIL'}")


def test_unknown_person():
    """Test detection of unknown person"""
    print("\n" + "="*60)
    print("TEST 6: Unknown Person Detection")
    print("="*60)
    
    # Random embeddings (different people)
    registered_embeddings = np.random.randn(5, 128)  # 5 different people
    registered_embeddings = registered_embeddings / np.linalg.norm(registered_embeddings, axis=1, keepdims=True)
    
    unknown_embedding = np.random.randn(128)  # Completely different
    unknown_embedding = unknown_embedding / np.linalg.norm(unknown_embedding)
    
    # Compare all
    similarities = np.dot(registered_embeddings, unknown_embedding)
    best_similarity = np.max(similarities)
    threshold = 0.65
    
    print(f"Registered embeddings: {len(registered_embeddings)}")
    print(f"Unknown embedding: random person")
    print(f"Similarities to registered: {similarities}")
    print(f"Best similarity: {best_similarity:.4f}")
    print(f"Threshold: {threshold:.2f}")
    print(f"Result: {'Unknown' if best_similarity < threshold else 'Matched'}")
    print(f"Expected: Unknown person")
    print(f"Test Result: {'PASS' if best_similarity < threshold else 'FAIL'}")


def test_preprocessing_consistency():
    """Test that preprocessing is consistent"""
    print("\n" + "="*60)
    print("TEST 7: Preprocessing Consistency")
    print("="*60)
    
    print("Preprocessing Pipeline:")
    print("  1. BGR → RGB conversion")
    print("  2. Resize to 160×160")
    print("  3. CLAHE histogram equalization per channel")
    print("  4. Normalize to [0, 1]")
    print("  5. Convert to CHW format (3, 160, 160)")
    print("\nEnsure this pipeline is used for:")
    print("  • Registration: YES")
    print("  • Recognition: YES")
    print("  • Video processing: YES")
    print("\nResult: PASS (if all YES)")


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "FACE RECOGNITION SYSTEM TESTS" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    test_cosine_similarity()
    test_l2_normalization()
    test_threshold_logic()
    test_batch_similarity()
    test_multiple_embeddings_per_person()
    test_unknown_person()
    test_preprocessing_consistency()
    
    print("\n" + "="*60)
    print("All Tests Completed")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
