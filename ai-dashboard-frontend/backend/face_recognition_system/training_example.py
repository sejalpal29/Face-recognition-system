"""
Complete Training Script Example

This script demonstrates how to train the face recognition model
from scratch using Triplet Loss or Contrastive Loss.

Usage:
    python train_example.py --loss_type triplet --epochs 20 --batch_size 32

Author: Face Recognition System
"""

import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
import numpy as np
import logging
from pathlib import Path
import json
from tqdm import tqdm

from cnn_architecture import FaceEmbeddingCNN, EmbeddingModel
from training import FaceRecognitionTrainer, TripletLoss, ContrastiveLoss, FaceDataset
from preprocessing import ImagePreprocessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Face Recognition Model"
    )
    
    parser.add_argument(
        "--loss_type",
        type=str,
        choices=["triplet", "contrastive"],
        default="triplet",
        help="Type of loss function to use"
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Number of training epochs"
    )
    
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for training"
    )
    
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=0.001,
        help="Learning rate for optimizer"
    )
    
    parser.add_argument(
        "--embedding_dim",
        type=int,
        default=128,
        help="Dimension of embeddings"
    )
    
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="./face_dataset",
        help="Path to face dataset directory"
    )
    
    parser.add_argument(
        "--save_path",
        type=str,
        default="./face_embedding_model.pth",
        help="Path to save trained model"
    )
    
    parser.add_argument(
        "--checkpoint_path",
        type=str,
        default=None,
        help="Path to load checkpoint (for resuming training)"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        choices=["cpu", "cuda"],
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to train on"
    )
    
    parser.add_argument(
        "--num_residual_blocks",
        type=int,
        default=2,
        help="Number of residual blocks per stage"
    )
    
    return parser.parse_args()


def prepare_dataset(dataset_path: str, batch_size: int = 32, loss_type: str = "triplet"):
    """
    Prepare training and validation datasets.
    
    Dataset directory structure should be:
    dataset/
        person_1/
            face_001.jpg
            face_002.jpg
        person_2/
            face_001.jpg
            ...
    """
    logger.info(f"[v0] Loading dataset from {dataset_path}")
    
    # Scan dataset directory
    dataset_path = Path(dataset_path)
    image_paths = []
    labels = []
    label_map = {}
    
    for label, person_dir in enumerate(sorted(dataset_path.iterdir())):
        if person_dir.is_dir():
            label_map[person_dir.name] = label
            
            for image_file in person_dir.glob("*.jpg") + person_dir.glob("*.png"):
                image_paths.append(str(image_file))
                labels.append(label)
    
    if len(image_paths) == 0:
        logger.error(f"[v0] No images found in {dataset_path}")
        logger.info("[v0] Dataset structure should be:")
        logger.info("    dataset/")
        logger.info("        person_1/")
        logger.info("            face_001.jpg")
        logger.info("        person_2/")
        logger.info("            face_002.jpg")
        raise ValueError("No dataset found")
    
    logger.info(f"[v0] Found {len(image_paths)} images from {len(set(labels))} persons")
    
    # Create dataset
    dataset = FaceDataset(
        image_paths=image_paths,
        labels=labels,
        transform=None,  # Add transforms if needed
        mode=loss_type
    )
    
    # Split into train and validation
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    
    logger.info(f"[v0] Train set: {len(train_dataset)} samples")
    logger.info(f"[v0] Validation set: {len(val_dataset)} samples")
    logger.info(f"[v0] Label mapping: {label_map}")
    
    return train_loader, val_loader, label_map


def build_model(embedding_dim: int, num_residual_blocks: int, device: str):
    """Build and initialize the model."""
    logger.info(f"[v0] Building FaceEmbeddingCNN...")
    
    model = FaceEmbeddingCNN(
        input_size=(224, 224),
        embedding_dim=embedding_dim,
        num_residual_blocks=num_residual_blocks,
        use_dropout=True,
        dropout_rate=0.5
    )
    
    model = model.to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    logger.info(f"[v0] Model parameters:")
    logger.info(f"    Total: {total_params:,}")
    logger.info(f"    Trainable: {trainable_params:,}")
    
    return model


def train(args):
    """Main training function."""
    logger.info("[v0] ========== Face Recognition Training ==========")
    logger.info(f"[v0] Loss Type: {args.loss_type}")
    logger.info(f"[v0] Epochs: {args.epochs}")
    logger.info(f"[v0] Batch Size: {args.batch_size}")
    logger.info(f"[v0] Learning Rate: {args.learning_rate}")
    logger.info(f"[v0] Embedding Dimension: {args.embedding_dim}")
    logger.info(f"[v0] Device: {args.device}")
    
    # Prepare dataset
    train_loader, val_loader, label_map = prepare_dataset(
        args.dataset_path,
        args.batch_size,
        args.loss_type
    )
    
    # Build model
    model = build_model(
        args.embedding_dim,
        args.num_residual_blocks,
        args.device
    )
    
    # Create trainer
    trainer = FaceRecognitionTrainer(
        model=model,
        device=args.device,
        learning_rate=args.learning_rate,
        loss_type=args.loss_type
    )
    
    # Load checkpoint if provided
    if args.checkpoint_path:
        logger.info(f"[v0] Loading checkpoint from {args.checkpoint_path}")
        trainer.load_checkpoint(args.checkpoint_path)
    
    # Train model
    logger.info("[v0] Starting training...")
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=args.epochs,
        save_path=args.save_path
    )
    
    logger.info(f"[v0] Training completed!")
    logger.info(f"[v0] Model saved to {args.save_path}")
    
    # Save label mapping
    label_map_path = Path(args.save_path).parent / "label_map.json"
    with open(label_map_path, 'w') as f:
        json.dump(label_map, f, indent=2)
    logger.info(f"[v0] Label mapping saved to {label_map_path}")
    
    # Plot training history
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 6))
        plt.plot(trainer.train_losses, label='Training Loss')
        plt.plot(trainer.val_losses, label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title(f'Training History ({args.loss_type} Loss)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        history_path = Path(args.save_path).parent / "training_history.png"
        plt.savefig(history_path)
        logger.info(f"[v0] Training history saved to {history_path}")
        
        plt.close()
    except ImportError:
        logger.warning("[v0] Matplotlib not available. Skipping history plot.")


def evaluate(model_path: str, val_loader: DataLoader, device: str):
    """Evaluate trained model."""
    logger.info("[v0] Evaluating model...")
    
    # Load model
    model = FaceEmbeddingCNN(embedding_dim=128)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    
    # Generate embeddings for validation set
    all_embeddings = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(val_loader):
            images, labels = batch
            images = images.to(device).float()
            
            embeddings = model(images)
            all_embeddings.append(embeddings.cpu().numpy())
            all_labels.append(labels.numpy())
    
    all_embeddings = np.vstack(all_embeddings)
    all_labels = np.hstack(all_labels)
    
    # Calculate statistics
    logger.info(f"[v0] Embedding statistics:")
    logger.info(f"    Shape: {all_embeddings.shape}")
    logger.info(f"    Mean norm: {np.mean(np.linalg.norm(all_embeddings, axis=1)):.4f}")
    logger.info(f"    Std norm: {np.std(np.linalg.norm(all_embeddings, axis=1)):.4f}")
    
    logger.info("[v0] Evaluation completed!")


if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        train(args)
    except KeyboardInterrupt:
        logger.info("[v0] Training interrupted by user")
    except Exception as e:
        logger.error(f"[v0] Error during training: {str(e)}", exc_info=True)
        raise
