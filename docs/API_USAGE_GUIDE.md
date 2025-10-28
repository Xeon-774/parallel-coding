# API Usage Guide - Week 2 MVP

**Version**: 2.0.0-week2-mvp
**Generated**: 2025-10-28
**Status**: Production Ready

---

## Quick Start

### 1. Start the API Server

```bash
# Development mode with auto-reload
uvicorn orchestrator.api.main:app --reload --port 8000

# Production mode
uvicorn orchestrator.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Access Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### 3. Generate Test Token

```python
from orchestrator.core.auth import create_access_token

# Create token with all scopes
token = create_access_token(
    user_id="test-user",
    scopes=["supervisor:read", "supervisor:write", "jobs:read", "jobs:write", "resources:read", "resources:write"]
)
print(f"Token: {token}")
```

---

## Authentication

All API endpoints require JWT Bearer token authentication.

### Token Format

```http
Authorization: Bearer <your-jwt-token>
```

### Available Scopes

| Scope | Description |
|-------|-------------|
| `supervisor:read` | Read worker status and metrics |
| `supervisor:write` | Control workers (pause/resume/terminate) |
| `jobs:read` | View job details and status |
| `jobs:write` | Submit and cancel jobs |
| `resources:read` | View resource quotas and usage |
| `resources:write` | Allocate and release resources |

### Example: cURL with Authentication

```bash
# Store token in variable
TOKEN="your-jwt-token-here"

# Make authenticated request
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/supervisor/workers
```

---

## Core API Endpoints

### Supervisor API

Monitor and control Claude Code worker instances.

#### List Workers

```http
GET /api/supervisor/workers
```

**Query Parameters:**
- `workspace_id` (optional): Filter by workspace
- `status` (optional): Filter by status (IDLE, RUNNING, PAUSED, COMPLETED, FAILED, TERMINATED)
- `limit` (default: 50): Maximum results
- `offset` (default: 0): Pagination offset

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/supervisor/workers?status=RUNNING&limit=10"
```

**Response:**
```json
{
  "workers": [
    {
      "id": "worker-123",
      "workspace_id": "ws-001",
      "status": "RUNNING",
      "created_at": "2025-10-28T10:00:00Z",
      "updated_at": "2025-10-28T10:05:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### Get Worker Details

```http
GET /api/supervisor/workers/{worker_id}
```

#### Terminate Worker

```http
POST /api/supervisor/workers/{worker_id}/terminate
```

#### Get System Metrics

```http
GET /api/supervisor/metrics
```

**Response:**
```json
{
  "total_workers": 10,
  "by_status": {
    "IDLE": 3,
    "RUNNING": 5,
    "PAUSED": 2,
    "COMPLETED": 0,
    "FAILED": 0,
    "TERMINATED": 0
  }
}
```

---

### Job Orchestrator API

Submit and manage hierarchical AI coding jobs.

#### Submit Job

```http
POST /api/jobs/submit
```

**Request Body:**
```json
{
  "task_description": "Implement user authentication system",
  "worker_count": 3,
  "depth": 0,
  "parent_job_id": null
}
```

**Response:**
```json
{
  "id": "j_a1b2c3d4e5f6",
  "status": "PENDING",
  "task_description": "Implement user authentication system",
  "worker_count": 3,
  "depth": 0,
  "parent_job_id": null,
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": "2025-10-28T10:00:01Z"
}
```

#### Get Job Details

```http
GET /api/jobs/{job_id}
```

#### List Jobs

```http
GET /api/jobs
```

**Query Parameters:**
- `depth` (optional): Filter by depth level
- `status` (optional): Filter by job status
- `parent_job_id` (optional): Filter by parent job
- `limit` (default: 50): Maximum results
- `offset` (default: 0): Pagination offset

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/jobs?status=RUNNING&depth=0"
```

#### Cancel Job

```http
POST /api/jobs/{job_id}/cancel
```

**Response:**
```json
{
  "id": "j_a1b2c3d4e5f6",
  "status": "CANCELED",
  "task_description": "Implement user authentication system",
  "worker_count": 3,
  "depth": 0,
  "parent_job_id": null,
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": "2025-10-28T10:05:30Z"
}
```

---

### Resource Manager API

Manage hierarchical resource allocation.

#### Get Resource Quotas

```http
GET /api/resources/quotas
```

**Response:**
```json
{
  "quotas": [
    {"depth": 0, "max_workers": 10},
    {"depth": 1, "max_workers": 8},
    {"depth": 2, "max_workers": 5},
    {"depth": 3, "max_workers": 3},
    {"depth": 4, "max_workers": 2},
    {"depth": 5, "max_workers": 1}
  ]
}
```

#### Allocate Resources

```http
POST /api/resources/allocate
```

**Request Body:**
```json
{
  "job_id": "j_a1b2c3d4e5f6",
  "depth": 0,
  "worker_count": 3
}
```

**Response:**
```json
{
  "job_id": "j_a1b2c3d4e5f6",
  "depth": 0,
  "requested": 3,
  "granted": 3
}
```

#### Release Resources

```http
POST /api/resources/release
```

**Request Body:**
```json
{
  "job_id": "j_a1b2c3d4e5f6",
  "depth": 0
}
```

