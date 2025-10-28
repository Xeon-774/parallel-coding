# Claude Orchestrator - Portable Package for AI Projects

## 🎯 What is this?

This is a **portable AI orchestration infrastructure** that enables any AI (like Claude) to spawn and manage multiple parallel AI workers for complex coding tasks.

**Use Case**: When an AI needs to handle a large project, it can use this orchestrator to:
- Split the task into parallel subtasks
- Spawn multiple AI workers (each in their own context)
- Execute tasks in parallel
- Aggregate results automatically
- Handle recursive orchestration (AI workers can spawn their own workers)

## 📦 Installation (AI Instructions)

### Step 1: Copy to Your Project

```bash
# Copy this entire orchestrator-portable/ folder to your project root
cp -r orchestrator-portable/ /path/to/your/project/
cd /path/to/your/project/orchestrator-portable/
```

### Step 2: Install Dependencies

```bash
# Run the install script
./install.sh

# Or manually:
pip install -r requirements.txt
```

### Step 3: Configure (Optional)

```bash
# Copy template and customize
cp config.template.yaml config.yaml
# Edit config.yaml for your project-specific settings
```

## 🚀 Quick Start (AI Usage)

### Option 1: Simple CLI

```bash
# Start the orchestrator with a task description
./quick-start.sh "Build a REST API with authentication, user management, and data CRUD operations"
```

### Option 2: REST API

```bash
# Start the API server
python api_server.py

# From another terminal or AI:
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "request": "Build a complete e-commerce site with frontend and backend",
    "config": {
      "max_workers": 5,
      "enable_recursion": true,
      "max_recursion_depth": 2
    }
  }'
```

### Option 3: Python API

```python
from orchestrator.api.client import OrchestratorClient

client = OrchestratorClient(
    api_url="http://localhost:8000",
    api_key="your-api-key"
)

result = client.orchestrate(
    request="Create a machine learning pipeline with data preprocessing, training, and evaluation",
    max_workers=4,
    enable_recursion=True
)

print(f"Job ID: {result['job_id']}")
print(f"Status: {result['status']}")
```

## 📊 How It Works (For AI Understanding)

### 1. Task Decomposition
```
Your Request: "Build a full-stack application"
    ↓
AI Analysis: Splits into subtasks
    ↓
Tasks: [Frontend, Backend API, Database, Tests]
    ↓
Parallel Execution: 4 AI workers work simultaneously
```

### 2. Recursive Orchestration (Advanced)
```
Worker 1: Frontend → Completes directly
Worker 2: Backend → "Too complex!"
    ↓
Worker 2 spawns child orchestration:
    ↓
    Child Worker 1: Auth API
    Child Worker 2: Data API
    Child Worker 3: Payment API
    ↓
    Results aggregated → Returned to parent
Worker 3: Database → Completes directly
Worker 4: Tests → Completes directly
```

### 3. Result Structure

Results are stored in hierarchical directories:

```
workspace/
└── job_abc123/
    ├── depth_0/              # Root level
    │   ├── worker_1/         # Frontend worker
    │   ├── worker_2_recursive/  # Backend (spawned children)
    │   ├── worker_3/         # Database worker
    │   └── LEVEL_0_REPORT.md
    ├── depth_1/              # Child level (from worker_2)
    │   ├── worker_1_1/       # Auth API
    │   ├── worker_1_2/       # Data API
    │   └── LEVEL_1_REPORT.md
    ├── logs/                 # All execution logs
    ├── reports/              # Aggregated reports
    └── FINAL_RESULT.md       # Complete summary
```

## 🤖 AI-to-AI Communication Protocol

### When to Use Recursion

If you're an AI worker and encounter a task that's too complex:

```python
# Detect complexity
if task_complexity > threshold:
    # Initiate recursive orchestration
    response = requests.post(
        "http://localhost:8000/api/v1/orchestrate",
        headers={"X-API-Key": "your-api-key"},
        json={
            "request": "Break down this complex backend into microservices",
            "config": {
                "current_depth": current_depth + 1,
                "max_recursion_depth": 3,
                "max_workers": 3
            }
        }
    )
    child_job_id = response.json()["job_id"]

    # Poll for completion
    while True:
        status = get_job_status(child_job_id)
        if status["status"] == "completed":
            return status["results"]
        time.sleep(5)
```

### JSON Input Format

```json
{
  "request": "Task description in natural language",
  "config": {
    "max_workers": 5,
    "default_timeout": 300,
    "execution_mode": "wsl",
    "enable_recursion": true,
    "max_recursion_depth": 3,
    "current_depth": 0
  }
}
```

### JSON Output Format

