# Interactive Mode Guide - Claude Orchestrator v8.0

**Revolutionary Feature**: Full bidirectional communication between orchestrator AI and worker AIs

---

## 🎯 Problem Solved

### Previous Architecture (v7.0 and earlier)

```
Orchestrator → Worker AI (one-way, non-interactive)
                  ↓
              --dangerously-skip-permissions (危険！)
                  ↓
              Auto-approves everything
                  ↓
              Cannot respond to errors
```

**Problems**:
- ❌ Worker AIs cannot ask for clarification
- ❌ All operations auto-approved (`--dangerously-skip-permissions`)
- ❌ No error recovery or intervention
- ❌ Dangerous operations executed without judgment

### New Architecture (v8.0)

```
┌─────────────────────────────────────────────────────────┐
│  Orchestrator AI                                        │
│  ・Monitors worker output continuously                   │
│  ・Detects confirmation requests                         │
│  ・Judges safety with AI reasoning                       │
│  ・Responds intelligently or escalates                   │
└─────────────────────────────────────────────────────────┘
         ↕ (Full bidirectional communication)
         │ stdin/stdout - continuous dialog
         │
┌─────────────────────────────────────────────────────────┐
│  Worker AI (Interactive Mode)                           │
│  ・Executes tasks                                        │
│  ・Asks for confirmation when needed                     │
│  ・Reports errors and waits for instructions            │
│  ・Receives guidance from orchestrator                   │
└─────────────────────────────────────────────────────────┘
         │
         ↓ (If dangerous or unclear)
┌─────────────────────────────────────────────────────────┐
│  User / Higher-level AI                                 │
│  ・Approves/denies dangerous operations                  │
│  ・Provides domain-specific judgment                     │
│  ・Handles exceptional cases                             │
└─────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Worker AIs can ask questions and get answers
- ✅ `--dangerously-skip-permissions` **removed** (安全！)
- ✅ AI judges each operation for safety
- ✅ Dangerous operations escalated to user
- ✅ Error recovery through dialog
- ✅ Adaptive problem-solving

---

## 🔧 Key Components

### 1. InteractiveWorkerManager

**Purpose**: Manages workers in interactive mode with full communication

**Key Features**:
```python
from orchestrator.core.interactive_worker_manager import InteractiveWorkerManager

manager = InteractiveWorkerManager(
    config=config,
    logger=logger,
    user_approval_callback=user_approval_function
)

# Spawn worker WITHOUT --dangerously-skip-permissions
worker = manager.spawn_interactive_worker(
    worker_id="worker_1",
    task={"name": "Create API", "prompt": "..."}
)

# Manager automatically:
# - Monitors worker output for confirmation requests
# - Detects questions and errors
# - Responds intelligently
# - Escalates dangerous operations
```

**Communication Flow**:
1. Worker asks: "Write to file 'output.py'?"
2. Orchestrator detects confirmation request
3. AI Safety Judge evaluates: "Safe - in workspace"
4. Orchestrator responds: "yes"
5. Worker continues execution

### 2. AISafetyJudge

**Purpose**: AI-powered safety assessment of operations

**Key Features**:
```python
from orchestrator.core.ai_safety_judge import AISafetyJudge, SafetyLevel

judge = AISafetyJudge(workspace_root="./workspace")

# Judge a confirmation request
judgment = judge.judge_confirmation(confirmation_request)

# judgment contains:
# - level: SAFE, CAUTION, DANGEROUS, PROHIBITED
# - should_approve: bool
# - should_escalate: bool (to user)
# - reasoning: str (explanation)
# - suggested_modifications: Optional[str]
```

**Safety Levels**:

| Level | Decision | Example |
|-------|----------|---------|
| **SAFE** | Auto-approve | Writing to workspace file |
| **CAUTION** | Approve with warning | Unknown file type in workspace |
| **DANGEROUS** | Escalate to user | Deleting files, executing commands |
| **PROHIBITED** | Always deny | `rm -rf /`, system file modifications |

### 3. ConfirmationRequest

**Purpose**: Structured representation of worker requests

```python
@dataclass
class ConfirmationRequest:
    worker_id: str                    # Which worker
    confirmation_type: ConfirmationType  # Type of operation
    message: str                      # Original message
    details: Dict[str, str]           # Parsed details
    timestamp: float                  # When requested

