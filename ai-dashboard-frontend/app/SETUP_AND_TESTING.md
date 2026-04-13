# Complete Setup and Testing Guide

## System Components Checklist

### ✅ Frontend (Next.js)
- [x] Login page with authentication
- [x] Protected pages with auth redirects
- [x] Dashboard with real-time statistics
- [x] Face database management
- [x] Camera capture and comparison
- [x] Reports and analytics
- [x] User profile management
- [x] Dark/Light theme support
- [x] Notifications system

### ✅ Backend (FastAPI)
- [x] FastAPI server (port 8000)
- [x] Image preprocessing pipeline
- [x] Face detection module
- [x] Custom CNN for embeddings
- [x] SQLite database layer
- [x] Face matching with similarity metrics
- [x] Complete API endpoints
- [x] CORS middleware
- [x] Auto-generated API docs

### ✅ Integration
- [x] TypeScript API client
- [x] Base64 image encoding/decoding
- [x] Request/Response validation
- [x] Error handling
- [x] Loading states

---

## Part 1: Backend Setup

### Step 1.1: Install Python Dependencies

```bash
# Navigate to backend directory
cd backend/face_recognition_system

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 1.2: Start FastAPI Server

```bash
# Option 1: Direct Python execution (includes auto-reload)
python api_server.py

# Option 2: Using uvicorn directly
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Production deployment
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

### Step 1.3: Verify Backend is Running

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "device": "cpu",
  "model_initialized": true
}

# Test persons endpoint (should be empty)
curl http://localhost:8000/api/persons

# Expected response: []

# Access API documentation
# Open browser to: http://localhost:8000/docs
```

---

## Part 2: Frontend Setup

### Step 2.1: Install Node Dependencies

```bash
# From project root directory
npm install

# Or if using yarn
yarn install
```

### Step 2.2: Set Environment Variables

```bash
# Create .env.local file in project root
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Verify the file was created
cat .env.local
```

### Step 2.3: Start Development Server

```bash
# From project root
npm run dev

# Or with yarn
yarn dev

# Or with npm script
npm run dev -- --port 3000
```

**Expected Output:**
```
> next dev

  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Environments: .env.local

✓ Ready in 2.5s
✓ Compiled client and server successfully
```

### Step 2.4: Access the Application

Open browser and navigate to:
- **Main App**: `http://localhost:3000`
- **Login Page**: `http://localhost:3000/login`

---

## Part 3: Testing Integration

### Test 3.1: Login to Dashboard

1. Open `http://localhost:3000/login`
2. Use demo credentials:
   ```
   Email: officer@police.gov
   Password: password123
   ```
3. Or other demo accounts:
   ```
   admin@police.gov / admin123
   detective@police.gov / detective123
   ```
4. Click "Login" button
5. Should redirect to dashboard (`http://localhost:3000`)

**Expected:**
- ✓ Login page loads
- ✓ No CORS errors in console
- ✓ Redirect to dashboard after login
- ✓ User info displays in header

### Test 3.2: Check API Connectivity

Open browser console (F12) and run:

```javascript
// Test API client
import { healthCheck } from '/lib/api-client'

// Health check
await healthCheck()

// Should see console output:
// [v0] Performing health check
// [v0] Health check passed: {status: "healthy", ...}
```

### Test 3.3: View Dashboard

1. After login, navigate to Dashboard
2. Should see:
   - ✓ Summary cards (total persons, matches, alerts)
   - ✓ Real-time statistics
   - ✓ Charts and graphs
   - ✓ Notifications panel

### Test 3.4: Test Face Database Page

1. Navigate to "Face Database" from sidebar
2. Should see:
   - ✓ Empty database initially
   - ✓ "Add Person" button
   - ✓ Search functionality
   - ✓ Filter options

### Test 3.5: Test Camera Capture Page

1. Navigate to "Camera Capture" from sidebar
2. Should see:
   - ✓ Camera section with start/stop buttons
   - ✓ Upload image section
   - ✓ Comparison results area
   - ✓ Database statistics

### Test 3.6: Test API Endpoints Directly

Using cURL or Postman:

```bash
# Get all persons
curl http://localhost:8000/api/persons

# Get statistics
curl http://localhost:8000/api/statistics

# Health check
curl http://localhost:8000/api/health
```

---

## Part 4: Advanced Testing

### Test 4.1: Register a Face

```bash
# Convert image to base64 (macOS/Linux)
base64 < /path/to/image.jpg

# Use API client in browser console
import { registerFace, fileToBase64 } from '/lib/api-client'

const file = /* your image file */
const base64 = await fileToBase64(file)
const result = await registerFace({
  name: "John Doe",
  image_base64: base64,
  status: "registered"
})
console.log(result)
```

