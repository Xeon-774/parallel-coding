# Project Integration Guide

**Version**: 2.0.0-dev (Cross-Platform Compatible)
**Status**: ✅ 100% Cross-Project Compatible
**Date**: 2025-10-30
**Update**: v2.0 - Zero hardcoded paths, full auto-detection

---

## 🆕 What's New in v2.0

**Cross-Project Compatibility Achieved!**

- ✅ **Zero Configuration**: Works out-of-the-box in any project
- ✅ **Auto-Detection**: Automatically finds Codex/Claude CLI (even in WSL!)
- ✅ **No Hardcoded Paths**: 100% portable across projects
- ✅ **Cross-Platform**: Windows (WSL), Linux, macOS
- ✅ **Easy Integration**: Just `git submodule add` and you're ready

**Integration is now as simple as:**
```bash
cd your-project
git submodule add https://github.com/Xeon-774/parallel-coding.git tools/parallel-coding
cd tools/parallel-coding
pip install -r requirements.txt
# Done! No configuration needed.
```

See [getting-started.md](getting-started.md) for quick start guide.

---

## 🎯 Use Cases

This parallel AI coding orchestrator enables **multiple AI instances** to work simultaneously on different parts of your project, dramatically accelerating development velocity.

### Why Parallel AI Coding?

**Traditional sequential AI coding** can take weeks to build complex features. **Parallel AI coding** allows:
- ✅ **4-10 AI workers** developing different components simultaneously
- ✅ **3-5x faster development** compared to single AI
- ✅ **Conflict-free**: Each AI works in isolated workspaces
- ✅ **Coordinated**: Orchestrator manages task distribution and integration

### Common Use Cases

1. **Multi-Service Development**: Build multiple microservices simultaneously
2. **Feature Parallelization**: Split large features into parallel tasks
3. **Documentation Generation**: Create docs, tests, and code in parallel
4. **Refactoring**: Modernize multiple modules at once
5. **Testing**: Generate unit, integration, and E2E tests in parallel

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Your Project Main Claude Instance              │
│           (You are reading this document now)               │
└──────────────────────┬──────────────────────────────────────┘
                       │ Invokes Orchestrator
┌──────────────────────▼──────────────────────────────────────┐
│         Parallel AI Coding Orchestrator (v2.0)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auto         │  │ Circuit      │  │ Structured   │     │
│  │ Detection    │  │ Breaker      │  │ Logging      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┬─────────────┐
         │             │             │             │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ Worker 1│   │ Worker 2│   │ Worker 3│   │ Worker N│
    │ (AI CLI)│   │ (AI CLI)│   │ (AI CLI)│   │ (AI CLI)│
    └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │             │
         └─────────────┴─────────────┴─────────────┘
                       │
    ┌──────────────────▼──────────────────────────────────────┐
    │  Your Project (Parallel Development)                     │
    │                                                           │
    │  workspace/worker_1/     workspace/worker_2/             │
    │  workspace/worker_3/     workspace/worker_4/             │
    └───────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Integration

### As Git Submodule (Recommended)

```bash
# Add as submodule
cd your-project
git submodule add https://github.com/Xeon-774/parallel-coding.git tools/parallel-coding

# Initialize
cd tools/parallel-coding
pip install -r requirements.txt

# Done! No configuration needed (v2.0 auto-detects everything)
```

### As Standalone Tool

```bash
# Clone
git clone https://github.com/Xeon-774/parallel-coding.git
cd parallel-coding

# Install
pip install -r requirements.txt

# Use from any project
cd /path/to/your/project
/path/to/parallel-coding/scripts/execute_task_files.py tasks.md
```

---

## ⚙️ Configuration

### Zero Configuration (Default)

v2.0 auto-detects:
- ✅ Project root
- ✅ Codex/Claude CLI location (even in WSL)
- ✅ WSL distribution (Windows)
- ✅ Node.js/NVM paths
- ✅ Workspace location

**No configuration file needed!**

### Optional Customization

Create `.env` file in your project root for custom settings:

