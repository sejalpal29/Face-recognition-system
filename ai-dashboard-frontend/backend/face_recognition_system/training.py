"""
Training Module for Face Recognition Model

This module implements:
1. Triplet Loss - For metric learning with anchor-positive-negative triplets
2. Contrastive Loss - For learning discriminative embeddings
3. Complete training loop with validation
4. Dataset handling
5. Model evaluation metrics

Author: Face Recognition System
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, List, Dict, Optional
import logging
from tqdm import tqdm
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TripletLoss(nn.Module):
    """
    Triplet Loss for metric learning.
    
    Loss = max(d(anchor, positive) - d(anchor, negative) + margin, 0)
    
    Where:
    - d() is distance (usually L2 distance)
    - margin is a hyperparameter (typically 0.2 to 1.0)
    
    Goal: Make positive pair (anchor, positive) closer and
          negative pair (anchor, negative) farther apart.
    """
    
    def __init__(self, margin: float = 0.5, distance_metric: str = "euclidean"):
        """
        Initialize Triplet Loss.
        
        Args:
            margin: Margin for the loss function
            distance_metric: 'euclidean' or 'cosine'
        """
        super(TripletLoss, self).__init__()
        self.margin = margin
        self.distance_metric = distance_metric
        logger.info(f"[v0] TripletLoss initialized with margin={margin}, metric={distance_metric}")
    
    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate triplet loss.
        
        Args:
            anchor: Anchor embeddings (batch_size, embedding_dim)
            positive: Positive embeddings (batch_size, embedding_dim)
            negative: Negative embeddings (batch_size, embedding_dim)
            
        Returns:
            Loss value
        """
        if self.distance_metric == "euclidean":
            # Euclidean distance
            pos_distance = torch.norm(anchor - positive, p=2, dim=1)
            neg_distance = torch.norm(anchor - negative, p=2, dim=1)
        else:  # cosine
            # Cosine distance (1 - cosine similarity)
            pos_distance = 1 - torch.nn.functional.cosine_similarity(anchor, positive, dim=1)
            neg_distance = 1 - torch.nn.functional.cosine_similarity(anchor, negative, dim=1)
        
        # Triplet loss
        loss = torch.clamp(pos_distance - neg_distance + self.margin, min=0.0)
        
        return torch.mean(loss)


