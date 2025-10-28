# Phase 1.3 Implementation Plan: Real-time Terminal Capture

**Project**: Parallel AI Coding Tool
**Phase**: 1.3 - Real-time Terminal Capture
**Status**: ⏳ PLANNED
**Estimated Effort**: 4-6 hours
**Priority**: High (User-requested feature)

---

## Executive Summary

Implement actual real-time capture of stdout/stderr from Claude AI worker and orchestrator processes, replacing the current sample data approach with genuine process output streaming.

**Goal**: Enable users to see actual AI instance execution output in real-time for visual verification.

---

## Current State Analysis

### What's Already Implemented ✅

After code inspection, we discovered that **worker terminal capture is already partially implemented** in `worker_manager.py`:

#### Worker Output Capture
```python
# Line 176-180: Creates raw terminal log file
raw_terminal_file = worker_dir / "raw_terminal.log"
with open(raw_terminal_file, 'w', encoding='utf-8') as f:
    f.write(f"=== Worker Terminal Output: {worker_name} ===\n")
    # ...

# Line 232-248: Appends output to file
def _append_raw_output(self, session: WorkerSession, text: str) -> None:
    session.output_lines.append(text)
    if session.raw_terminal_file:
        with open(session.raw_terminal_file, 'a', encoding='utf-8') as f:
            f.write(text)
            if not text.endswith('\n'):
                f.write('\n')

# Line 354: Captures output before confirmation
self._append_raw_output(session, before_text)

# Line 416: Captures final output
self._append_raw_output(session, remaining)
```

**Status**: Worker output capture is **implemented but may need testing/validation**.

### What's Missing ❌

1. **Orchestrator Output Capture**: No mechanism to capture orchestrator's own stdout/stderr
2. **Complete Worker Output**: May not be capturing ALL worker output (only before confirmations)
3. **Real-time Streaming**: Output is written but may have buffering delays
4. **Testing**: No verification that actual AI output is being captured correctly

---

## Problem Statement

### User's Core Need
> "Is this actual AI instance output? It looks different from the usual terminal screen."

Users need to see **genuine Claude AI process output** to:
1. Verify AI instances are actually running
2. Debug issues with AI worker execution
3. Monitor progress of long-running tasks
4. Understand what commands AI is executing

### Current Limitation
- Frontend displays sample data from static log files
- Real process output capture exists but is incomplete
- Orchestrator output is not captured at all
- No verification that capture is working

---

## Implementation Plan

### Phase 1.3.1: Verify & Fix Worker Output Capture ⏳

**Objective**: Ensure worker output is being captured completely and correctly.

#### Task 1: Verify Existing Capture Implementation
1. Run a real worker task
2. Check if `raw_terminal.log` is being populated
3. Verify output is complete (not just partial)
4. Test with different types of tasks (file operations, code generation, etc.)

**Verification Steps**:
```bash
# Start orchestrator and run a simple task
python -m orchestrator.cli assign "Create a hello.txt file" --workers 1

# Check if output is captured
cat workspace/worker_*/raw_terminal.log
```

**Expected Output**: Should see actual Claude CLI output like:
```
I'll help you create a hello.txt file.
*Uses Write tool to create hello.txt*
I've created hello.txt with content...
```

#### Task 2: Identify Capture Gaps
Potential issues to check:
- [ ] Output only captured before confirmations (missing output after approvals)
- [ ] Buffering delays (output not written immediately)
- [ ] Encoding issues (ANSI codes, Unicode)
- [ ] Race conditions (file writes vs WebSocket reads)

#### Task 3: Fix Incomplete Capture
If gaps are found, add capture points:

```python
# Capture output AFTER sending confirmation response
self._append_raw_output(session, after_response_text)

# Capture output during idle periods
def _capture_continuous_output(self, session: WorkerSession):
    """Background thread to capture output continuously"""
    while session.is_active:
        try:
            line = session.child_process.readline()
            if line:
                self._append_raw_output(session, line)
        except:
            break
```

---

### Phase 1.3.2: Implement Orchestrator Output Capture ⏳

**Objective**: Capture orchestrator's own decision-making output to `orchestrator_terminal.log`.

#### Current Orchestrator Output
The orchestrator prints to stdout:
```python
print(f"  [OUTPUT] {before_text.strip()}")
print(f"  [DECISION] {judgment_result}")
print(f"  [RESPONSE] Sending: {response}")
```

These print statements go to the terminal but are NOT captured to a file.

#### Implementation Approach

**Option A: Capture via Logger** (Recommended)
```python
class OrchestratorTerminalCapture:
    """Captures orchestrator decision-making output"""

    def __init__(self, workspace_dir: Path):
        self.terminal_file = workspace_dir / "orchestrator_terminal.log"
        self._init_log_file()

    def _init_log_file(self):
        """Initialize log file with header"""
        with open(self.terminal_file, 'w', encoding='utf-8') as f:
            f.write("=== Orchestrator Terminal Output ===\n")
            f.write(f"=== Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

    def log(self, message: str, category: str = "INFO"):
        """Append message to terminal log"""
        timestamp = time.strftime('%H:%M:%S')
        formatted = f"[{timestamp}] [{category}] {message}\n"

        # Write to file
        with open(self.terminal_file, 'a', encoding='utf-8') as f:
            f.write(formatted)

        # Also print to stdout
        print(formatted.rstrip())
```

