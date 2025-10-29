# Codex Task: Refactor DialogueFileMonitor._read_new_entries (C901: 12)

## Objective
Reduce complexity of `_read_new_entries` method from 12 to <10 using Extract Method pattern.

## Target File
`orchestrator/api/dialogue_ws.py:127`

## Requirements
1. Apply Extract Method pattern to reduce cyclomatic complexity
2. Extract logical blocks into focused helper methods
3. Maintain 100% original behavior (zero behavior changes)
4. Follow Single Responsibility Principle
5. All helper methods must have clear docstrings
6. No shortcuts (no `# noqa`)

## Excellence AI Standard Compliance
- ✅ Proper refactoring (no noqa)
- ✅ Single Responsibility Principle
- ✅ Clear method names and documentation
- ✅ Zero behavior changes

## Expected Outcome
- C901 complexity: 12 → <10
- 3-5 helper methods extracted
- All tests passing
- Code more maintainable and readable

## Verification
After refactoring, run:
```bash
python -m py_compile orchestrator/api/dialogue_ws.py
flake8 orchestrator/api/dialogue_ws.py --select=C901
```