class ContrastiveLoss(nn.Module):
    """
    Contrastive Loss for learning discriminative embeddings.
    
    Loss = (1-y) * 0.5 * d^2 + y * 0.5 * max(margin - d, 0)^2
    
    Where:
    - y=0 for similar pairs (same person)
    - y=1 for dissimilar pairs (different people)
    - d is the distance between embeddings
    - margin is the threshold distance
    
    Objective:
    - Minimize distance for similar pairs
    - Maximize distance for dissimilar pairs (but only if < margin)
    """
    
    def __init__(self, margin: float = 1.0, distance_metric: str = "euclidean"):
        """
        Initialize Contrastive Loss.
        
        Args:
            margin: Margin for dissimilar pairs
            distance_metric: 'euclidean' or 'cosine'
        """
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
        self.distance_metric = distance_metric
        logger.info(f"[v0] ContrastiveLoss initialized with margin={margin}, metric={distance_metric}")
    
    def forward(
        self,
        embedding1: torch.Tensor,
        embedding2: torch.Tensor,
        label: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate contrastive loss.
        
        Args:
            embedding1: First set of embeddings (batch_size, embedding_dim)
            embedding2: Second set of embeddings (batch_size, embedding_dim)
            label: Labels (0=same person, 1=different person)
            
        Returns:
            Loss value
        """
        if self.distance_metric == "euclidean":
            # Euclidean distance
            distance = torch.norm(embedding1 - embedding2, p=2, dim=1)
        else:  # cosine
            # Cosine distance
            distance = 1 - torch.nn.functional.cosine_similarity(embedding1, embedding2, dim=1)
        
        # Contrastive loss formula
        # For similar pairs (label=0): minimize distance
        # For dissimilar pairs (label=1): maximize distance (but penalize if < margin)
        similar_loss = (1 - label) * 0.5 * distance ** 2
        dissimilar_loss = label * 0.5 * torch.clamp(self.margin - distance, min=0.0) ** 2
        
        loss = similar_loss + dissimilar_loss
        
        return torch.mean(loss)


class FaceDataset(Dataset):
    """
    Dataset for face recognition training.
    
    Supports both triplet and contrastive learning formats.
    """
    
    def __init__(
        self,
        image_paths: List[str],
        labels: List[int],
        transform=None,
        mode: str = "triplet"
    ):
        """
        Initialize dataset.
        
        Args:
            image_paths: List of image file paths
            labels: List of labels (person IDs)
            transform: Image transformations
            mode: 'triplet' or 'contrastive'
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.mode = mode
        
        # Group images by label for triplet sampling
        self.label_to_indices = {}
        for idx, label in enumerate(labels):
            if label not in self.label_to_indices:
                self.label_to_indices[label] = []
            self.label_to_indices[label].append(idx)
        
        logger.info(f"[v0] FaceDataset initialized with {len(image_paths)} images, {len(set(labels))} unique persons")
    
    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Tuple:
        """
        Get item from dataset.
        
        Args:
            idx: Index
            
        Returns:
            Tuple of (images, labels) depending on mode
        """
        import cv2
        
        # Load anchor image
        anchor_path = self.image_paths[idx]
        anchor_image = cv2.imread(anchor_path)
        anchor_label = self.labels[idx]
        
        if self.mode == "triplet":
            # Select positive (same label)
            positive_indices = [i for i in self.label_to_indices[anchor_label] if i != idx]
            if len(positive_indices) == 0:
                positive_idx = idx
            else:
                positive_idx = np.random.choice(positive_indices)
            
            positive_path = self.image_paths[positive_idx]
            positive_image = cv2.imread(positive_path)
            
            # Select negative (different label)
            negative_label = np.random.choice([l for l in self.label_to_indices.keys() if l != anchor_label])
            negative_idx = np.random.choice(self.label_to_indices[negative_label])
            negative_path = self.image_paths[negative_idx]
            negative_image = cv2.imread(negative_path)
            
            # Apply transforms
            if self.transform:
                anchor_image = self.transform(anchor_image)
                positive_image = self.transform(positive_image)
                negative_image = self.transform(negative_image)
            
            return anchor_image, positive_image, negative_image
        
        else:  # contrastive mode
            # Select another image
            if np.random.rand() > 0.5:
                # Positive pair (same label)
                other_indices = [i for i in self.label_to_indices[anchor_label] if i != idx]
                if len(other_indices) == 0:
                    other_idx = idx
                else:
                    other_idx = np.random.choice(other_indices)
                label = 0
            else:
                # Negative pair (different label)
                other_label = np.random.choice([l for l in self.label_to_indices.keys() if l != anchor_label])
                other_idx = np.random.choice(self.label_to_indices[other_label])
                label = 1
            
            other_path = self.image_paths[other_idx]
            other_image = cv2.imread(other_path)
            
            # Apply transforms
            if self.transform:
                anchor_image = self.transform(anchor_image)
                other_image = self.transform(other_image)
            
            return anchor_image, other_image, label


class FaceRecognitionTrainer:
    """Main trainer class for face recognition model."""
    
    def __init__(
        self,
        model: nn.Module,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        learning_rate: float = 0.001,
        loss_type: str = "triplet"
    ):
        """
        Initialize trainer.
        
        Args:
            model: PyTorch model
            device: Device to train on ('cuda' or 'cpu')
            learning_rate: Learning rate for optimizer
            loss_type: 'triplet' or 'contrastive'
        """
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate
        self.loss_type = loss_type
        
        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Loss function
        if loss_type == "triplet":
            self.loss_fn = TripletLoss(margin=0.5)
        else:
            self.loss_fn = ContrastiveLoss(margin=1.0)
        
        self.train_losses = []
        self.val_losses = []
        
        logger.info(f"[v0] Trainer initialized on device: {device}, loss_type: {loss_type}")
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
            
        Returns:
            Average loss for the epoch
        """
        self.model.train()
        total_loss = 0.0
        
        pbar = tqdm(train_loader, desc="Training")
        for batch_idx, batch in enumerate(pbar):
            if self.loss_type == "triplet":
                anchor, positive, negative = batch
                anchor = anchor.to(self.device).float()
                positive = positive.to(self.device).float()
                negative = negative.to(self.device).float()
                
                # Forward pass
                anchor_emb = self.model(anchor)
                positive_emb = self.model(positive)
                negative_emb = self.model(negative)
                
                # Calculate loss
                loss = self.loss_fn(anchor_emb, positive_emb, negative_emb)
            
            else:  # contrastive
                img1, img2, label = batch
                img1 = img1.to(self.device).float()
                img2 = img2.to(self.device).float()
                label = label.to(self.device).float()
                
                # Forward pass
                emb1 = self.model(img1)
                emb2 = self.model(img2)
                
                # Calculate loss
                loss = self.loss_fn(emb1, emb2, label)
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            pbar.set_postfix({"loss": loss.item()})
        
        avg_loss = total_loss / len(train_loader)
        self.train_losses.append(avg_loss)
        logger.info(f"[v0] Epoch average loss: {avg_loss:.4f}")
        
        return avg_loss
    
    def validate(self, val_loader: DataLoader) -> float:
        """
        Validate model.
        
        Args:
            val_loader: Validation data loader
            
        Returns:
            Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                if self.loss_type == "triplet":
                    anchor, positive, negative = batch
                    anchor = anchor.to(self.device).float()
                    positive = positive.to(self.device).float()
                    negative = negative.to(self.device).float()
                    
                    anchor_emb = self.model(anchor)
                    positive_emb = self.model(positive)
                    negative_emb = self.model(negative)
                    
                    loss = self.loss_fn(anchor_emb, positive_emb, negative_emb)
                
                else:  # contrastive
                    img1, img2, label = batch
                    img1 = img1.to(self.device).float()
                    img2 = img2.to(self.device).float()
                    label = label.to(self.device).float()
                    
                    emb1 = self.model(img1)
                    emb2 = self.model(img2)
                    
                    loss = self.loss_fn(emb1, emb2, label)
                
                total_loss += loss.item()
        
        avg_loss = total_loss / len(val_loader)
        self.val_losses.append(avg_loss)
        logger.info(f"[v0] Validation loss: {avg_loss:.4f}")
        
        return avg_loss
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 20,
        save_path: Optional[str] = None
    ):
        """
        Train model for multiple epochs.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of epochs to train
            save_path: Path to save best model
        """
        best_val_loss = float('inf')
        
        for epoch in range(num_epochs):
            logger.info(f"\n[v0] Epoch {epoch+1}/{num_epochs}")
            
            # Train
            train_loss = self.train_epoch(train_loader)
            
            # Validate
            val_loss = self.validate(val_loader)
            
            # Save best model
            if save_path and val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(self.model.state_dict(), save_path)
                logger.info(f"[v0] Model saved to {save_path}")
    
    def save_checkpoint(self, checkpoint_path: str):
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, checkpoint_path)
        logger.info(f"[v0] Checkpoint saved to {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.train_losses = checkpoint['train_losses']
        self.val_losses = checkpoint['val_losses']
        logger.info(f"[v0] Checkpoint loaded from {checkpoint_path}")
