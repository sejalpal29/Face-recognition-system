"""
Face Detection Module

Implements multiple face detection methods:
1. Haar Cascade Classifiers (fast, traditional approach)
2. Deep Learning-based CNN detector (more accurate)

Supports detecting multiple faces in a single image and handles
various pose angles and lighting conditions.

Author: Face Recognition System
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceDetector:
    """Base class for face detection."""
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces in an image.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            List of dictionaries containing face bounding boxes and confidence
        """
        raise NotImplementedError


class HaarCascadeDetector(FaceDetector):
    """
    Face detection using Haar Cascade Classifiers.
    
    Fast and suitable for real-time applications, but may have
    more false positives than deep learning methods.
    """
    
    def __init__(self, scale_factor: float = 1.1, min_neighbors: int = 6):
        """
        Initialize Haar Cascade detector.
        
        Args:
            scale_factor: Image pyramid scale factor (1.01-1.4)
            min_neighbors: Number of neighbors each candidate should retain (4-8)
        """
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.cascade = cv2.CascadeClassifier(cascade_path)
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        logger.info(f"[v0] Haar Cascade detector initialized with scale_factor={scale_factor}, min_neighbors={min_neighbors}")
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces using Haar Cascade.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            List of detected faces with bounding boxes
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        min_size = max(40, min(width, height) // 20)
        max_size = min(max(width, height), max(200, min(width, height)))
        
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=(min_size, min_size),
            maxSize=(max_size, max_size)
        )
        
        results = []
        for (x, y, w, h) in faces:
            if w <= 0 or h <= 0:
                continue
            aspect_ratio = w / float(h)
            if aspect_ratio < 0.4 or aspect_ratio > 2.5:
                continue
            results.append({
                "bbox": (x, y, w, h),
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "confidence": 0.9,
                "method": "haar_cascade"
            })
        
        logger.info(f"[v0] Haar Cascade detected {len(results)} face(s) after filtering")
        return results
        
        results = []
        for (x, y, w, h) in faces:
            results.append({
                "bbox": (x, y, w, h),
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "confidence": 0.9,  # Haar Cascade doesn't provide confidence
                "method": "haar_cascade"
            })
        
        logger.info(f"[v0] Haar Cascade detected {len(results)} faces")
        return results


