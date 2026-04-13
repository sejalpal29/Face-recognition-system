"""
Custom Convolutional Neural Network Architecture for Face Recognition

This module implements a custom CNN designed specifically for generating
fixed-length facial embeddings. The architecture includes:
- Multiple convolutional layers with batch normalization
- ReLU activation functions
- Max pooling for dimensionality reduction
- Global average pooling
- Fully connected layers for embedding generation
- L2 normalization of embeddings

The model is trained using Triplet Loss or Contrastive Loss to generate
discriminative embeddings where faces of the same person are close together
in embedding space, and faces of different people are far apart.

Author: Face Recognition System
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConvBlock(nn.Module):
    """
    Convolutional block with convolution, batch normalization, and activation.
    """
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
        activation: str = "relu",
        batch_norm: bool = True
    ):
        """
        Initialize convolutional block.
        
        Args:
            in_channels: Number of input channels
            out_channels: Number of output channels
            kernel_size: Size of the convolutional kernel
            stride: Stride of the convolution
            padding: Padding for the convolution
            activation: Activation function ('relu', 'elu', 'leaky_relu')
            batch_norm: Whether to use batch normalization
        """
        super(ConvBlock, self).__init__()
        
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        self.batch_norm = nn.BatchNorm2d(out_channels) if batch_norm else None
        
        if activation == "relu":
            self.activation = nn.ReLU(inplace=True)
        elif activation == "elu":
            self.activation = nn.ELU(alpha=1.0, inplace=True)
        elif activation == "leaky_relu":
            self.activation = nn.LeakyReLU(negative_slope=0.2, inplace=True)
        else:
            self.activation = nn.ReLU(inplace=True)
        
        logger.info(f"[v0] ConvBlock: {in_channels} -> {out_channels} (kernel: {kernel_size}, activation: {activation})")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the block."""
        x = self.conv(x)
        
        if self.batch_norm is not None:
            x = self.batch_norm(x)
        
        x = self.activation(x)
        return x


