# Flask Backend Setup Guide

## Installation

### 1. Prerequisites
- Python 3.9+
- pip or conda
- SQLite or PostgreSQL database

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r flask_requirements.txt
```

### 4. Environment Configuration
Create `.env` file with your configuration:
```bash
cp .env .env.local
# Edit .env.local with your settings
```

### 5. Initialize Database
```bash
python -c "from flask_app import app, db; app.app_context().push(); db.create_all()"
```

### 6. Run the Flask Server
```bash
python flask_app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Person Management
- `GET /api/persons` - Get all persons
- `GET /api/persons/<id>` - Get person by ID
- `POST /api/persons` - Add new person with face image
- `PUT /api/persons/<id>` - Update person details
- `DELETE /api/persons/<id>` - Delete person

### CCTV Processing
- `GET /api/cctv/cameras` - Get all cameras
- `POST /api/cctv/cameras` - Add new camera
- `POST /api/cctv/process-frame` - Process single frame
- `POST /api/cctv/upload-video` - Upload and process video
- `POST /api/cctv/realtime-feed` - Process real-time frames

### Alert Management
- `GET /api/alerts` - Get alerts with filtering
- `GET /api/alerts/<id>` - Get specific alert
- `PUT /api/alerts/<id>/status` - Update alert status
- `GET /api/alerts/by-person/<id>` - Get alerts for person
- `GET /api/alerts/statistics` - Get alert statistics
- `GET /api/alerts/export` - Export alerts as CSV

### Dashboard
- `GET /api/stats` - Get dashboard statistics
- `GET /api/system-info` - Get system information

## Testing with cURL

```bash
# Add a person (requires face_image file)
curl -X POST http://localhost:5000/api/persons \
  -F "name=John Doe" \
  -F "age=30" \
  -F "status=missing" \
  -F "face_image=@/path/to/image.jpg"

# Process a frame
curl -X POST http://localhost:5000/api/cctv/process-frame \
  -F "frame=@frame.jpg" \
  -F "camera_id=CAM-001" \
  -F "location=Main Entrance"

# Get alerts
curl http://localhost:5000/api/alerts?days=7&limit=20

# Get statistics
curl http://localhost:5000/api/stats
```

## Database Models

### Person Table
- id (Primary Key)
- name (String, indexed)
- age (Integer)
- status (String: missing, wanted, found)
- case_number (String, unique)
- last_seen (String)
- face_image_path (String)
- embedding_path (String)

### Alert Table
- id (Primary Key)
- person_id (Foreign Key)
- camera_id (Foreign Key)
- similarity (Float)
- location (String)
- alert_status (String)
- created_at (DateTime, indexed)

### Camera Table
- id (Primary Key)
- camera_id (String, unique)
- location (String)
- latitude/longitude (Float)
- feed_url (String)

## Security Considerations

1. **Input Validation**: All file uploads are validated
2. **SQL Injection**: Using SQLAlchemy ORM prevents SQL injection
3. **File Handling**: Secure filename handling for uploads
4. **CORS**: Configure CORS properly for production
5. **Authentication**: Add JWT/API Key authentication for production
6. **Rate Limiting**: Implement rate limiting for API endpoints
7. **Logging**: All operations are logged for audit trails

## Production Deployment

1. Use PostgreSQL instead of SQLite
2. Enable HTTPS/SSL
3. Configure proper authentication (JWT)
4. Add rate limiting and request throttling
5. Setup proper logging and monitoring
6. Use environment-specific configurations
7. Enable database backups
8. Configure error handling and alerting
