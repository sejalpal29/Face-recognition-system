"""
Face Recognition Image Preprocessing Module

This module handles all image preprocessing tasks including:
- Grayscale conversion
- Normalization
- Resizing
- Face alignment
- Histogram equalization for lighting variations

Author: Face Recognition System
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Handles all image preprocessing operations for face recognition."""
    
    def __init__(self, target_size: Tuple[int, int] = (160, 160)):
        """
        Initialize the preprocessor.
        
        Args:
            target_size: Target image size (height, width). Default: (160, 160)
        """
        self.target_size = target_size
        logger.info(f"[v0] ImagePreprocessor initialized with target size: {target_size}")
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load an image from file path.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Image as numpy array or None if loading fails
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"[v0] Failed to load image from {image_path}")
                return None
            logger.info(f"[v0] Successfully loaded image: {image_path}")
            return image
        except Exception as e:
            logger.error(f"[v0] Error loading image: {str(e)}")
            return None
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert BGR image to grayscale.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Grayscale image
        """
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        logger.info(f"[v0] Converted image to grayscale. Shape: {grayscale.shape}")
        return grayscale
    
    def resize_image(self, image: np.ndarray, size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Resize image to target size.
        
        Args:
            image: Input image
            size: Target size (width, height). If None, uses self.target_size
            
        Returns:
            Resized image
        """
        if size is None:
            size = (self.target_size[1], self.target_size[0])  # OpenCV uses (width, height)
        
        resized = cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)
        logger.info(f"[v0] Resized image to {size}")
        return resized
    
    def normalize_image(self, image: np.ndarray, method: str = "zscore") -> np.ndarray:
        """
        Normalize image pixel values.
        
        Args:
            image: Input image
            method: Normalization method - 'zscore' or 'minmax'
            
        Returns:
            Normalized image
        """
        image = image.astype(np.float32)
        
        if method == "zscore":
            # Z-score normalization: (x - mean) / std
            mean = np.mean(image)
            std = np.std(image)
            if std != 0:
                normalized = (image - mean) / std
            else:
                normalized = image
            logger.info(f"[v0] Applied Z-score normalization (mean: {mean:.2f}, std: {std:.2f})")
        
        elif method == "minmax":
            # Min-max normalization: (x - min) / (max - min)
            min_val = np.min(image)
            max_val = np.max(image)
            if max_val - min_val != 0:
                normalized = (image - min_val) / (max_val - min_val)
            else:
                normalized = image
            logger.info(f"[v0] Applied Min-Max normalization")
        
        else:
            logger.warning(f"[v0] Unknown normalization method: {method}. Using identity")
            normalized = image / 255.0
        
        return normalized
    
    def histogram_equalization(self, image: np.ndarray, method: str = "clahe") -> np.ndarray:
        """
        Apply histogram equalization to handle lighting variations.
        
        Args:
            image: Input grayscale image
            method: 'standard' or 'clahe' (Contrast Limited Adaptive Histogram Equalization)
            
        Returns:
            Equalized image
        """
        image_uint8 = (image * 255).astype(np.uint8) if image.max() <= 1.0 else image.astype(np.uint8)
        
        if method == "standard":
            equalized = cv2.equalizeHist(image_uint8)
            logger.info(f"[v0] Applied standard histogram equalization")
        
        elif method == "clahe":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            equalized = clahe.apply(image_uint8)
            logger.info(f"[v0] Applied CLAHE histogram equalization")
        
        else:
            logger.warning(f"[v0] Unknown equalization method: {method}")
            equalized = image_uint8
        
        return equalized.astype(np.float32) / 255.0
    
    def align_face(self, image: np.ndarray, landmarks: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Align face using detected landmarks (eye positions).
        
        Args:
            image: Input image
            landmarks: Facial landmarks (optional). If None, simple rotation is applied
            
        Returns:
            Aligned image
        """
        if landmarks is None:
            logger.info(f"[v0] No landmarks provided. Returning image as-is")
            return image
        
        # Simple alignment based on eye positions
        try:
            # Assume landmarks contain left eye and right eye coordinates
            left_eye = landmarks[0]
            right_eye = landmarks[1]
            
            # Calculate angle between eyes
            dY = right_eye[1] - left_eye[1]
            dX = right_eye[0] - left_eye[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # Get image center and rotation matrix
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Apply rotation
            aligned = cv2.warpAffine(image, rotation_matrix, (width, height))
            logger.info(f"[v0] Applied face alignment with rotation angle: {angle:.2f} degrees")
            
            return aligned
        except Exception as e:
            logger.warning(f"[v0] Face alignment failed: {str(e)}. Returning original image")
            return image
    
    def preprocess_face(
        self,
        image: np.ndarray,
        normalize: bool = True,
        equalize: bool = False,
        grayscale: bool = False
    ) -> np.ndarray:
        """
        Full preprocessing pipeline for face image.
        
        Args:
            image: Input image (BGR format from OpenCV)
            normalize: Whether to normalize pixel values
            equalize: Whether to apply histogram equalization (for grayscale only)
            grayscale: Whether to convert to grayscale
            
        Returns:
            Preprocessed image ready for model input (RGB format, CHW layout)
        """
        logger.info(f"[v0] Starting preprocessing pipeline. Input shape: {image.shape}")
        
        # Step 1: Convert BGR to RGB (OpenCV uses BGR by default)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            logger.info(f"[v0] Converted BGR to RGB")
        
        # Step 2: Resize
        image = self.resize_image(image)
        
        # Step 3: Convert to grayscale if requested
        if grayscale:
            image = self.to_grayscale(image)
            # Apply histogram equalization for lighting variations (grayscale only)
            if equalize:
                image = self.histogram_equalization(image)
        else:
            # For RGB images, apply basic brightness/contrast normalization per channel
            if equalize:
                # Apply CLAHE to each channel separately
                channels = []
                for i in range(3):
                    channel = image[:, :, i]
                    channel_eq = self.histogram_equalization(channel, method="clahe")
                    channels.append(channel_eq)
                image = np.stack(channels, axis=2)
                logger.info(f"[v0] Applied CLAHE to RGB channels separately")
        
        # Step 4: Normalize pixel values to [0, 1]
        if normalize:
            image = image.astype(np.float32) / 255.0
            logger.info(f"[v0] Normalized pixel values to [0, 1]")
        
        # Step 5: Convert to CHW format for PyTorch (HWC to CHW)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = np.transpose(image, (2, 0, 1))
            logger.info(f"[v0] Converted to CHW format for PyTorch")
        
        logger.info(f"[v0] Preprocessing complete. Output shape: {image.shape}")
        return image
    
    def batch_preprocess(
        self,
        images: list,
        **kwargs
    ) -> np.ndarray:
        """
        Preprocess a batch of images.
        
        Args:
            images: List of images (numpy arrays or file paths)
            **kwargs: Arguments to pass to preprocess_face
            
        Returns:
            Batch of preprocessed images
        """
        processed_batch = []
        
        for i, img in enumerate(images):
            try:
                if isinstance(img, str):
                    img = self.load_image(img)
                
                if img is not None:
                    processed = self.preprocess_face(img, **kwargs)
                    processed_batch.append(processed)
                    logger.info(f"[v0] Preprocessed image {i+1}/{len(images)}")
            except Exception as e:
                logger.error(f"[v0] Error processing image {i}: {str(e)}")
        
        return np.array(processed_batch) if processed_batch else np.array([])


if __name__ == "__main__":
    # Example usage
    preprocessor = ImagePreprocessor(target_size=(224, 224))
    
    # Load and preprocess an image
    image = cv2.imread("sample_face.jpg")
    if image is not None:
        processed = preprocessor.preprocess_face(image, normalize=True, equalize=True)
        print(f"Preprocessed shape: {processed.shape}")
        print(f"Preprocessed dtype: {processed.dtype}")
        print(f"Value range: [{processed.min():.2f}, {processed.max():.2f}]")