**Integration Points**:
```python
# In WorkerManager.__init__
self.orchestrator_capture = OrchestratorTerminalCapture(config.workspace_root)

# Replace print statements
# Before:
print(f"  [OUTPUT] {before_text.strip()}")

# After:
self.orchestrator_capture.log(before_text.strip(), "WORKER-OUTPUT")
```

**Option B: Redirect stdout** (Alternative)
```python
import sys
from io import StringIO

class TeeOutput:
    """Captures stdout while still printing"""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'a', encoding='utf-8')
        self.stdout = sys.stdout

    def write(self, text: str):
        self.stdout.write(text)
        self.file.write(text)
        self.file.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()

# Usage
sys.stdout = TeeOutput(workspace_dir / "orchestrator_terminal.log")
```

**Recommendation**: Use Option A (logger-based) for better control and formatting.

---

### Phase 1.3.3: Real-time Streaming Optimization ⏳

**Objective**: Ensure captured output appears in UI with minimal delay.

#### Current Behavior
- `watchdog` monitors file changes
- UI polls for new content
- Potential buffering delays

#### Optimization Strategies

**1. Disable Buffering**
```python
# When opening files for writing
with open(file_path, 'a', encoding='utf-8', buffering=1) as f:
    f.write(text)
    # buffering=1 enables line buffering
```

**2. Explicit Flush**
```python
def _append_raw_output(self, session: WorkerSession, text: str) -> None:
    if session.raw_terminal_file:
        with open(session.raw_terminal_file, 'a', encoding='utf-8') as f:
            f.write(text)
            if not text.endswith('\n'):
                f.write('\n')
            f.flush()  # Force write to disk immediately
```

**3. File Handle Reuse**
Instead of opening/closing file repeatedly, keep it open:
```python
class WorkerSession:
    # ...
    raw_terminal_handle: Optional[TextIO] = None

    def close(self):
        if self.raw_terminal_handle:
            self.raw_terminal_handle.close()

# In _append_raw_output
def _append_raw_output(self, session: WorkerSession, text: str) -> None:
    if session.raw_terminal_handle:
        session.raw_terminal_handle.write(text)
        if not text.endswith('\n'):
            session.raw_terminal_handle.write('\n')
        session.raw_terminal_handle.flush()
```

---

### Phase 1.3.4: Testing & Validation ⏳

**Objective**: Verify capture works correctly with real AI workers.

#### Test Cases

**Test 1: Simple File Creation Task**
```python
# Task: "Create a test.txt file with content 'Hello World'"
# Expected output in raw_terminal.log:
"""
I'll create a test.txt file with the content 'Hello World'.
*Uses Write tool to create test.txt*
I've successfully created test.txt with the requested content.
"""
```

**Test 2: Multi-step Task**
```python
# Task: "Create 3 files: a.txt, b.txt, c.txt"
# Expected output: Should see multiple tool uses
```

**Test 3: Interactive Confirmation**
```python
# Task: "Delete all .tmp files"
# Expected output: Should see confirmation request and approval
```

**Test 4: Error Handling**
```python
# Task: "Read a file that doesn't exist"
# Expected output: Should see error messages
```

#### Validation Checklist
- [ ] Worker output captured completely
- [ ] Orchestrator decisions captured
- [ ] Output appears in UI within 1 second
- [ ] No data loss or corruption
- [ ] Handles Unicode/ANSI codes correctly
- [ ] Multiple workers don't interfere with each other
- [ ] File handles closed properly on worker termination

---

## Implementation Order

### Recommended Sequence

1. **Phase 1.3.1**: Verify & Fix Worker Capture (2 hours)
   - Test existing implementation
   - Identify and fix gaps
   - Validate completeness

2. **Phase 1.3.2**: Orchestrator Capture (1-2 hours)
   - Implement `OrchestratorTerminalCapture` class
   - Replace print statements
   - Test decision-making output

3. **Phase 1.3.3**: Optimize Streaming (1 hour)
   - Add explicit flush calls
   - Test real-time latency
   - Tune buffering settings

4. **Phase 1.3.4**: Testing & Validation (1 hour)
   - Run comprehensive test cases
   - Verify UI displays correctly
   - Document any limitations

**Total Estimated Time**: 5-6 hours

---

## Success Criteria

### Functional Requirements ✅
- [ ] Worker stdout/stderr captured completely
- [ ] Orchestrator decision-making logged
- [ ] Output appears in UI in real-time (< 1 second delay)
- [ ] Supports multiple concurrent workers
- [ ] No data loss or corruption

