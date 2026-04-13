"""
Face Matching and Similarity Metrics Module

This module implements:
1. Distance metrics (Euclidean, Cosine)
2. Face matching algorithms
3. Threshold-based matching
4. Multiple face comparison
5. Match confidence calculation

Author: Face Recognition System
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.spatial.distance import euclidean, cosine
from scipy.special import softmax
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimilarityMetrics:
    """Calculate similarity metrics between embeddings."""
    
    @staticmethod
    def euclidean_distance(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate Euclidean distance between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Euclidean distance
        """
        distance = euclidean(embedding1, embedding2)
        return float(distance)
    
    @staticmethod
    def cosine_distance(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine distance between two embeddings.
        
        Cosine distance = 1 - cosine_similarity
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine distance (0 to 2, where 0 means identical)
        """
        distance = cosine(embedding1, embedding2)
        return float(distance)
    
    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Cosine similarity ranges from -1 (opposite) to 1 (identical).
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (-1 to 1)
        """
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2) + 1e-8
        )
        return float(np.clip(similarity, -1.0, 1.0))
    
    @staticmethod
    def l2_normalized_euclidean(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate Euclidean distance on L2-normalized embeddings.
        
        For L2-normalized embeddings:
        L2_euclidean = 2 - 2 * cosine_similarity
        
        Args:
            embedding1: First embedding (should be L2-normalized)
            embedding2: Second embedding (should be L2-normalized)
            
        Returns:
            L2 Euclidean distance
        """
        # Ensure embeddings are L2-normalized
        emb1_norm = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        emb2_norm = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        
        distance = euclidean(emb1_norm, emb2_norm)
        return float(distance)
    
    @staticmethod
    def batch_distances(
        embedding: np.ndarray,
        embeddings: np.ndarray,
        metric: str = "euclidean"
    ) -> np.ndarray:
        """
        Calculate distances between one embedding and multiple embeddings.
        
        Args:
            embedding: Single embedding (embedding_dim,)
            embeddings: Multiple embeddings (n_embeddings, embedding_dim)
            metric: Distance metric ('euclidean', 'cosine', 'l2_euclidean')
            
        Returns:
            Array of distances (n_embeddings,)
        """
        n = embeddings.shape[0]
        distances = np.zeros(n)
        
        for i in range(n):
            if metric == "euclidean":
                distances[i] = SimilarityMetrics.euclidean_distance(embedding, embeddings[i])
            elif metric == "cosine":
                distances[i] = SimilarityMetrics.cosine_distance(embedding, embeddings[i])
            elif metric == "l2_euclidean":
                distances[i] = SimilarityMetrics.l2_normalized_euclidean(embedding, embeddings[i])
        
        return distances

    @staticmethod
    def batch_cosine_similarities(
        embedding: np.ndarray,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarities between one embedding and multiple embeddings.
        
        Args:
            embedding: Single embedding (embedding_dim,)
            embeddings: Multiple embeddings (n_embeddings, embedding_dim)
            
        Returns:
            Array of similarities (n_embeddings,) ranging from -1 to 1
        """
        n = embeddings.shape[0]
        similarities = np.zeros(n)
        
        for i in range(n):
            similarities[i] = SimilarityMetrics.cosine_similarity(embedding, embeddings[i])
        
        return similarities


class FaceMatcher:
    """
    Main face matching class with configurable thresholds.
    """
    
    def __init__(
        self,
        distance_metric: str = "euclidean",
        threshold: float = 0.6,
        confidence_metric: str = "distance_based"
    ):
        """
        Initialize face matcher.
        
        Args:
            distance_metric: 'euclidean', 'cosine', or 'l2_euclidean'
            threshold: Distance threshold for matching (lower = stricter)
            confidence_metric: How to calculate confidence ('distance_based', 'softmax')
        """
        self.distance_metric = distance_metric
        self.threshold = threshold
        self.confidence_metric = confidence_metric
        
        # Recommended thresholds for different metrics
        if distance_metric == "euclidean":
            self.threshold = threshold if threshold > 0.1 else 0.6
            logger.info(f"[v0] FaceMatcher using Euclidean distance with threshold: {self.threshold}")
        elif distance_metric == "cosine":
            self.threshold = threshold if threshold < 1.0 else 0.35
            logger.info(f"[v0] FaceMatcher using Cosine distance with threshold: {self.threshold}")
        elif distance_metric == "l2_euclidean":
            self.threshold = threshold if threshold > 0.1 else 0.6
            logger.info(f"[v0] FaceMatcher using L2 Euclidean distance with threshold: {self.threshold}")
    
    def compare_faces(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> Dict:
        """
        Compare two faces and determine if they match.
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Dictionary with match result and confidence
        """
        # Calculate distance
        distance = SimilarityMetrics.batch_distances(
            embedding1,
            embedding2.reshape(1, -1),
            metric=self.distance_metric
        )[0]
        
        # Determine if match
        is_match = distance <= self.threshold
        
        # Calculate confidence
        confidence = self._calculate_confidence(distance)
        
        result = {
            "is_match": is_match,
            "distance": float(distance),
            "threshold": self.threshold,
            "confidence": float(confidence),
            "metric": self.distance_metric
        }
        
        logger.info(f"[v0] Face comparison: distance={distance:.4f}, is_match={is_match}, confidence={confidence:.2f}")
        return result
    
    def find_matches(
        self,
        test_embedding: np.ndarray,
        reference_embeddings: Dict[int, List[np.ndarray]],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find matching faces in a database.
        
        Args:
            test_embedding: Embedding to match
            reference_embeddings: Dict mapping person_id to list of embeddings
            top_k: Return top K matches
            
        Returns:
            Sorted list of matches with person info
        """
        matches = []
        
        for person_id, embeddings in reference_embeddings.items():
            # Calculate distance to all embeddings of this person
            embeddings_array = np.array(embeddings)
            distances = SimilarityMetrics.batch_distances(
                test_embedding,
                embeddings_array,
                metric=self.distance_metric
            )
            
            # Get best match for this person
            best_distance = np.min(distances)
            best_idx = np.argmin(distances)
            
            # Check if within threshold
            if best_distance <= self.threshold:
                confidence = self._calculate_confidence(best_distance)
                
                matches.append({
                    "person_id": person_id,
                    "distance": float(best_distance),
                    "confidence": float(confidence),
                    "best_match_index": int(best_idx),
                    "is_match": True
                })
        
        # Sort by distance (ascending) or confidence (descending)
        matches.sort(key=lambda x: x["distance"])
        
        logger.info(f"[v0] Found {len(matches)} matches. Top {min(top_k, len(matches))} returned")
        return matches[:top_k]

    def find_matches_by_cosine_similarity(
        self,
        test_embedding: np.ndarray,
        reference_embeddings: Dict[int, List[np.ndarray]],
        threshold: float = 0.65,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find matching faces using cosine similarity (better for normalized embeddings).
        
        Args:
            test_embedding: Embedding to match
            reference_embeddings: Dict mapping person_id to list of embeddings
            threshold: Minimum cosine similarity to consider a match (0.6-0.7 recommended)
            top_k: Return top K matches
            
        Returns:
            Sorted list of matches with person info (highest similarity first)
        """
        matches = []
        
        for person_id, embeddings in reference_embeddings.items():
            # Calculate cosine similarity to all embeddings of this person
            embeddings_array = np.array(embeddings)
            similarities = SimilarityMetrics.batch_cosine_similarities(
                test_embedding,
                embeddings_array
            )
            
            # Get best match for this person (highest similarity)
            best_similarity = np.max(similarities)
            best_idx = np.argmax(similarities)
            
            # Check if within threshold
            if best_similarity >= threshold:
                matches.append({
                    "person_id": person_id,
                    "similarity": float(best_similarity),
                    "confidence": float(best_similarity),  # Similarity IS the confidence
                    "best_match_index": int(best_idx),
                    "is_match": True
                })
        
        # Sort by similarity (descending - highest first)
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        logger.info(f"[v0] Found {len(matches)} matches using cosine similarity. Top {min(top_k, len(matches))} returned")
        return matches[:top_k]
    
    def compare_face_to_group(
        self,
        test_embedding: np.ndarray,
        embeddings: np.ndarray,
        person_ids: Optional[np.ndarray] = None
    ) -> Tuple[List[Dict], float]:
        """
        Compare one face embedding to a group of embeddings.
        
        Args:
            test_embedding: Test embedding
            embeddings: Array of reference embeddings (n, embedding_dim)
            person_ids: Optional person IDs corresponding to embeddings
            
        Returns:
            Tuple of (list of matches, average confidence)
        """
        distances = SimilarityMetrics.batch_distances(
            test_embedding,
            embeddings,
            metric=self.distance_metric
        )
        
        matches = []
        total_confidence = 0.0
        match_count = 0
        
        for i, distance in enumerate(distances):
            if distance <= self.threshold:
                confidence = self._calculate_confidence(distance)
                person_id = person_ids[i] if person_ids is not None else -1
                
                matches.append({
                    "index": i,
                    "person_id": int(person_id),
                    "distance": float(distance),
                    "confidence": float(confidence)
                })
                
                total_confidence += confidence
                match_count += 1
        
        avg_confidence = total_confidence / len(distances) if len(distances) > 0 else 0.0
        
        logger.info(f"[v0] Compared to {len(embeddings)} faces. Found {match_count} matches")
        return matches, avg_confidence
    
    def _calculate_confidence(self, distance: float) -> float:
        """
        Calculate confidence score from distance.
        
        Args:
            distance: Distance value
            
        Returns:
            Confidence score (0 to 1)
        """
        if self.confidence_metric == "distance_based":
            # Normalize distance to confidence
            if self.distance_metric in ["euclidean", "l2_euclidean"]:
                # For Euclidean: lower distance = higher confidence
                confidence = max(0.0, 1.0 - (distance / (self.threshold * 2)))
            else:  # cosine
                # For cosine: distance ranges 0-2, where 0 is identical
                confidence = max(0.0, 1.0 - (distance / (self.threshold * 2)))
        
        elif self.confidence_metric == "softmax":
            # Use softmax for normalized probabilities
            confidence = 1.0 / (1.0 + np.exp(distance))
        
        else:
            confidence = max(0.0, 1.0 - (distance / self.threshold))
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    def get_best_match(
        self,
        test_embedding: np.ndarray,
        reference_embeddings: Dict[int, List[np.ndarray]]
    ) -> Optional[Dict]:
        """
        Get the single best match.
        
        Args:
            test_embedding: Test embedding
            reference_embeddings: Reference embeddings by person
            
        Returns:
            Best match dictionary or None
        """
        matches = self.find_matches(test_embedding, reference_embeddings, top_k=1)
        
        if matches:
            logger.info(f"[v0] Best match: person_id={matches[0]['person_id']}, distance={matches[0]['distance']:.4f}")
            return matches[0]
        
        logger.info("[v0] No matches found")
        return None


class MultiFrameFaceMatching:
    """
    Match faces using multiple frames for improved accuracy.
    """
    
    def __init__(self, matcher: FaceMatcher):
        """
        Initialize multi-frame matcher.
        
        Args:
            matcher: FaceMatcher instance
        """
        self.matcher = matcher
        logger.info("[v0] MultiFrameFaceMatching initialized")
    
    def aggregate_embeddings(
        self,
        embeddings: List[np.ndarray],
        method: str = "mean"
    ) -> np.ndarray:
        """
        Aggregate multiple embeddings into a single embedding.
        
        Args:
            embeddings: List of embeddings
            method: 'mean', 'median', or 'l2_normalize_then_mean'
            
        Returns:
            Aggregated embedding
        """
        embeddings_array = np.array(embeddings)
        
        if method == "mean":
            aggregated = np.mean(embeddings_array, axis=0)
        elif method == "median":
            aggregated = np.median(embeddings_array, axis=0)
        elif method == "l2_normalize_then_mean":
            # L2 normalize each embedding first, then average
            normalized = embeddings_array / (np.linalg.norm(embeddings_array, axis=1, keepdims=True) + 1e-8)
            aggregated = np.mean(normalized, axis=0)
        else:
            aggregated = np.mean(embeddings_array, axis=0)
        
        # Re-normalize the aggregated embedding
        aggregated = aggregated / (np.linalg.norm(aggregated) + 1e-8)
        
        logger.info(f"[v0] Aggregated {len(embeddings)} embeddings using {method} method")
        return aggregated
    
    def match_with_multiple_frames(
        self,
        test_embeddings: List[np.ndarray],
        reference_embeddings: Dict[int, List[np.ndarray]],
        aggregation_method: str = "mean"
    ) -> Dict:
        """
        Match using multiple test frames.
        
        Args:
            test_embeddings: List of test embeddings
            reference_embeddings: Reference embeddings by person
            aggregation_method: How to aggregate embeddings
            
        Returns:
            Match result
        """
        # Aggregate test embeddings
        aggregated_test = self.aggregate_embeddings(test_embeddings, aggregation_method)
        
        # Find best match
        best_match = self.matcher.get_best_match(aggregated_test, reference_embeddings)
        
        if best_match:
            best_match["num_frames"] = len(test_embeddings)
            logger.info(f"[v0] Multi-frame match found using {len(test_embeddings)} frames")
        
        return best_match


if __name__ == "__main__":
    # Example usage
    logger.info("[v0] Creating sample embeddings...")
    
    # Create sample embeddings
    embedding1 = np.random.randn(128)
    embedding1 /= np.linalg.norm(embedding1)  # L2 normalize
    
    embedding2 = embedding1 + np.random.randn(128) * 0.1  # Similar
    embedding2 /= np.linalg.norm(embedding2)
    
    embedding3 = np.random.randn(128)  # Different
    embedding3 /= np.linalg.norm(embedding3)
    
    # Test similarity metrics
    print("\nSimilarity Metrics:")
    print(f"Euclidean distance (same): {SimilarityMetrics.euclidean_distance(embedding1, embedding2):.4f}")
    print(f"Euclidean distance (diff): {SimilarityMetrics.euclidean_distance(embedding1, embedding3):.4f}")
    print(f"Cosine similarity (same): {SimilarityMetrics.cosine_similarity(embedding1, embedding2):.4f}")
    print(f"Cosine similarity (diff): {SimilarityMetrics.cosine_similarity(embedding1, embedding3):.4f}")
    
    # Test face matcher
    matcher = FaceMatcher(distance_metric="euclidean", threshold=0.6)
    result = matcher.compare_faces(embedding1, embedding2)
    print(f"\nFace Comparison Result: {result}")