#### Get Resource Usage

```http
GET /api/resources/usage
```

**Response:**
```json
{
  "usage": [
    {"depth": 0, "allocated": 7, "available": 3},
    {"depth": 1, "allocated": 3, "available": 5},
    {"depth": 2, "allocated": 0, "available": 5}
  ]
}
```

---

## Complete Workflow Example

### 1. Submit a Job

```python
import requests

API_BASE = "http://localhost:8000"
TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Submit job
response = requests.post(
    f"{API_BASE}/api/jobs/submit",
    headers=headers,
    json={
        "task_description": "Build React dashboard",
        "worker_count": 2,
        "depth": 0
    }
)
job = response.json()
job_id = job["id"]
print(f"Job created: {job_id}")
```

### 2. Allocate Resources

```python
# Allocate resources for the job
response = requests.post(
    f"{API_BASE}/api/resources/allocate",
    headers=headers,
    json={
        "job_id": job_id,
        "depth": 0,
        "worker_count": 2
    }
)
allocation = response.json()
print(f"Resources allocated: {allocation['granted']} workers")
```

### 3. Monitor Progress

```python
import time

# Poll job status
while True:
    response = requests.get(
        f"{API_BASE}/api/jobs/{job_id}",
        headers=headers
    )
    job = response.json()
    status = job["status"]
    print(f"Job status: {status}")

    if status in ["COMPLETED", "FAILED", "CANCELED"]:
        break

    time.sleep(5)  # Poll every 5 seconds
```

### 4. Release Resources

```python
# Release resources after completion
response = requests.post(
    f"{API_BASE}/api/resources/release",
    headers=headers,
    json={
        "job_id": job_id,
        "depth": 0
    }
)
print("Resources released")
```

---

## Postman Collection

### Import OpenAPI Spec

1. Open Postman
2. Click **Import** button
3. Select **File** tab
4. Choose `openapi.json` from project root
5. Postman will generate a complete collection with all endpoints

### Configure Environment

Create a Postman environment with these variables:

```json
{
  "base_url": "http://localhost:8000",
  "token": "your-jwt-token-here"
}
```

Use `{{base_url}}` and `{{token}}` in your requests.

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET request successful |
| 201 | Created | Job submitted successfully |
| 400 | Bad Request | Invalid state transition |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient scope |
| 404 | Not Found | Job/worker not found |
| 422 | Validation Error | Invalid request body |
| 500 | Internal Server Error | Unexpected error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Example

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "task_description"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## Testing

### Run Integration Tests

```bash
# Run all Week 2 MVP tests
pytest tests/integration/test_week2*.py -v

# Run with coverage
pytest tests/integration/test_week2*.py --cov=orchestrator --cov-report=html
```

### Manual Testing Script

```python
# tests/manual/test_api_workflow.py
import requests
from orchestrator.core.auth import create_access_token

API_BASE = "http://localhost:8000"

# Generate token
token = create_access_token(
    user_id="test-user",
    scopes=["supervisor:read", "jobs:write", "resources:write"]
)

headers = {"Authorization": f"Bearer {token}"}

# Test workflow
print("1. Listing workers...")
r = requests.get(f"{API_BASE}/api/supervisor/workers", headers=headers)
print(f"   Status: {r.status_code}, Workers: {r.json()['total']}")

print("2. Submitting job...")
r = requests.post(
    f"{API_BASE}/api/jobs/submit",
    headers=headers,
    json={"task_description": "Test job", "worker_count": 1, "depth": 0}
)
job_id = r.json()["id"]
print(f"   Job ID: {job_id}")

print("3. Getting resource quotas...")
r = requests.get(f"{API_BASE}/api/resources/quotas", headers=headers)
print(f"   Quotas: {len(r.json()['quotas'])} depth levels")

print("\n✅ All tests passed!")
```

---

## Production Deployment

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/orchestrator

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://your-frontend.com

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "orchestrator.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
# Build and run
docker build -t parallel-ai-orchestrator .
docker run -p 8000:8000 parallel-ai-orchestrator
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Missing or invalid JWT token

**Solution**:
```python
# Generate fresh token
from orchestrator.core.auth import create_access_token
token = create_access_token(user_id="your-id", scopes=["supervisor:read", "jobs:write"])
```

### Issue: 403 Forbidden

**Cause**: Token lacks required scope

**Solution**: Include all necessary scopes when creating token:
```python
scopes=["supervisor:read", "supervisor:write", "jobs:read", "jobs:write", "resources:read", "resources:write"]
```

### Issue: 422 Validation Error

**Cause**: Invalid request body format

**Solution**: Check the schema in `/docs` and ensure all required fields are present with correct types.

### Issue: Database Connection Error

**Cause**: Database not initialized

**Solution**:
```bash
python scripts/init_database.py
```

---

## Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Specification**: `openapi.json`
- **Integration Tests**: `tests/integration/test_week2*.py`
- **Architecture**: `docs/WEEK2_MVP_SPECIFICATION.md`
- **GitHub Repository**: https://github.com/your-org/parallel-coding

---

**Generated with**: Claude Code
**Last Updated**: 2025-10-28