# Types:
# - FILE_WRITE: Writing files
# - FILE_DELETE: Deleting files
# - COMMAND_EXECUTE: Running commands
# - PACKAGE_INSTALL: Installing packages
# - UNKNOWN: Other confirmations
```

---

## 📋 Usage Examples

### Example 1: Basic Interactive Execution

```python
from orchestrator.core.interactive_worker_manager import InteractiveWorkerManager
from orchestrator.core.ai_safety_judge import AISafetyJudge
from orchestrator.config import OrchestratorConfig

# Setup
config = OrchestratorConfig.from_env()
judge = AISafetyJudge(workspace_root=config.workspace_root)

def user_approval(confirmation):
    """Called when operation needs user approval"""
    print(f"\n⚠️  Approval needed:")
    print(f"   {confirmation.message}")

    response = input("   Approve? (y/n): ")
    return response.lower() == 'y'

manager = InteractiveWorkerManager(
    config=config,
    logger=logger,
    user_approval_callback=user_approval
)

# Execute task
task = {
    "name": "Create Todo API",
    "prompt": """
    Create a REST API for todo management with:
    - FastAPI framework
    - CRUD endpoints
    - SQLite database
    - Write files to workspace/todo_api/
    """
}

worker = manager.spawn_interactive_worker("worker_1", task)
results = manager.wait_for_completion(timeout=300)

print(f"Result: {results[0].success}")
```

**What happens**:
1. Worker starts executing task
2. Worker: "Write to file 'workspace/todo_api/main.py'?"
3. AI Judge: "SAFE - in workspace, Python file"
4. Orchestrator: Responds "yes" automatically
5. Worker continues...
6. Worker: "Delete file '/__init__.py'?"
7. AI Judge: "DANGEROUS - delete operation"
8. Orchestrator: Escalates to user
9. User: Approves or denies
10. Worker receives response and continues

### Example 2: Error Recovery

```python
# Worker encounters error during execution

# Worker output:
# "Error: Module 'requests' not found"
# "Should I install it? (y/n)"

# Orchestrator detects question
# AI Judge: "SAFE - package install"
# Orchestrator responds: "yes"

# Worker continues:
# "Installing requests..."
# "Retrying import..."
# "Success!"
```

### Example 3: Dangerous Operation Prevention

```python
# Worker asks to execute dangerous command

# Worker output:
# "Execute command 'rm -rf /'? (y/n)"

# Orchestrator detects confirmation
# AI Judge analyzes: "rm -rf /"
# Judgment: PROHIBITED - recursive delete of root

# Orchestrator responds: "no"
# Orchestrator logs: "Blocked dangerous operation"

# Worker receives denial:
# "Operation denied. Continuing with alternative approach..."
```

---

## 🎨 Safety Decision Tree

```
Confirmation Request Detected
        ↓
    AI Safety Judge
        ↓
   ┌────┴────┬────────┬────────┐
   │         │        │        │
  SAFE    CAUTION  DANGEROUS  PROHIBITED
   │         │        │        │
   │         │        │        │
Auto-     Auto-    Escalate   Always
Approve   Approve   to User    Deny
   │         │        │        │
   └─────────┴────────┴────────┘
              ↓
        Response sent to worker
              ↓
        Worker continues
```

---

## 🔐 Security Benefits

### Removed Dangerous Flag

**Before (v7.0)**:
```bash
claude --print --dangerously-skip-permissions < task.txt
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                Bypasses ALL safety checks!
```

**After (v8.0)**:
```bash
claude --print < task.txt
#      Only non-interactive output mode
#      All operations require approval
```

### AI-Powered Safety

Instead of blindly approving everything, each operation is:

1. **Detected**: Pattern matching finds confirmation requests
2. **Parsed**: Details extracted (file paths, commands, etc.)
3. **Judged**: AI analyzes safety based on:
   - Operation type
   - Target location (workspace vs system)
   - Command content
   - Historical context
4. **Decided**: Auto-approve, approve with caution, or escalate
5. **Logged**: All decisions recorded for audit

### Defense in Depth

```
Layer 1: Worker AI (asks for confirmation)
   ↓
Layer 2: Orchestrator AI (judges safety)
   ↓
Layer 3: User approval (for dangerous ops)
   ↓