class ResidualBlock(nn.Module):
    """
    Residual block with skip connection.
    
    Helps with training deeper networks and gradient flow.
    """
    
    def __init__(self, channels: int, kernel_size: int = 3):
        """
        Initialize residual block.
        
        Args:
            channels: Number of channels
            kernel_size: Size of convolutional kernel
        """
        super(ResidualBlock, self).__init__()
        
        padding = (kernel_size - 1) // 2
        
        self.conv1 = nn.Conv2d(channels, channels, kernel_size, padding=padding)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size, padding=padding)
        self.bn2 = nn.BatchNorm2d(channels)
        self.conv3 = nn.Conv2d(channels, channels, kernel_size, padding=padding)
        self.bn3 = nn.BatchNorm2d(channels)
        self.conv4 = nn.Conv2d(channels, channels, kernel_size, padding=padding)
        self.bn4 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
        
        logger.info(f"[v0] ResidualBlock: {channels} channels with skip connection")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with skip connection."""
        identity = x
        
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        
        x = self.conv2(x)
        x = self.bn2(x)
        
        x = x + identity  # Skip connection
        x = self.relu(x)
        
        return x


class FaceEmbeddingCNN(nn.Module):
    """
    Custom CNN for generating facial embeddings.
    
    Architecture:
    1. Input: (batch, 3, 160, 160)
    2. Convolutional blocks with increasing channels
    3. Max pooling layers for dimension reduction
    4. Residual blocks for deep feature learning
    5. Global average pooling
    6. Fully connected layers for embedding
    7. L2 normalization of output embeddings
    
    Output: Fixed-length embeddings (default: 128 dimensions)
    """
    
    def __init__(
        self,
        input_size: Tuple[int, int] = (160, 160),
        embedding_dim: int = 128,
        num_residual_blocks: int = 2,
        use_dropout: bool = True,
        dropout_rate: float = 0.5
    ):
        """
        Initialize the CNN for facial embeddings.
        
        Args:
            input_size: Input image size (height, width)
            embedding_dim: Dimension of the output embeddings
            num_residual_blocks: Number of residual blocks per stage
            use_dropout: Whether to use dropout
            dropout_rate: Dropout probability
        """
        super(FaceEmbeddingCNN, self).__init__()
        
        self.input_size = input_size
        self.embedding_dim = embedding_dim
        
        logger.info(f"[v0] Building FaceEmbeddingCNN with embedding_dim={embedding_dim}")
        
        # Stage 1: 3 -> 64 channels
        self.conv_block1 = ConvBlock(3, 64, kernel_size=7, stride=2, padding=3)
        self.max_pool1 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        
        # Residual blocks for stage 1
        self.residual_blocks1 = nn.Sequential(*[
            ResidualBlock(64) for _ in range(num_residual_blocks)
        ])
        
        # Stage 2: 64 -> 128 channels
        self.conv_block2 = ConvBlock(64, 128, kernel_size=3, stride=2, padding=1)
        self.residual_blocks2 = nn.Sequential(*[
            ResidualBlock(128) for _ in range(num_residual_blocks)
        ])
        
        # Stage 3: 128 -> 256 channels
        self.conv_block3 = ConvBlock(128, 256, kernel_size=3, stride=2, padding=1)
        self.residual_blocks3 = nn.Sequential(*[
            ResidualBlock(256) for _ in range(num_residual_blocks)
        ])
        
        # Stage 4: 256 -> 512 channels
        self.conv_block4 = ConvBlock(256, 512, kernel_size=3, stride=2, padding=1)
        self.residual_blocks4 = nn.Sequential(*[
            ResidualBlock(512) for _ in range(num_residual_blocks)
        ])
        
        # Global average pooling
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Fully connected layers
        self.fc1 = nn.Linear(512, 256)
        self.bn_fc1 = nn.BatchNorm1d(256)
        self.relu_fc = nn.ReLU(inplace=True)
        
        if use_dropout:
            self.dropout = nn.Dropout(p=dropout_rate)
        else:
            self.dropout = None
        
        self.fc2 = nn.Linear(256, embedding_dim)
        
        logger.info(f"[v0] FaceEmbeddingCNN architecture built successfully")
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize network weights using Kaiming initialization."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
        
        logger.info(f"[v0] Weights initialized using Kaiming initialization")
    
    def forward(self, x: torch.Tensor, return_normalized: bool = True) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor (batch_size, 3, 160, 160)
            return_normalized: If True, returns L2-normalized embeddings
            
        Returns:
            Embeddings tensor (batch_size, embedding_dim)
        """
        # Stage 1
        x = self.conv_block1(x)  # (batch, 64, 80, 80)
        x = self.max_pool1(x)    # (batch, 64, 40, 40)
        x = self.residual_blocks1(x)
        
        # Stage 2
        x = self.conv_block2(x)  # (batch, 128, 28, 28)
        x = self.residual_blocks2(x)
        
        # Stage 3
        x = self.conv_block3(x)  # (batch, 256, 14, 14)
        x = self.residual_blocks3(x)
        
        # Stage 4
        x = self.conv_block4(x)  # (batch, 512, 7, 7)
        x = self.residual_blocks4(x)
        
        # Global average pooling
        x = self.global_avg_pool(x)  # (batch, 512, 1, 1)
        x = x.view(x.size(0), -1)    # (batch, 512)
        
        # Fully connected layers
        x = self.fc1(x)           # (batch, 256)
        x = self.bn_fc1(x)
        x = self.relu_fc(x)
        
        if self.dropout is not None:
            x = self.dropout(x)
        
        x = self.fc2(x)           # (batch, embedding_dim)
        
        # L2 normalization
        if return_normalized:
            x = F.normalize(x, p=2, dim=1)  # Normalize each embedding to unit length
        
        return x
    
    def get_embedding(self, x: torch.Tensor) -> torch.Tensor:
        """
        Get embedding for input image(s).
        
        Args:
            x: Input tensor
            
        Returns:
            Normalized embeddings
        """
        return self.forward(x, return_normalized=True)


class EmbeddingModel(nn.Module):
    """
    Complete model wrapper for embedding generation with preprocessing.
    """
    
    def __init__(self, embedding_dim: int = 128, pretrained: bool = False):
        """
        Initialize embedding model.
        
        Args:
            embedding_dim: Dimension of embeddings
            pretrained: Whether to load pretrained weights
        """
        super(EmbeddingModel, self).__init__()
        
        self.embedding_dim = embedding_dim
        self.cnn = FaceEmbeddingCNN(embedding_dim=embedding_dim)
        
        logger.info(f"[v0] EmbeddingModel initialized with embedding_dim={embedding_dim}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.cnn.forward(x, return_normalized=True)
    
    def get_embedding_batch(self, images: torch.Tensor) -> torch.Tensor:
        """
        Generate embeddings for a batch of images.
        
        Args:
            images: Batch of images (batch_size, 3, 224, 224)
            
        Returns:
            Batch of embeddings (batch_size, embedding_dim)
        """
        with torch.no_grad():
            embeddings = self.forward(images)
        return embeddings


if __name__ == "__main__":
    # Example usage
    logger.info("[v0] Creating model...")
    model = FaceEmbeddingCNN(embedding_dim=128)
    
    # Create dummy input
    dummy_input = torch.randn(4, 3, 224, 224)
    
    # Forward pass
    logger.info("[v0] Running forward pass...")
    embeddings = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding norm (should be ~1): {torch.norm(embeddings[0]).item():.4f}")