```bash
# Custom workspace location
PARALLEL_CODING_WORKSPACE_ROOT=./build/workspace

# Worker limits
PARALLEL_CODING_MAX_WORKERS=8
PARALLEL_CODING_WORKER_TIMEOUT=600

# Platform-specific (auto-detected if not set)
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04
PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex
PARALLEL_CODING_CLAUDE_PATH=/home/user/.local/bin/claude

# AI model selection
PARALLEL_CODING_CODEX_MODEL=gpt-5
```

See [configuration.md](configuration.md) for all options.

---

## 📋 Integration Examples

### Example 1: Python Project

```bash
# Project structure
your-python-project/
├── src/
├── tests/
├── tools/
│   └── parallel-coding/  ← git submodule
└── tasks/
    ├── task1_implement_api.md
    ├── task2_add_tests.md
    └── task3_documentation.md

# Execute parallel tasks
cd your-python-project
python tools/parallel-coding/scripts/execute_task_files.py tasks/*.md

# Workers create code in workspace/worker_N/
# Review and integrate into src/
```

### Example 2: Node.js / TypeScript Project

```bash
# Project structure
your-node-project/
├── src/
├── __tests__/
├── tools/
│   └── parallel-coding/
└── parallel-tasks.md

# Execute with Codex
python tools/parallel-coding/scripts/execute_task_files.py --codex parallel-tasks.md
```

### Example 3: Multi-Service Project

```bash
# Project structure
microservices-project/
├── service-a/
├── service-b/
├── service-c/
└── tools/
    └── parallel-coding/

# Task file: build-services.md
Split into parallel tasks:
1. Implement service-a API endpoints
2. Implement service-b database layer
3. Implement service-c message queue integration
4. Create integration tests
5. Generate API documentation

# Execute
python tools/parallel-coding/scripts/execute_task_files.py build-services.md
```

---

## 🎯 Best Practices

### 1. Task Decomposition

Break large features into worker-sized tasks (2-4 hours each):

```markdown
# ✅ GOOD: Atomic tasks

## Task 1: API Endpoints
Create REST API with Express.js:
- GET /users
- POST /users
- PUT /users/:id
- DELETE /users/:id

## Task 2: Database Layer
Create database layer with Prisma:
- Define User schema
- Add migrations
- Create CRUD operations

## Task 3: Input Validation
Add Zod validation:
- Request schemas
- Response schemas
- Error handling
```

```markdown
# ❌ BAD: Too large

## Task: Build entire user management system
(Too vague, will confuse workers)
```

### 2. Clear Task Specifications

Each task file should include:
- **What** to build (clear requirements)
- **Where** to put files (directory structure)
- **How** to implement (architecture patterns)
- **Tests** requirements (coverage expectations)

Example task file:
```markdown
# Task: Implement User Authentication

## Requirements
- JWT-based authentication
- Argon2id password hashing
- 30-day refresh tokens

## File Structure
workspace/
├── src/auth/
│   ├── jwt.ts
│   ├── password.ts
│   └── tokens.ts
└── __tests__/auth/
    └── auth.test.ts

## Implementation
- Use jsonwebtoken library
- Use @node-rs/argon2 for hashing
- Store tokens in Redis

## Testing
- Unit tests for all functions
- ≥90% code coverage
- Test edge cases (expired tokens, invalid passwords)
```

### 3. Workspace Management

```bash
# Check worker outputs
ls workspace/worker_1/
ls workspace/worker_2/

# Review generated code
cat workspace/worker_1/src/auth/jwt.ts

# Copy to your project (after review)
cp -r workspace/worker_1/src/* ./src/

# Clean workspace after integration
rm -rf workspace/worker_*/
```

### 4. Progressive Integration

Start small and scale up:

```python
# Stage 1: 2-3 workers (validate system)
python scripts/execute_task_files.py task1.md task2.md

# Review results, verify quality

# Stage 2: 4-6 workers (scale up)
python scripts/execute_task_files.py task*.md

# Stage 3: Full parallel (8-10 workers)
python scripts/execute_task_files.py **/*.md
```

---

## 🔧 CI/CD Integration

### GitHub Actions