Layer 4: Operating system (final protection)
```

---

## 📊 Comparison: v7.0 vs v8.0

| Feature | v7.0 (Old) | v8.0 (New) |
|---------|------------|------------|
| **Worker Communication** | One-way (stdin only) | Bidirectional (stdin/stdout) |
| **Permission Handling** | `--dangerously-skip-permissions` | Individual judgment |
| **Safety Assessment** | None (approve all) | AI-powered analysis |
| **Error Recovery** | Timeout and terminate | Dialog and resolution |
| **User Involvement** | Never | When needed |
| **Dangerous Operations** | Auto-executed | Blocked or escalated |
| **Audit Trail** | Basic logging | Detailed decision logs |
| **Worker Questions** | Cannot respond | Full dialog |

---

## 🚀 Migration from v7.0 to v8.0

### For Existing Code

**v7.0 Code**:
```python
from orchestrator import AdvancedOrchestrator

orchestrator = AdvancedOrchestrator(config=config)
result = orchestrator.execute("Create an API")
```

**v8.0 Code (Interactive)**:
```python
from orchestrator.core.interactive_worker_manager import InteractiveWorkerManager

manager = InteractiveWorkerManager(
    config=config,
    logger=logger,
    user_approval_callback=user_approval_func
)

worker = manager.spawn_interactive_worker("worker_1", task)
results = manager.wait_for_completion()
```

### Backward Compatibility

v7.0 mode still available for:
- Fully automated scenarios
- Trusted environments
- Legacy compatibility

Use `WorkerManager` (v7.0) for non-interactive mode.
Use `InteractiveWorkerManager` (v8.0) for interactive mode.

---

## 💡 Best Practices

### 1. Define User Approval Callback

```python
def smart_user_approval(confirmation: ConfirmationRequest) -> bool:
    """Intelligent user approval with context"""

    # Show detailed information
    print(f"\n{'='*60}")
    print(f"APPROVAL REQUEST from {confirmation.worker_id}")
    print(f"Type: {confirmation.confirmation_type}")
    print(f"Message: {confirmation.message}")

    # Get AI safety judgment
    judge = AISafetyJudge(workspace_root="./workspace")
    judgment = judge.judge_confirmation(confirmation)

    print(f"\nAI Safety Assessment:")
    print(f"  Level: {judgment.level}")
    print(f"  Reasoning: {judgment.reasoning}")

    if judgment.suggested_modifications:
        print(f"  Suggestion: {judgment.suggested_modifications}")

    # Ask user
    response = input("\nApprove? (y/n/explain): ").strip().lower()

    if response == 'explain':
        print(judge.explain_decision(judgment))
        response = input("\nApprove? (y/n): ").strip().lower()

    return response == 'y'
```

### 2. Custom Safety Rules

```python
class CustomSafetyJudge(AISafetyJudge):
    """Extended safety judge with domain-specific rules"""

    def _judge_file_write(self, confirmation, context):
        # Add custom logic
        if "production" in confirmation.details.get("file", ""):
            return SafetyJudgment(
                level=SafetyLevel.PROHIBITED,
                should_approve=False,
                should_escalate=True,
                reasoning="Never write to production files"
            )

        # Fall back to parent logic
        return super()._judge_file_write(confirmation, context)
```

### 3. Logging and Audit

```python
# All decisions are logged automatically
logger.info(
    f"Safety decision",
    worker_id=confirmation.worker_id,
    type=confirmation.confirmation_type,
    decision="approved",
    level=judgment.level,
    reasoning=judgment.reasoning
)

