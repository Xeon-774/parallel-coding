# Testing Guide for Claude Orchestrator v7.0

This guide explains how to test the AI-to-AI REST API functionality at different levels.

---

## 🧪 Testing Strategy

Since this is an AI-to-AI orchestration system, testing has unique challenges:

1. **Unit Tests** - Test API models, validation, and auth (no Claude execution needed)
2. **Integration Tests** - Test API endpoints with mocks (no Claude execution needed)
3. **Manual API Tests** - Test SDK client and API workflow (no Claude execution needed)
4. **Full E2E Tests** - Test actual Claude orchestration (requires Claude CLI access)

---

## 📋 Test Levels

### Level 1: Unit Tests (No Server Required)

Test Pydantic models and validation logic:

```bash
# Install test dependencies
pip install pytest pytest-mock httpx

# Run unit tests
pytest tests/test_api_models.py -v
```

**What this tests:**
- ✅ Request/response model validation
- ✅ Configuration parameter validation
- ✅ Data structure integrity
- ✅ Pydantic type checking

**Expected result:** All tests should pass ✓

---

### Level 2: Integration Tests (Mock Server)

Test API endpoints with mocked orchestrator:

```bash
# Install FastAPI test client
pip install httpx

# Run integration tests
pytest tests/test_api_integration.py -v
```

**What this tests:**
- ✅ API endpoint routing
- ✅ Authentication and rate limiting
- ✅ Request/response flow
- ✅ Error handling
- ✅ Status code validation

**Expected result:** Most tests should pass (some may be skipped)

---

### Level 3: Manual API Tests (Live Server)

Test SDK client with live API server:

**Option A: Two Terminals (Recommended)**

Terminal 1 - Start API server:
```bash
python start_api_server.py
```

Terminal 2 - Run tests:
```bash
python tests/manual_api_test.py
```

**Option B: Automated (Experimental)**

```bash
python tests/manual_api_test.py --auto
```

**What this tests:**
- ✅ Server connectivity
- ✅ Health check endpoint
- ✅ System status endpoint
- ✅ Authentication (valid/invalid keys)
- ✅ SDK client functionality
- ⚠️  Job submission (will queue but may fail execution)

**Expected results:**
- Server connectivity: ✓ PASS
- Health check: ✓ PASS
- System status: ✓ PASS
- Authentication: ✓ PASS
- SDK client: ✓ PASS
- Mock orchestration: ⚠️ MAY FAIL (expected without real Claude CLI)

**Note:** The orchestration test will create a job, but execution may fail because it requires actual Claude CLI access. This is **expected** and **OK** - we're testing the API workflow, not the actual orchestration.

---

### Level 4: Full E2E Test (Requires Claude CLI)

Test complete workflow with actual Claude execution:

**Prerequisites:**
- Claude CLI installed and configured
- Git Bash available (Windows) or Bash (Linux/WSL)
- Working directory with git repository

**Simplified E2E Test:**

Create a simple test file: `test_e2e.py`

```python
from orchestrator_client import OrchestratorClient
import time

# Start API server first in another terminal:
# python start_api_server.py

client = OrchestratorClient(
    api_url="http://localhost:8000",
    api_key="sk-orch-dev-key-12345"
)

# Submit a very simple task
print("Submitting simple task...")
job = client.orchestrate(
    request="Create a Python function that prints 'Hello, World!'",
    config={
        "max_workers": 1,
        "enable_ai_analysis": False,
        "default_timeout": 60
    },
    wait=False
)

print(f"Job created: {job.job_id}")

# Monitor progress
print("Monitoring progress...")
for i in range(30):  # Check for 30 seconds
    status = job.status()
    print(f"  Status: {status['status']}")

    if job.is_complete():
        print("✓ Job completed!")
        results = job.results()
        print(f"  Summary: {results['results']['summary']}")
        break

    time.sleep(1)
else:
    print("⚠️  Job did not complete in time")
```

Run:
```bash
python test_e2e.py
```

**What this tests:**
- ✅ Complete API workflow
- ✅ Actual Claude AI execution
- ✅ Task decomposition
- ✅ Result integration
- ✅ Progress monitoring

---

## 🎯 Quick Test Recommendations

### For AI Integration Development

If you're developing an AI application that will use this API:

**Run these tests:**
1. ✅ Unit tests - Verify models work
2. ✅ Manual API tests - Verify API endpoints work
3. ✅ Test with mock data - No need for real Claude execution

**Commands:**
```bash
# 1. Unit tests
pytest tests/test_api_models.py -v

# 2. Start API server (Terminal 1)
python start_api_server.py

# 3. Run manual tests (Terminal 2)
python tests/manual_api_test.py --skip-execution
```

### For System Validation

If you want to validate the entire system works:

**Run all tests:**
```bash
# 1. Unit tests
pytest tests/test_api_models.py -v

# 2. Integration tests
pytest tests/test_api_integration.py -v

# 3. Manual API tests
#    (Start server in one terminal, then run in another)
python start_api_server.py  # Terminal 1
python tests/manual_api_test.py  # Terminal 2

# 4. E2E test (if you have Claude CLI set up)
python test_e2e.py
```

---

## 🔍 Understanding Test Results

### ✅ Success Criteria

**Unit Tests:**
- All Pydantic model validations pass
- Invalid inputs are correctly rejected
- Default values are correct

**Integration Tests:**
- Authentication works correctly
- API endpoints return expected status codes
- Request/response flow is correct

**Manual Tests:**
- Server is reachable
- Health checks pass
- System status returns valid data
- SDK client has all expected methods

**E2E Tests:**
- Jobs are created successfully
- Progress is monitored correctly
- Results are retrieved and structured properly

### ⚠️ Expected Failures

**Without Claude CLI:**
- Orchestration execution will fail
- Worker processes won't start
- No actual code will be generated

**This is OK for API testing!** The API layer works independently of Claude execution.

---

## 🛠️ Troubleshooting

### Server won't start

**Error:** `Address already in use`
**Solution:** Kill existing server or use different port:
```bash
python start_api_server.py --port 8001
```

### Authentication fails

**Error:** `Invalid API key`
**Solution:** Check you're using the default key:
```bash
export ORCHESTRATOR_API_KEY=sk-orch-dev-key-12345
```

### Import errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Tests fail with "Connection refused"

**Error:** `ConnectionRefusedError`
**Solution:** Make sure API server is running:
```bash
# Check if server is running
curl http://localhost:8000/api/v1/health
```

---

## 📊 Test Coverage

Current test coverage:

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|------------|-------------------|-----------|
| API Models | ✅ Complete | - | - |
| API Endpoints | - | ✅ Complete | ⚠️ Partial |
| Authentication | ✅ Complete | ✅ Complete | - |
| SDK Client | ✅ Basic | ✅ Complete | ⚠️ Partial |
| Job Management | - | ✅ Mocked | ⚠️ Partial |
| Orchestration | - | - | ⚠️ Requires Claude |

---

## 🎓 Next Steps

1. **Start with Level 1** - Run unit tests to verify models
2. **Progress to Level 3** - Test API with manual tests
3. **Skip Level 4 initially** - E2E tests require full Claude setup

The API is fully functional even without actual Claude execution. External AI applications can integrate and test against the API without needing Claude CLI access during development.

---

**Last Updated:** 2025-10-20
**Version:** 7.0.0