```yaml
name: Parallel AI Development

on:
  workflow_dispatch:
    inputs:
      task_files:
        description: 'Task files to execute'
        required: true

jobs:
  parallel-coding:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          cd tools/parallel-coding
          pip install -r requirements.txt

      - name: Execute Parallel Tasks
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python tools/parallel-coding/scripts/execute_task_files.py \
            ${{ github.event.inputs.task_files }}

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: generated-code
          path: workspace/
```

### GitLab CI

```yaml
parallel-coding:
  stage: build
  image: python:3.11
  script:
    - cd tools/parallel-coding
    - pip install -r requirements.txt
    - python scripts/execute_task_files.py ../tasks/*.md
  artifacts:
    paths:
      - workspace/
  only:
    - branches
```

---

## 📊 Monitoring

### Check Worker Status

```bash
# View workspace structure
tree workspace/

# Check worker logs
tail -f workspace/worker_1/orchestrator_terminal.log

# Monitor all workers
for i in {1..4}; do
  echo "=== Worker $i ===" && tail -n 20 workspace/worker_$i/orchestrator_terminal.log
done
```

### Verification

```bash
# Verify generated code compiles
cd workspace/worker_1
npm run build  # or python -m py_compile *.py

# Run generated tests
npm test  # or pytest

# Check code quality
npm run lint  # or flake8 .
```

---

## 🔒 Security

### API Key Management

```bash
# Use environment variables (never commit)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Or use .env file (add to .gitignore)
echo "OPENAI_API_KEY=sk-..." >> .env
echo ".env" >> .gitignore
```

### Code Review

**Always review generated code before integrating:**
1. Check for security vulnerabilities
2. Verify test coverage
3. Review logic correctness
4. Validate API contracts
5. Test edge cases

---

## 🧪 Testing Integration

### Unit Tests

```bash
# Test orchestrator
cd tools/parallel-coding
pytest tests/ -v
```

### Integration Tests

```bash
# Test with real task files
python scripts/execute_task_files.py test_tasks/simple_task.md

# Verify output
ls workspace/worker_1/
```

---

## 🔧 Troubleshooting

### Issue: "Claude/Codex CLI not found"

```bash
# Check detection
python -c "from orchestrator.utils.binary_discovery import BinaryDiscovery; d = BinaryDiscovery(); print(f'Codex: {d.find_codex()}'); print(f'Claude: {d.find_claude()}')"

# If not found, install AI CLI
# See getting-started.md for installation instructions
```

### Issue: Workspace conflicts

```bash
# Clean workspace between runs
rm -rf workspace/

# Or use custom workspace per run
export PARALLEL_CODING_WORKSPACE_ROOT=./build/workspace-$(date +%s)
```

### Issue: Performance

```bash
# Reduce workers
export PARALLEL_CODING_MAX_WORKERS=4

# Increase timeout for long tasks
export PARALLEL_CODING_WORKER_TIMEOUT=1800  # 30 minutes
```

---

## 📖 Documentation Links

- [getting-started.md](getting-started.md) - Installation & setup
- [configuration.md](configuration.md) - Configuration reference
- [../README.md](../README.md) - Complete orchestrator documentation
- [../CHANGELOG.md](../CHANGELOG.md) - Version history

---

## 🎓 Learning Path

1. ✅ Read [getting-started.md](getting-started.md) - Quick setup
2. ✅ Create simple task file (1 task, 1 worker)
3. ✅ Run and verify output
4. ✅ Create multi-task file (3-5 tasks, parallel)
5. ✅ Integrate results into your project
6. ✅ Scale up to full parallel (8-10 workers)
7. ✅ Add to CI/CD pipeline

---

## 🤝 Contributing

Contributions welcome! Please:
- Follow Python coding standards
- Include tests (≥90% coverage)
- Update documentation
- Follow semantic versioning

---

## 📝 License

MIT License - See [../LICENSE](../LICENSE)

---

**🚀 Ready to accelerate your development with parallel AI coding!**

**Version**: 2.0.0-dev
**Status**: ✅ Production Ready
**Cross-Project Compatible**: ✅ YES

For detailed configuration options, see [configuration.md](configuration.md).

Happy parallel coding! 🚀