# Review audit trail
# workspace/logs/orchestrator_*.jsonl contains:
# - All confirmation requests
# - AI safety judgments
# - User approvals/denials
# - Timestamps and reasoning
```

---

## 🚀 Enhanced Implementation (pexpect/wexpect)

### Overview

v8.0 now uses **pexpect** (Unix/Linux) and **wexpect** (Windows) for robust pseudo-terminal control, replacing the basic subprocess.Popen() approach.

### Why pexpect/wexpect?

**Previous approach (subprocess.Popen)**:
- ❌ Manual pattern matching on stdout
- ❌ Complex threading for I/O monitoring
- ❌ Unreliable detection of confirmation requests
- ❌ Difficult timeout handling

**New approach (pexpect/wexpect)**:
- ✅ Built-in pattern matching with regex
- ✅ Native pseudo-terminal (PTY) support
- ✅ Robust expect() mechanism
- ✅ Easy timeout and EOF handling
- ✅ Cross-platform support

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  EnhancedInteractiveWorkerManager                        │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Platform Detection                                 │ │
│  │  - Windows → import wexpect                         │ │
│  │  - Unix/Linux → import pexpect                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                     ↓                                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Worker Spawning                                    │ │
│  │  - spawn() with encoding='utf-8'                    │ │
│  │  - NO --dangerously-skip-permissions                │ │
│  │  - Real terminal environment                        │ │
│  └─────────────────────────────────────────────────────┘ │
│                     ↓                                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Interactive Loop                                   │ │
│  │  - expect([patterns...])                            │ │
│  │  - Pattern matching with regex groups               │ │
│  │  - Capture matched text and details                 │ │
│  └─────────────────────────────────────────────────────┘ │
│                     ↓                                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Confirmation Handling                              │ │
│  │  - Parse confirmation type from pattern             │ │
│  │  - Call AISafetyJudge for decision                  │ │
│  │  - sendline() response to worker                    │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Key Implementation Details

#### 1. Cross-Platform Module Import

```python
import sys

if sys.platform == 'win32':
    import wexpect as expect_module
    PLATFORM = 'windows'
else:
    import pexpect as expect_module
    PLATFORM = 'unix'
```

This allows the same code to work on both Windows and Unix/Linux.

#### 2. Worker Spawning with Pseudo-Terminal

```python
# Spawn with real terminal environment
child = expect_module.spawn(
    cmd,
    encoding='utf-8',  # UTF-8 for international support
    timeout=timeout     # Default timeout for expect operations
)
```

**Benefits**:
- Real terminal environment (Claude CLI expects this)
- Automatic encoding handling
- Configurable timeout

#### 3. Pattern-Based Confirmation Detection

```python
# Define patterns with regex groups to capture details
confirmation_patterns = [
    # File write: captures filename in group 1
    (r"(?i)write\s+(?:to\s+)?(?:file\s+)?['\"]([^'\"]+)['\"].*\?",
     ConfirmationType.FILE_WRITE),

    # File delete: captures filename in group 1
    (r"(?i)delete\s+(?:file\s+)?['\"]([^'\"]+)['\"].*\?",
     ConfirmationType.FILE_DELETE),

    # Command execution: captures command in group 1
    (r"(?i)execute\s+(?:command\s+)?['\"]([^'\"]+)['\"].*\?",
     ConfirmationType.COMMAND_EXECUTE),
]

# Use in expect loop
patterns = [p[0] for p in confirmation_patterns]
patterns.append(expect_module.EOF)
patterns.append(expect_module.TIMEOUT)

# Wait for pattern match
index = child.expect(patterns, timeout=30)
```

**Features**:
- Case-insensitive matching (`(?i)`)
- Flexible whitespace handling
- Regex groups for detail extraction
- Automatic EOF/TIMEOUT handling

#### 4. Interactive Session Loop

```python
def run_interactive_session(self, worker_id, max_iterations=100):
    """Run interactive session for a worker"""

    session = self.workers.get(worker_id)
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Build pattern list
        patterns = [p[0] for p in self.confirmation_patterns]
        patterns.extend([expect_module.EOF, expect_module.TIMEOUT])

        # Wait for pattern match
        index = session.child_process.expect(patterns, timeout=30)

        # Capture output
        before_text = session.child_process.before
        session.output_lines.append(before_text)

        # Check for completion
        if index == len(patterns) - 2:  # EOF
            break

        # Check for timeout
        if index == len(patterns) - 1:  # TIMEOUT
            continue  # Keep waiting

        # Confirmation detected
        confirmation = self._parse_confirmation(worker_id, index, session.child_process)

        if confirmation:
            # Get AI safety judgment
            response = self._handle_confirmation(confirmation)

            # Send response
            if response:
                session.child_process.sendline(response)