### Test 4.2: Match Face

```javascript
import { matchFace, fileToBase64 } from '/lib/api-client'

const file = /* your image file */
const base64 = await fileToBase64(file)
const result = await matchFace({
  image_base64: base64,
  top_k: 5
})
console.log(result)
```

### Test 4.3: Performance Testing

```bash
# Backend performance
time curl http://localhost:8000/api/health

# Frontend load time (Chrome DevTools)
# 1. Press F12 to open DevTools
# 2. Go to Performance tab
# 3. Record page load
# 4. Analyze metrics
```

---

## Part 5: Troubleshooting

### Issue: "Connection refused" on localhost:8000

**Cause**: Backend not running

**Solution**:
```bash
# Check if port 8000 is in use
# macOS/Linux:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# Start backend again
cd backend/face_recognition_system
python api_server.py
```

### Issue: CORS errors in browser console

**Cause**: API URL not set correctly

**Solution**:
```bash
# Check .env.local file exists
cat .env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000/api

# If missing, create it:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Restart frontend
npm run dev
```

### Issue: 422 Validation Error from API

**Cause**: Invalid request body

**Solution**:
- Ensure image is properly base64 encoded
- Check all required fields are present
- Verify data types match API schema
- Check API documentation: http://localhost:8000/docs

### Issue: Model loading errors

**Cause**: Missing model files or dependencies

**Solution**:
```bash
# Reinstall dependencies
cd backend/face_recognition_system
pip install -r requirements.txt --force-reinstall

# Check model files exist
ls models/
```

### Issue: High latency on API calls

**Cause**: GPU not available or model too large

**Solution**:
```python
# Check device in backend logs
# Should show: "Using device: cuda" or "Using device: cpu"

# For GPU support, install appropriate CUDA/cuDNN
# See backend/face_recognition_system/README.md
```

---

## Part 6: Monitoring and Debugging

### View Backend Logs

```bash
# In backend terminal, logs are printed in real-time
# Look for:
# - "[v0]" prefixed messages
# - INFO: requests
# - ERROR: exceptions

# Example log output:
# INFO:     127.0.0.1:54321 - "POST /api/register HTTP/1.1" 200 OK
```

### View Frontend Console

```bash
# Press F12 in browser to open DevTools
# Console tab shows:
# - "[v0]" prefixed debug messages
# - Network requests to backend
# - Errors and warnings
```

### API Documentation

```bash
# Swagger UI (interactive)
# http://localhost:8000/docs

# ReDoc (read-only)
# http://localhost:8000/redoc

# Both show:
# - All available endpoints
# - Request/response schemas
# - Try it out functionality
```

---

## Part 7: Database

### SQLite Database Location

```bash
# Database file created at:
backend/face_recognition_system/faces.db

# View database contents (install sqlite3 first)
sqlite3 backend/face_recognition_system/faces.db

# In sqlite3 prompt:
.tables                    # List all tables
SELECT * FROM persons;     # View persons
SELECT * FROM faces;       # View faces
SELECT COUNT(*) FROM embeddings;  # Count embeddings
```

### Reset Database

```bash
# Delete database file
rm backend/face_recognition_system/faces.db

# Backend will recreate on next request
```

---

## Part 8: Deployment

### Local Testing (Development)

```bash
# Terminal 1: Backend
cd backend/face_recognition_system
python api_server.py

# Terminal 2: Frontend
npm run dev
```

### Production Deployment

```bash
# Build frontend
npm run build
npm start

# Deploy backend with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 api_server:app
```

---

## Summary Checklist

Before considering integration complete, verify:

- [x] Backend starts without errors
- [x] Frontend loads without errors
- [x] No CORS errors in console
- [x] Login works with demo credentials
- [x] Dashboard displays correctly
- [x] API endpoints respond to requests
- [x] API documentation loads (http://localhost:8000/docs)
- [x] Database operations work
- [x] Performance is acceptable

---

## Support

For issues or questions:

1. Check logs in terminal (backend) and console (frontend)
2. Review API documentation: http://localhost:8000/docs
3. Check INTEGRATION_STATUS.md for common issues
4. Refer to README files in backend directory

---

## Next Steps

Once all tests pass:

1. **Register Test Data**: Use Camera Capture to register sample faces
2. **Test Matching**: Upload images and verify matching accuracy
3. **Explore Features**: Test all dashboard features
4. **Performance**: Monitor latency and throughput
5. **Production**: Deploy to cloud platform (AWS, GCP, Azure, etc.)

**Status: READY FOR TESTING** ✅
