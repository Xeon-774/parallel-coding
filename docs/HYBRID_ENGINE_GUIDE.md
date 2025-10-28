# Hybrid Decision Engine - User Guide

**Version**: 1.0
**Date**: 2025-10-23
**Status**: Production Ready ✅

---

## 📋 Overview

The **Hybrid Decision Engine** combines the best of both worlds:
- **Rule-based safety checks** (< 1ms) for common cases
- **AI judgment** (~7-30s) for complex decisions
- **Template fallback** (< 1ms) for error resilience

This design ensures both **speed** and **intelligence** in orchestrating parallel AI workers.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│         Hybrid Decision Engine                           │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────┐          ┌────────────────┐         │
│  │  Safety Rules  │          │ Orchestrator   │         │
│  │  Engine        │          │ AI (Claude)    │         │
│  │                │          │                │         │
│  │ - File ops     │          │ - Complex      │         │
│  │ - Package mgmt │          │   decisions    │         │
│  │ - Cmd safety   │          │ - Context-aware│         │
│  │                │          │ - Nuanced      │         │
│  └────────────────┘          └────────────────┘         │
│         ↓ ~0.1ms                    ↓ ~27s              │
│         └──────────┬────────────────┘                    │
│                    ↓                                     │
│         Decision Router                                  │
│         - Simple → Rules (instant)                       │
│         - Complex → AI (thoughtful)                      │
│         - Error → Template (safe)                        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Basic Usage

```python
from pathlib import Path
from orchestrator.core.hybrid_engine import (
    HybridDecisionEngine,
    ConfirmationType,
    ConfirmationRequest
)

# Initialize engine
engine = HybridDecisionEngine(
    workspace_root=Path("/path/to/workspace"),
    wsl_distribution="Ubuntu-24.04",  # For Claude CLI
    verbose=True  # Enable logging
)

# Create a request
request = ConfirmationRequest(
    confirmation_type=ConfirmationType.FILE_WRITE,
    message="I want to create a file 'models/user.py' with database model code.",
    details={'file': 'workspace/models/user.py'}
)

# Make a decision
decision = await engine.decide(
    worker_id='worker_001',
    request=request,
    context={
        'task_name': 'Database models implementation',
        'project_name': 'AI_Investor',
        'project_goal': 'Build AI-powered investment platform MVP'
    }
)

# Check result
print(f"Action: {decision.action}")  # "approve" or "deny"
print(f"Decided by: {decision.decided_by}")  # "rules", "ai", or "template"
print(f"Reasoning: {decision.reasoning}")
print(f"Latency: {decision.latency_ms:.1f}ms")
```

---

## 📊 Request Types

### ConfirmationType Enum

```python
class ConfirmationType(Enum):
    FILE_WRITE = "file_write"        # Creating/modifying files
    FILE_READ = "file_read"          # Reading files
    FILE_DELETE = "file_delete"      # Deleting files
    PACKAGE_INSTALL = "package_install"  # Installing packages
    COMMAND_EXECUTE = "command_execute"  # Running system commands
    GENERAL = "general"              # Complex decisions
```

---

## 🎯 Decision Flow

### 1. Rule-Based Approval (Fast Path)

**Automatically approved** by rules (< 1ms):

✅ **File Creation** in workspace
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.FILE_WRITE,
    message="Create models/user.py",
    details={'file': 'workspace/models/user.py'}
)
# → APPROVED by rules in 0.2ms
```

✅ **File Reading** in workspace
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.FILE_READ,
    message="Read config.yaml",
    details={'file': 'workspace/config.yaml'}
)
# → APPROVED by rules in 0.1ms
```

✅ **Package Installation** from requirements.txt
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.PACKAGE_INSTALL,
    message="Install pytest",
    details={'package': 'pytest'}
)
# → APPROVED by rules in 0.2ms (if pytest is in requirements.txt)
```

### 2. Rule-Based Denial (Fast Path)

**Automatically denied** by rules (< 1ms):

❌ **Important File Deletion**
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.FILE_DELETE,
    message="Delete config.py",
    details={'file': 'config.py'}
)
# → DENIED by rules in 0.0ms
```

Important files:
- `.git/`
- `config.py`, `settings.py`
- `.env`
- `requirements.txt`
- `setup.py`, `pyproject.toml`