class CNNFaceDetector(FaceDetector):
    """
    Face detection using Deep Learning (CNN).
    
    More accurate than Haar Cascade but slower.
    Uses OpenCV's DNN module for face detection.
    """

    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize CNN-based detector.
        
        Args:
            confidence_threshold: Confidence threshold for face detection
        """
        self.confidence_threshold = confidence_threshold
        
        model_file = "opencv_face_detector_uint8.pb"
        config_file = "opencv_face_detector.pbtxt"
        
        try:
            self.net = cv2.dnn.readNetFromTensorflow(model_file, config_file)
            logger.info(f"[v0] CNN detector loaded successfully with threshold={confidence_threshold}")
        except Exception:
            logger.warning(f"[v0] CNN detector model files not found. Using Haar Cascade instead")
            self.net = None
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces using CNN.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            List of detected faces with bounding boxes and confidence
        """
        if self.net is None:
            logger.warning("[v0] CNN detector not available, returning empty list")
            return []
        
        height, width = image.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            image,
            1.0,
            (300, 300),
            [104.0, 177.0, 123.0],
            False,
            False
        )
        
        self.net.setInput(blob)
        detections = self.net.forward()
        
        results = []
        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            
            if confidence >= self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                x1, y1, x2, y2 = box.astype("int")
                
                w = x2 - x1
                h = y2 - y1
                
                if w <= 0 or h <= 0:
                    continue
                if w < max(40, width // 30) or h < max(40, height // 30):
                    continue
                aspect_ratio = w / float(h)
                if aspect_ratio < 0.4 or aspect_ratio > 2.5:
                    continue
                
                x1 = max(0, x1)
                y1 = max(0, y1)
                
                results.append({
                    "bbox": (x1, y1, w, h),
                    "x": x1,
                    "y": y1,
                    "width": w,
                    "height": h,
                    "confidence": confidence,
                    "method": "cnn"
                })
        
        logger.info(f"[v0] CNN detector found {len(results)} faces")
        return results


class MultiScaleFaceDetector(FaceDetector):
    """
    Advanced detector using multiple methods for robustness.
    
    Combines results from Haar Cascade and CNN for improved accuracy.
    """
    
    def __init__(self):
        """Initialize multi-scale detector with both methods."""
        self.haar_detector = HaarCascadeDetector()
        self.cnn_detector = CNNFaceDetector()
        logger.info(f"[v0] Multi-scale detector initialized")
    
    def detect_faces(self, image: np.ndarray, use_ensemble: bool = True) -> List[Dict]:
        """
        Detect faces using ensemble of methods.
        
        Args:
            image: Input image (BGR)
            use_ensemble: If True, combines both methods; if False, uses Haar only
            
        Returns:
            List of detected faces
        """
        cnn_results = []
        if self.cnn_detector.net is not None:
            cnn_results = self.cnn_detector.detect_faces(image)
        
        if use_ensemble and cnn_results:
            haar_results = self.haar_detector.detect_faces(image)
            results = self._merge_detections(haar_results, cnn_results)
            logger.info(f"[v0] Ensemble detection merged results: {len(results)}")
        elif cnn_results:
            results = cnn_results
            logger.info(f"[v0] Using CNN-only detection results: {len(results)}")
        else:
            results = self.haar_detector.detect_faces(image)
            logger.info(f"[v0] Using Haar-only detection results: {len(results)}")

        results = [det for det in results if self._is_valid_detection(det, image)]
        results = deduplicate_detections(results, iou_threshold=0.45)
        logger.info(f"[v0] Filtered and deduplicated results: {len(results)}")
        return results
    
    def _is_valid_detection(self, detection: Dict, image: np.ndarray) -> bool:
        x, y, w, h = detection["bbox"]
        height, width = image.shape[:2]
        if w <= 0 or h <= 0:
            return False
        if w < 40 or h < 40:
            return False
        if x < 0 or y < 0 or x + w > width or y + h > height:
            return False
        area = w * h
        image_area = width * height
        if area < max(1600, int(image_area * 0.0015)):
            return False
        aspect_ratio = w / float(h)
        if aspect_ratio < 0.4 or aspect_ratio > 2.5:
            return False
        return True
    
    def _merge_detections(self, detections1: List[Dict], detections2: List[Dict]) -> List[Dict]:
        """
        Merge detections from two methods, removing duplicates.
        
        Args:
            detections1: First set of detections
            detections2: Second set of detections
            
        Returns:
            Merged list of unique detections
        """
        merged = detections1.copy()
        iou_threshold = 0.3
        
        for det2 in detections2:
            is_duplicate = False
            for det1 in detections1:
                iou = self._calculate_iou(det1["bbox"], det2["bbox"])
                if iou > iou_threshold:
                    is_duplicate = True
                    # Keep the detection with higher confidence
                    if det2["confidence"] > det1["confidence"]:
                        merged.remove(det1)
                        merged.append(det2)
                    break
            
            if not is_duplicate:
                merged.append(det2)
        
        return merged
    
    def _calculate_iou(self, box1: Tuple, box2: Tuple) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            box1: (x, y, width, height)
            box2: (x, y, width, height)
            
        Returns:
            IoU value between 0 and 1
        """
        x1_1, y1_1, w1, h1 = box1
        x2_1, y2_1 = x1_1 + w1, y1_1 + h1
        
        x1_2, y1_2, w2, h2 = box2
        x2_2, y2_2 = x1_2 + w2, y1_2 + h2
        
        # Calculate intersection
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = (w1 * h1) + (w2 * h2) - intersection
        
        return intersection / union if union > 0 else 0.0


def _calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Calculate IoU between two bounding boxes.
    """
    x1_1, y1_1, w1, h1 = box1
    x2_1, y2_1 = x1_1 + w1, y1_1 + h1

    x1_2, y1_2, w2, h2 = box2
    x2_2, y2_2 = x1_2 + w2, y1_2 + h2

    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection = (x_right - x_left) * (y_bottom - y_top)
    union = (w1 * h1) + (w2 * h2) - intersection
    return intersection / union if union > 0 else 0.0


def deduplicate_detections(detections: List[Dict], iou_threshold: float = 0.4) -> List[Dict]:
    """
    Remove duplicate face detections that overlap heavily.

    Keeps the highest-confidence bounding box and discards overlapping duplicates.
    """
    if not detections:
        return []

    sorted_detections = sorted(detections, key=lambda d: d.get("confidence", 0.0), reverse=True)
    deduped: List[Dict] = []

    for det in sorted_detections:
        bbox = det["bbox"]
        if any(_calculate_iou(bbox, existing["bbox"]) > iou_threshold for existing in deduped):
            continue
        deduped.append(det)

    logger.info(f"[v0] Deduplicated {len(detections)} detections to {len(deduped)}")
    return deduped


def extract_face_regions(image: np.ndarray, detections: List[Dict]) -> List[np.ndarray]:
    """
    Extract face regions from image based on detections.
    
    Args:
        image: Input image
        detections: List of face detections
        
    Returns:
        List of face cropped images
    """
    faces = []
    for det in detections:
        x, y, w, h = det["bbox"]
        face = image[y:y+h, x:x+w]
        faces.append(face)
    
    logger.info(f"[v0] Extracted {len(faces)} face regions")
    return faces


if __name__ == "__main__":
    # Example usage
    detector = MultiScaleFaceDetector()
    
    # Load image
    image = cv2.imread("sample_image.jpg")
    
    if image is not None:
        # Detect faces
        detections = detector.detect_faces(image)
        
        print(f"Found {len(detections)} faces:")
        for i, det in enumerate(detections):
            print(f"  Face {i+1}: {det['bbox']}, confidence: {det['confidence']:.2f}")
        
        # Extract faces
        faces = extract_face_regions(image, detections)