```

**Flow**:
1. Build list of patterns to watch for
2. Wait for match with `expect()`
3. Capture all output before match
4. Check if EOF (completed) or TIMEOUT
5. Parse confirmation from matched pattern
6. Get AI safety judgment
7. Send response with `sendline()`
8. Loop continues

#### 5. Detail Extraction from Regex Groups

```python
def _parse_confirmation(self, worker_id, pattern_index, child_process):
    """Parse confirmation from matched pattern"""

    pattern, conf_type = self.confirmation_patterns[pattern_index]

    # Get matched text
    matched_text = child_process.after

    # Get regex match object with groups
    match = child_process.match

    details = {}

    if match and match.groups():
        # Extract from first group
        target = match.group(1) if len(match.groups()) >= 1 else ""

        # Store based on type
        if conf_type == ConfirmationType.FILE_WRITE:
            details["file"] = target
        elif conf_type == ConfirmationType.COMMAND_EXECUTE:
            details["command"] = target

    return ConfirmationRequest(
        worker_id=worker_id,
        confirmation_type=conf_type,
        message=matched_text.strip(),
        details=details
    )
```

**Advantages**:
- Automatic regex group extraction
- Type-specific detail parsing
- Clean separation of concerns

### Testing

#### Basic Functionality Test

```bash
# Test pexpect/wexpect basic functionality
python scripts/test_pexpect_basic.py
```

**Results**:
- ✅ Command execution works
- ✅ Pattern matching works
- ✅ Interactive Q&A works

#### Mock Claude CLI Test

```bash
# Test with simulated Claude CLI
python scripts/test_with_mock_claude.py
```

**Purpose**:
- Validate EnhancedInteractiveWorkerManager
- Test confirmation detection
- Verify AI safety judgment integration

#### Actual Claude CLI Test

```bash
# Test with real Claude CLI (requires Claude CLI installed)
python scripts/test_enhanced_interactive.py
```

**Purpose**:
- Capture actual Claude CLI confirmation formats
- Tune regex patterns
- Validate end-to-end flow

### Pattern Tuning

After running tests with actual Claude CLI, check these files:

```
workspace/confirmation_requests.log      # All detected confirmations
workspace/test_enhanced_interactive.log  # Full test log
workspace/worker_*/full_output.txt       # Complete worker output
```

Use this information to refine the regex patterns in:
```
orchestrator/core/enhanced_interactive_worker_manager.py
```

### Performance Benefits

| Metric | subprocess.Popen() | pexpect/wexpect |
|--------|-------------------|-----------------|
| **Pattern Matching** | Manual regex + threading | Built-in expect() |
| **Timeout Handling** | Complex thread coordination | Native timeout parameter |
| **EOF Detection** | Manual poll() loop | Automatic EOF exception |
| **Terminal Support** | Limited | Full PTY support |
| **Code Complexity** | High (500+ lines) | Medium (300 lines) |
| **Reliability** | Moderate | High |

### Dependencies

Added to `requirements.txt`:

```txt
# Interactive Terminal Control (v8.0)
pexpect>=4.8.0        # Unix/Linux pseudo-terminal control
wexpect>=4.0.0        # Windows pseudo-terminal control
```

**Installation**:
```bash
pip install -r requirements.txt
```

### Migration from Basic InteractiveWorkerManager

**Old (basic)**:
```python
from orchestrator.core.interactive_worker_manager import InteractiveWorkerManager

manager = InteractiveWorkerManager(config, logger, user_approval_callback)
worker = manager.spawn_interactive_worker("worker_1", task)
results = manager.wait_for_completion()
```

**New (enhanced with pexpect/wexpect)**:
```python
from orchestrator.core.enhanced_interactive_worker_manager import (
    EnhancedInteractiveWorkerManager
)

manager = EnhancedInteractiveWorkerManager(config, logger, user_approval_callback)
session = manager.spawn_worker("worker_1", task)
result = manager.run_interactive_session(session.worker_id)
```

**Benefits of migration**:
- ✅ More reliable pattern matching
- ✅ Better timeout handling
- ✅ Real terminal environment
- ✅ Cross-platform support
- ✅ Cleaner code

---

## 🎓 Conclusion

v8.0 Interactive Mode fundamentally changes the orchestrator-worker relationship from:

**One-way command execution** → **Collaborative problem-solving dialog**

This enables:
- ✅ **Safety**: Intelligent approval instead of blind execution
- ✅ **Adaptability**: Workers can ask for guidance and recover from errors
- ✅ **Transparency**: Clear reasoning for all decisions
- ✅ **Control**: User involvement when truly needed
- ✅ **Audit**: Complete trail of all decisions

The system is now **truly intelligent** - workers and orchestrator work together,
making informed decisions, with human oversight when necessary.

---

**Version**: 8.0.0 (Proposed)
**Status**: Implementation Complete, Testing Pending
**Documentation**: This Guide