❌ **Dangerous Commands**
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.COMMAND_EXECUTE,
    message="Clean up",
    details={'command': 'rm -rf /'}
)
# → DENIED by rules in 0.0ms
```

Dangerous commands:
- `rm -rf`
- `del /f /s /q`
- `format`
- `dd if=`
- `mkfs`

### 3. AI Judgment (Smart Path)

**Routed to AI** when rules are inconclusive (~7-30s):

🤖 **Complex Decisions**
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.GENERAL,
    message="Refactor database connection pooling to use asyncio?",
    details={'scope': 'multiple files', 'complexity': 'high'}
)
# → AI decides in ~27s with thoughtful reasoning
```

AI provides:
- Context-aware decisions
- Detailed reasoning
- Project-specific insights

### 4. Template Fallback (Error Resilience)

**Used when AI fails** (< 1ms):

⚠️ **API Error / Timeout**
```python
# If Claude CLI fails or times out:
# → Template provides safe default based on operation type
# FILE_WRITE/READ: approve (safe operations)
# FILE_DELETE: deny (cautious approach)
# PACKAGE_INSTALL: approve (if from requirements.txt context)
```

---

## 📈 Performance Metrics

### Test Results

| Test Case | Decided By | Latency | Action |
|-----------|-----------|---------|--------|
| Safe file creation | Rules | 0.2ms | APPROVE ✅ |
| Important file deletion | Rules | 0.0ms | DENY ❌ |
| Dangerous command | Rules | 0.0ms | DENY ❌ |
| Complex refactoring | AI | 27,031ms | DENY ❌ |
| Package from requirements | Rules | 0.2ms | APPROVE ✅ |

### Statistics

```python
stats = engine.get_stats()

# Returns:
{
    'total_decisions': 6,
    'rules_decisions': 5,           # 83.3% handled by rules
    'ai_decisions': 1,              # 16.7% required AI
    'template_fallbacks': 0,        # 0% errors
    'average_latency_ms': 4505.4,   # Weighted average
    'rules_percentage': 83.3
}
```

**Key Insights:**
- **83%** of decisions handled by rules (instant)
- **17%** required AI judgment (thoughtful)
- **0%** fallbacks (high reliability)
- Average latency heavily influenced by AI calls

---

## 🔧 Configuration

### Initialization Options

```python
engine = HybridDecisionEngine(
    workspace_root=Path("/path/to/workspace"),  # Required
    wsl_distribution="Ubuntu-24.04",             # For Claude CLI
    verbose=True                                 # Enable detailed logging
)
```

### Context Parameters

```python
decision = await engine.decide(
    worker_id='worker_001',      # Required: Worker identifier
    request=request,             # Required: ConfirmationRequest
    context={                    # Optional: Additional context
        'task_name': 'Feature implementation',
        'project_name': 'AI_Investor',
        'project_goal': 'Build MVP',
        # Any custom fields...
    }
)
```

---

## 🛡️ Safety Rules

### File Operations

**Safe (Auto-approve):**
- Create files in workspace
- Read files in workspace
- Modify files in workspace

**Unsafe (Auto-deny):**
- Delete important config files
- Access files outside workspace
- Modify system files

### Package Management

**Safe (Auto-approve):**
- Install packages listed in `requirements.txt`

**Needs AI Judgment:**
- Install packages NOT in `requirements.txt`
- Upgrade critical dependencies
- Remove packages

### Command Execution

**Unsafe (Auto-deny):**
- `rm -rf`, `del /f /s /q`
- `format`, `mkfs`
- `dd if=`, `> /dev/sda`
- System-level destructive commands

**Needs AI Judgment:**
- Custom scripts
- Build commands
- Database migrations

---

## 📝 Best Practices

### 1. Request Design

**Good Request:**
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.FILE_WRITE,
    message="I need to create 'models/user.py' with the User database model. This is part of the database layer setup.",
    details={
        'file': 'workspace/models/user.py',
        'purpose': 'database model',
        'size_estimate': 'small (~100 lines)'
    }
)
```

**Bad Request:**
```python
ConfirmationRequest(
    confirmation_type=ConfirmationType.GENERAL,
    message="Create file?",  # Too vague
    details={}               # No context
)
```

### 2. Context Provision

Always provide context for AI decisions:
```python
context = {
    'worker_id': 'worker_001',
    'task_name': 'Database models implementation',
    'project_name': 'AI_Investor',
    'project_goal': 'Build AI-powered investment platform MVP',
    'current_phase': 'MVP Phase 1',
    'deadline': '2025-11-01'
}
```

### 3. Error Handling

```python
try:
    decision = await engine.decide(worker_id, request, context)

    if decision.is_fallback:
        print(f"Warning: Using template fallback - {decision.reasoning}")

    if decision.action == "approve":
        # Proceed with operation
        pass
    else:
        # Operation denied
        print(f"Denied: {decision.reasoning}")

