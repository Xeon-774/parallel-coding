# Codex Batch Task: Refactor 5 Remaining C901 Functions

## Objective
Reduce complexity of 5 remaining functions using Extract Method pattern.

## Target Functions

### 1. metrics_api.py:58 - get_current_hybrid_metrics (C901: 12)
**File**: `orchestrator/api/metrics_api.py:58`
**Strategy**: Extract metric collection blocks into separate functions
- Extract worker metrics collection
- Extract supervisor metrics collection
- Extract system metrics collection

### 2. hybrid_engine.py:312 - HybridDecisionEngine.decide (C901: 12)
**File**: `orchestrator/core/hybrid_engine.py:312`
**Strategy**: Extract decision logic blocks
- Extract task complexity evaluation
- Extract worker selection logic
- Extract load balancing logic

### 3. resilience.py:425 - Anonymous function (C901: 12)
**File**: `orchestrator/core/resilience.py:425`
**Strategy**: Extract into named function with helpers
- Create named function
- Extract retry logic
- Extract timeout handling

### 4. recursion_websocket.py:101 - ws_recursion (C901: 11)
**File**: `orchestrator/api/recursion_websocket.py:101`
**Strategy**: Extract WebSocket message handling
- Extract auth validation
- Extract message processing
- Extract error handling

### 5. quality_gate.py:310 - QualityGateEngine.run_lint (C901: 11)
**File**: `orchestrator/quality/quality_gate.py:310`
**Strategy**: Extract lint tool execution
- Extract black formatting
- Extract isort sorting
- Extract flake8 checking

## Requirements (All Functions)
1. Apply Extract Method pattern
2. Reduce complexity from 11-12 to <10
3. Maintain 100% original behavior
4. Single Responsibility Principle
5. Clear docstrings for all helpers
6. No shortcuts (no `# noqa`)

## Excellence AI Standard
- ✅ Proper refactoring approach
- ✅ Zero behavior changes
- ✅ Improved maintainability

## Verification
```bash
# Syntax check
python -m py_compile orchestrator/api/metrics_api.py
python -m py_compile orchestrator/core/hybrid_engine.py
python -m py_compile orchestrator/core/resilience.py
python -m py_compile orchestrator/api/recursion_websocket.py
python -m py_compile orchestrator/quality/quality_gate.py

# C901 check
flake8 orchestrator --select=C901 --count

# Expected: 0 C901 issues
```

## Expected Outcome
- All 6 C901 issues resolved (total: 16→0, -100%)
- 15-25 helper methods extracted across all functions
- All tests passing
- Excellence AI Standard 100% compliance