```json
{
  "job_id": "abc123",
  "status": "completed",
  "results": {
    "tasks": [
      {
        "worker_id": "worker_1",
        "status": "success",
        "output": "...",
        "files_created": ["src/app.tsx", "src/components/Header.tsx"]
      },
      {
        "worker_id": "worker_2",
        "status": "recursive_success",
        "child_job_id": "def456",
        "child_results": [...]
      }
    ],
    "workspace": "/workspace/job_abc123",
    "final_report": "/workspace/job_abc123/FINAL_RESULT.md"
  }
}
```

## 📋 Configuration Options

### config.yaml Example

```yaml
orchestrator:
  execution_mode: "wsl"  # or "windows"
  workspace_root: "./workspace"

workers:
  max_workers: 10
  default_timeout: 300
  max_retries: 2

recursion:
  enable: true
  max_depth: 3

api:
  host: "localhost"
  port: 8000
  api_key: "your-secure-api-key"

logging:
  level: "INFO"
  enable_structured: true
  log_dir: "./logs"
```

## 🔧 Troubleshooting (For AI)

### Issue: "No such file or directory: claude"

**Solution**: Install Claude CLI or configure the path:
```bash
# In config.yaml
orchestrator:
  claude_command: "/path/to/claude"
```

### Issue: "Max recursion depth reached"

**Solution**: This is intentional to prevent infinite loops. Increase if needed:
```json
{
  "config": {
    "max_recursion_depth": 5
  }
}
```

### Issue: "Worker timeout"

**Solution**: Increase timeout for complex tasks:
```json
{
  "config": {
    "default_timeout": 600
  }
}
```

## 📊 Monitoring Progress

### Real-time Log Streaming

```bash
# Watch orchestrator logs
tail -f workspace/job_abc123/logs/orchestrator.log

# Watch specific worker
tail -f workspace/job_abc123/logs/depth_0_worker_1.log
```

### Check Job Status

```bash
# Via API
curl http://localhost:8000/api/v1/jobs/abc123/status

# Via CLI
./check-status.sh abc123
```

## 🎯 Best Practices for AI Usage

### 1. Task Decomposition
- Break down tasks into 3-7 subtasks (optimal parallelization)
- Each subtask should be independently executable
- Avoid dependencies between subtasks when possible

### 2. Recursion Decision
- Use recursion when a subtask has 5+ sub-components
- Don't recurse for simple tasks (overhead not worth it)
- Set appropriate max_depth (2-3 is usually sufficient)

### 3. Error Handling
- Always check status before retrieving results
- Handle "partial" status (some workers succeeded, some failed)
- Retry failed tasks with increased timeout

### 4. Resource Management
- Don't spawn more workers than CPU cores (use max_workers wisely)
- Clean up old job directories periodically
- Monitor memory usage for large projects

## 🔐 Security Notes

**For AI Usage in Production:**

1. **API Key**: Always use a secure API key
2. **Isolation**: Each job runs in isolated workspace
3. **Timeouts**: Prevent runaway processes
4. **Validation**: Input sanitization is built-in
5. **Audit Logs**: All operations are logged

## 📚 Example Use Cases

### Use Case 1: Microservices Development
```
Request: "Build a microservices architecture with auth, users, orders, and payments"
Workers: 4 (one per service)
Recursion: Each service spawns workers for API, database, tests
Result: Complete microservices system in parallel
```

### Use Case 2: Full-stack Application
```
Request: "Create a React + FastAPI + PostgreSQL application"
Workers: 3 (frontend, backend, database)
Recursion: Backend spawns workers for routes, models, migrations
Result: Full-stack app with all components
```

### Use Case 3: Documentation Generation
```
Request: "Generate comprehensive documentation for this codebase"
Workers: 5 (API docs, architecture, user guide, contributing, examples)
Recursion: Not needed (simple parallel tasks)
Result: Complete documentation suite
```

## 🚀 Advanced Features

### Feature: Hierarchical Reporting
- Each recursion level generates its own report
- Final report aggregates all levels
- Complete traceability: which AI created which file

### Feature: Performance Analytics
- Execution timeline
- Parallelization efficiency
- Bottleneck identification
- Resource usage tracking

### Feature: Git Integration
- Each worker commits its changes
- Commit messages include worker ID
- Easy to trace authorship
- Conflict resolution built-in

## 🆘 Support

For issues or questions:
1. Check the logs: `workspace/job_XXX/logs/`
2. Read the final report: `workspace/job_XXX/FINAL_RESULT.md`
3. Review configuration: `config.yaml`
4. See examples in `examples/` directory

## 📄 License

MIT License - Free to use in any project

---

**Ready to orchestrate? Start with `./quick-start.sh "your task here"`** 🚀