except Exception as e:
    # Complete failure - orchestrator unresponsive
    print(f"Critical: {e}")
    # Stop worker or escalate
```

### 4. Monitoring

```python
# Periodically check statistics
stats = engine.get_stats()

if stats['template_fallbacks'] > stats['total_decisions'] * 0.1:
    # More than 10% fallbacks - investigate AI issues
    print("Warning: High fallback rate")

if stats['rules_percentage'] < 50:
    # Less than 50% rules - may need more rules
    print("Warning: Low rule coverage")
```

---

## 🧪 Testing

### Run Test Suite

```bash
cd tools/parallel-coding
python tests/test_hybrid_engine.py
```

### Test Coverage

✅ Rule-based approval
✅ Rule-based denial
✅ Dangerous command detection
✅ AI judgment for complex cases
✅ Package installation from requirements
✅ Statistics tracking

---

## 🔍 Troubleshooting

### Issue: High AI Latency

**Symptom**: AI decisions taking > 60s

**Solutions:**
1. Check WSL Claude CLI installation
2. Verify network connectivity
3. Consider increasing timeout in `cli_orchestrator.py`
4. Add more rules to reduce AI calls

### Issue: High Fallback Rate

**Symptom**: `template_fallbacks` > 10%

**Solutions:**
1. Check Claude CLI authentication
2. Verify WSL distribution is running
3. Review Claude CLI logs
4. Check system resources

### Issue: Wrong Rule Decisions

**Symptom**: Rules approving dangerous operations

**Solutions:**
1. Review `SafetyRulesEngine._check_dangerous_patterns()`
2. Add new patterns to `dangerous_patterns` list
3. Update important file patterns
4. Test edge cases

---

## 📚 API Reference

### Classes

#### `HybridDecisionEngine`

Main engine class combining rules + AI + templates.

**Methods:**
- `async decide(worker_id, request, context)` → `Decision`
- `get_stats()` → `Dict[str, Any]`

#### `SafetyRulesEngine`

Fast rule-based evaluation.

**Methods:**
- `evaluate(request)` → `RuleResult`

#### `CLIOrchestratorAI`

Claude CLI-based orchestrator AI.

**Methods:**
- `async ask(question, context)` → `AIDecision`

#### `ErrorTemplates`

Fallback response templates.

**Methods:**
- `get_api_error_template(request)` → `Template`
- `get_timeout_template(request)` → `Template`

### Data Classes

#### `ConfirmationRequest`
- `confirmation_type: ConfirmationType`
- `message: str`
- `details: Dict[str, Any]`

#### `Decision`
- `action: str` - "approve" or "deny"
- `reasoning: str`
- `latency_ms: float`
- `is_fallback: bool`
- `decided_by: str` - "rules", "ai", or "template"

#### `RuleResult`
- `is_definitive: bool`
- `action: Optional[str]`
- `reason: str`
- `duration_ms: float`

---

## 🎓 Examples

See `tests/test_hybrid_engine.py` for comprehensive examples covering:
- All confirmation types
- Rule-based decisions
- AI judgment scenarios
- Statistics tracking
- Error handling

---

## 📊 Production Metrics

**From Phase 0 Testing:**

| Metric | Value |
|--------|-------|
| Rule decisions | 83.3% |
| AI decisions | 16.7% |
| Template fallbacks | 0% |
| Average rule latency | 0.1ms |
| Average AI latency | 27s |
| Overall average latency | 4.5s |

**Expected in Production (with 8 workers):**

| Metric | Expected Value |
|--------|---------------|
| Rule decisions | 85-90% |
| AI decisions | 10-15% |
| Template fallbacks | < 2% |
| Average latency | < 2s |
| Throughput | ~400 decisions/hour |

---

## 🔄 Version History

### v1.0 (2025-10-23)
- ✅ Initial implementation
- ✅ Rule-based safety engine
- ✅ Claude CLI orchestrator integration
- ✅ Template fallback system
- ✅ Comprehensive test suite
- ✅ Statistics tracking

---

## 📖 References

- [FINAL_DESIGN_SPECIFICATION.md](../FINAL_DESIGN_SPECIFICATION.md)
- [CLI_ONLY_DESIGN.md](../CLI_ONLY_DESIGN.md)
- [cli_orchestrator.py](../orchestrator/core/cli_orchestrator.py)
- [test_hybrid_engine.py](../tests/test_hybrid_engine.py)

---

**Status**: Production Ready ✅
**Tested**: 6/6 tests passing
**Performance**: Meets all design criteria
**Reliability**: 100% success rate in testing