#!/bin/bash

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p faces
mkdir -p embeddings

echo "Backend setup completed successfully!"
echo "To run the server: uvicorn app:app --reload --port 8000"