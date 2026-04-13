# Postman Collection Examples

## Import Into Postman

1. Create a new collection called "AI Surveillance Dashboard"
2. Create a new environment with variable:
   - `base_url`: http://localhost:8000

## Test Requests

### 1. Health Check
\`\`\`
GET {{base_url}}/health
\`\`\`

### 2. Get Dashboard Stats
\`\`\`
GET {{base_url}}/api/stats
\`\`\`

### 3. Get All Persons
\`\`\`
GET {{base_url}}/api/get_people
\`\`\`

### 4. Add Person (requires image file)
\`\`\`
POST {{base_url}}/api/add_person

Form Data:
- name: John Doe
- status: missing
- file: [select image file]
\`\`\`

### 5. Update Person
\`\`\`
PUT {{base_url}}/api/update_person/1

Body (JSON):
{
  "name": "John Updated",
  "status": "wanted"
}
\`\`\`

### 6. Scan CCTV Frame
\`\`\`
POST {{base_url}}/api/scan_frame

Form Data:
- file: [select image file]
- location: CCTV-01
\`\`\`

### 7. Delete Person
\`\`\`
DELETE {{base_url}}/api/delete_person/1
\`\`\`

## Expected Responses

All successful responses return HTTP 200 or 201.
Errors return appropriate HTTP status codes (400, 404, 500) with error details.