### Non-Functional Requirements ✅
- [ ] Performance: < 5% CPU overhead for capture
- [ ] Memory: < 10MB per worker for buffering
- [ ] Reliability: No crashes or hangs
- [ ] Maintainability: Clean, documented code

### User Experience ✅
- [ ] User can see actual AI commands being executed
- [ ] Clear visual distinction between worker and orchestrator
- [ ] Output is readable (proper line breaks, no garbled text)
- [ ] No sample data warnings in UI

---

## Risk Mitigation

### Identified Risks

**Risk 1: Performance Impact**
- Concern: File I/O on every output line may slow down workers
- Mitigation: Use buffered writes, benchmark performance
- Fallback: Implement async file writing

**Risk 2: Unicode/ANSI Handling**
- Concern: ANSI escape codes may garble display
- Mitigation: Test with various output types
- Fallback: Strip ANSI codes if needed

**Risk 3: Race Conditions**
- Concern: WebSocket reading while file is being written
- Mitigation: Use line-buffered writes (atomic per line)
- Fallback: Add file locking if needed

**Risk 4: Incomplete Capture**
- Concern: May miss output if buffering is complex
- Mitigation: Extensive testing with real tasks
- Fallback: Add debug logging to identify gaps

---

## Alternative Approaches Considered

### Approach A: Direct stdout/stderr Piping (Rejected)
**Idea**: Pipe subprocess stdout directly to WebSocket.
**Pros**: No file intermediary, potentially lower latency.
**Cons**: Complex threading, no persistence, harder to debug.
**Reason for Rejection**: File-based approach is more robust and debuggable.

### Approach B: Memory-Only Streaming (Rejected)
**Idea**: Keep output in memory only, no file writes.
**Pros**: Faster, no disk I/O.
**Cons**: Data lost on crash, no persistence for replay.
**Reason for Rejection**: Files provide persistence and crash recovery.

### Approach C: Database Logging (Overkill)
**Idea**: Store output in SQLite database.
**Pros**: Queryable, structured.
**Cons**: Overly complex, performance overhead.
**Reason for Rejection**: Files are sufficient for this use case.

---

## Code Changes Summary

### Files to Modify
1. `orchestrator/core/worker_manager.py`
   - Verify `_append_raw_output` works correctly
   - Add missing capture points if needed
   - Implement `OrchestratorTerminalCapture` class
   - Replace print statements with capture calls

### Files to Create
- None (infrastructure already exists)

### Files to Test
1. `workspace/*/raw_terminal.log` - Worker output
2. `workspace/*/orchestrator_terminal.log` - Orchestrator output

---

## Dependencies

### External Libraries
- **pexpect/wexpect**: Already used for process control
- **watchdog**: Already used for file monitoring
- No new dependencies needed ✅

### Internal Dependencies
- `worker_manager.py`: Core implementation
- `terminal_ws.py`: Already ready for streaming
- Frontend components: Already implemented ✅

---

## Rollback Plan

If implementation encounters critical issues:

1. **Immediate Rollback**: Keep using sample data
2. **Debug in Isolation**: Test capture in separate script
3. **Incremental Integration**: Add capture one component at a time
4. **User Communication**: Inform user of delay and continue with Phase 2

---

## Post-Implementation

### Documentation Updates
- [ ] Update ROADMAP.md - Mark Phase 1.3 as completed
- [ ] Create PHASE1_3_COMPLETION_REPORT.md
- [ ] Update user-facing documentation
- [ ] Add troubleshooting guide for capture issues

### Next Phase Preview
After Phase 1.3 completion, consider:
- **Phase 2.1**: Terminal output search/filtering
- **Phase 2.2**: Performance metrics visualization
- **Phase 2.3**: Export and replay functionality

---

## Open Questions

1. **ANSI Code Handling**: Strip or convert to HTML?
   - Recommendation: Start with stripping, add HTML conversion later

2. **Log Rotation**: When to rotate large log files?
   - Recommendation: Implement in Phase 2, not critical for initial version

3. **Historical Replay**: Should old logs be preserved?
   - Recommendation: Keep for session lifetime, clean on new task

4. **Orchestrator Multi-Worker**: How to log when managing multiple workers?
   - Recommendation: One orchestrator log per workspace, clearly mark which worker

---

## Conclusion

Phase 1.3 builds upon the solid foundation of Phase 1.2's UI infrastructure by connecting it to actual AI process output. With worker capture already partially implemented, the main work is:

1. Validating existing capture works
2. Adding orchestrator output logging
3. Testing with real AI tasks
4. Optimizing for real-time streaming

This is a **high-value, medium-complexity** phase that directly addresses user concerns about AI instance verification.

**Status**: READY TO BEGIN ⏳

**Next Step**: Phase 1.3.1 - Verify existing worker capture implementation

---

**Plan Created**: 2025-10-24
**Author**: Claude (Sonnet 4.5)
**Project**: AI Parallel Coding Tool
