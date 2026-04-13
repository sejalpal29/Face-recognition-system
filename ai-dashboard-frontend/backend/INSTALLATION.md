# AI Surveillance Dashboard Backend - Installation Guide

## Overview
This is a FastAPI-based backend for facial recognition and surveillance monitoring. It provides REST APIs for managing persons, scanning CCTV frames, and generating real-time alerts.

## Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps

### 1. Clone or Download the Backend Files
\`\`\`bash
cd backend
\`\`\`

### 2. Create Virtual Environment
\`\`\`bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
\`\`\`

### 3. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

This will install:
- FastAPI: Modern web framework
- Uvicorn: ASGI server
- SQLAlchemy: ORM for database
- OpenCV: Computer vision library
- DeepFace: Face recognition
- TensorFlow: Deep learning
- scikit-learn: Machine learning utilities

### 4. Create Necessary Directories
\`\`\`bash
mkdir faces
mkdir embeddings
\`\`\`

### 5. Run the Backend Server
\`\`\`bash
uvicorn app:app --reload --port 8000
\`\`\`

The API will be available at: http://localhost:8000

## Project Structure
\`\`\`
backend/
├── app.py                          # Main FastAPI application
├── models.py                       # Pydantic data models
├── routes.py                       # Person management endpoints
├── cctv_routes.py                 # CCTV scanning endpoints
├── face_recognition_utils.py      # Face detection and embedding utilities
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── setup.sh                       # Setup script
├── faces/                         # Stored cropped face images
├── embeddings/                    # Stored face embeddings (vectors)
└── surveillance.db               # SQLite database

\`\`\`

## API Endpoints

### Health Check
\`\`\`
GET /health
\`\`\`

### Dashboard Stats
\`\`\`
GET /api/stats
Returns: total_persons, total_matches, total_alerts, total_scans, recent_alerts
\`\`\`

### Person Management

#### Add Person
\`\`\`
POST /api/add_person
Parameters: name (string), status (string), file (image)
Returns: Person object with id, name, status, timestamps
\`\`\`

#### Get All Persons
\`\`\`
GET /api/get_people
Returns: List of all registered persons
\`\`\`

#### Get Specific Person
\`\`\`
GET /api/get_person/{person_id}
Returns: Person object
\`\`\`

#### Update Person
\`\`\`
PUT /api/update_person/{person_id}
Parameters: name (string), status (string)
Returns: Updated person object
\`\`\`

#### Delete Person
\`\`\`
DELETE /api/delete_person/{person_id}
Returns: Success message
\`\`\`

### CCTV Monitoring

#### Scan Frame for Matches
\`\`\`
POST /api/scan_frame
Parameters: file (image), location (string, optional)
Returns: ScanResult with match status, person name, similarity score, alert flag
\`\`\`

## Configuration

Edit `.env` file to configure:
\`\`\`
DATABASE_URL=sqlite:///./surveillance.db
SIMILARITY_THRESHOLD=0.6        # Threshold for considering a match (0-1)
LOG_LEVEL=INFO
\`\`\`

## Testing with cURL

### Add a Person
\`\`\`bash
curl -X POST "http://localhost:8000/api/add_person" \
  -F "name=John Doe" \
  -F "status=missing" \
  -F "file=@/path/to/image.jpg"
\`\`\`

### Get All Persons
\`\`\`bash
curl "http://localhost:8000/api/get_people"
\`\`\`

### Scan CCTV Frame
\`\`\`bash
curl -X POST "http://localhost:8000/api/scan_frame" \
  -F "file=@/path/to/cctv_frame.jpg" \
  -F "location=CCTV-01"
\`\`\`

### Get Dashboard Stats
\`\`\`bash
curl "http://localhost:8000/api/stats"
\`\`\`

### Delete Person
\`\`\`bash
curl -X DELETE "http://localhost:8000/api/delete_person/1"
\`\`\`

## Testing with Postman

1. Open Postman
2. Import the endpoints or create requests manually
3. Use the cURL examples above as reference
4. Set request method (GET, POST, DELETE, etc.)
5. Add form data for file uploads
6. Send and view responses

## API Response Examples

### Successful Person Add
\`\`\`json
{
  "id": 1,
  "name": "John Doe",
  "status": "missing",
  "face_image_path": "faces/uuid-here.jpg",
  "embedding_path": "embeddings/uuid-here.pkl",
  "created_at": "2024-01-15T10:30:45.123456",
  "updated_at": "2024-01-15T10:30:45.123456"
}
\`\`\`

### Scan Frame Result (Match Found)
\`\`\`json
{
  "match": true,
  "name": "John Doe",
  "person_id": 1,
  "similarity": 0.88,
  "alert": true,
  "location": "CCTV-01",
  "timestamp": "2024-01-15T10:35:12.654321"
}
\`\`\`

### Dashboard Stats
\`\`\`json
{
  "total_persons": 25,
  "total_matches": 42,
  "total_alerts": 15,
  "total_scans": 1205,
  "recent_alerts": [
    {
      "id": 1,
      "person_id": 1,
      "person_name": "John Doe",
      "similarity": 0.88,
      "location": "CCTV-01",
      "created_at": "2024-01-15T10:35:12.654321"
    }
  ]
}
\`\`\`

## Troubleshooting

### Issue: DeepFace model download fails
**Solution**: Models will auto-download on first use. Ensure internet connection is stable.

### Issue: No faces detected in image
**Solution**: Ensure the image has clear, frontal faces. Try with better lighting.

### Issue: Database locked error
**Solution**: Close all connections and restart the server.

### Issue: CORS errors in frontend
**Solution**: CORS is enabled for all origins by default. Check browser console for specific errors.

### Issue: Out of memory during model loading
**Solution**: Reduce batch processing or run on a machine with more RAM.

## Performance Tips

1. **Optimize Images**: Keep images below 2MB
2. **Batch Processing**: Process multiple frames in batch for efficiency
3. **Caching**: Embeddings are cached in memory for faster comparison
4. **Database**: Regular cleanup of old alerts improves performance
5. **Threading**: FastAPI handles concurrent requests efficiently

## Security Recommendations

1. **API Keys**: Add authentication before production
2. **Rate Limiting**: Implement rate limiting for public APIs
3. **Input Validation**: All inputs are validated
4. **File Upload**: Limit file size and type
5. **Database**: Use production database (PostgreSQL recommended)
6. **Environment Variables**: Never commit .env files

## Production Deployment

### Using Gunicorn
\`\`\`bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
\`\`\`

### Using Docker
\`\`\`dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
\`\`\`

## Support and Updates

For issues or updates:
- Check the API documentation at: http://localhost:8000/docs
- Review logs in the console output
- Test endpoints with provided cURL examples
