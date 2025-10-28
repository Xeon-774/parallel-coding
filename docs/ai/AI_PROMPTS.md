# AI Prompts Guide - Claude Orchestrator

**Version:** v10.1.0
**Purpose:** Effective prompts for AI assistants working with this codebase
**Last Updated:** 2025-10-21

---

## 📋 Table of Contents

1. [General Principles](#general-principles)
2. [Initial Context Prompts](#initial-context-prompts)
3. [Development Task Prompts](#development-task-prompts)
4. [Debugging & Troubleshooting Prompts](#debugging--troubleshooting-prompts)
5. [Testing Prompts](#testing-prompts)
6. [Documentation Prompts](#documentation-prompts)
7. [Code Review Prompts](#code-review-prompts)
8. [Refactoring Prompts](#refactoring-prompts)

---

## 🎯 General Principles

### How to Provide Effective Context

**DO:**
- ✅ Mention version (v10.1.0)
- ✅ Reference specific files/modules
- ✅ Include error messages verbatim
- ✅ Specify desired outcome
- ✅ Mention constraints (time, scope, dependencies)

**DON'T:**
- ❌ Assume AI knows recent changes
- ❌ Use vague descriptions ("the config thing")
- ❌ Skip error details
- ❌ Request multiple unrelated changes at once

---

## 🌟 Initial Context Prompts

### Prompt 1: First-Time Project Overview

```
I'm working with the Claude Orchestrator project (v10.1.0).
This is a Python framework for parallel AI task execution using
multiple Claude CLI instances.

Key context:
- Current version: v10.1.0 (Clean Architecture, DDD principles)
- Architecture: 4-layer (Presentation, Application, Domain, Infrastructure)
- Quality: A++ (100% functional test pass rate)
- Major change in v10: RefactoredOrchestrator removed, use service layer

Please help me understand [specific aspect].

References:
- AI_DEVELOPMENT_GUIDE.md
- ARCHITECTURE.md
- CODEBASE_MAP.md
```

**When to use:** First interaction with new AI assistant

---

### Prompt 2: Resuming After Break

```
Resuming work on Claude Orchestrator v10.1.0.

Previous session context:
- Was working on: [describe previous task]
- Files modified: [list files]
- Current status: [describe state]

Next steps:
- [ ] [task 1]
- [ ] [task 2]

Please help me continue from where I left off.
```

**When to use:** Resuming work after interruption

---

### Prompt 3: Understanding Specific Feature

```
I need to understand how [feature] works in Claude Orchestrator v10.1.0.

Specific questions:
1. What file(s) implement this feature?
2. What are the key classes/functions?
3. What are the dependencies?
4. Are there existing tests I can reference?

Please provide:
- File locations
- Code snippets
- Architecture diagram (if complex)
- Related documentation
```

**When to use:** Learning about specific features

---

## 🛠️ Development Task Prompts

### Prompt 4: Adding New API Endpoint

```
Task: Add a new REST API endpoint to Claude Orchestrator v10.1.0

Requirements:
- Endpoint: POST /api/v1/[endpoint-name]
- Purpose: [describe functionality]
- Input: [describe request model]
- Output: [describe response model]
- Authentication: Required (API key)

Follow patterns from:
- orchestrator/api/app.py (existing endpoints)
- orchestrator/api/models.py (Pydantic models)
- tests/test_api_integration.py (test patterns)

Steps needed:
1. Create request/response models in models.py
2. Add endpoint handler in app.py
3. Add tests in test_api_integration.py
4. Verify with: pytest tests/test_api_integration.py::[test_name] -v

Maintain:
- Type safety (mypy)
- Error handling (custom exceptions)
- World-class quality standards
```

**When to use:** Adding new API endpoints

---

### Prompt 5: Adding Exception Type

```
Task: Add new exception type to Claude Orchestrator v10.1.0

Exception details:
- Name: [ExceptionName]Error
- Parent: [OrchestratorException|WorkerError|TaskError|etc.]
- Purpose: [when to raise this exception]
- Context fields: [list specific context fields]

Follow pattern from orchestrator/core/exceptions.py:
- Inherit from appropriate base exception
- Include context in __init__
- Add docstring describing when to use
- Update exception hierarchy in file comments

Add tests in tests/test_exceptions.py:
- Test instantiation
- Test context fields
- Test string representation
- Test exception chaining (if applicable)

Verify:
- pytest tests/test_exceptions.py -v
- mypy orchestrator/core/exceptions.py
```

**When to use:** Adding new exception types

---

### Prompt 6: Adding Observability Metrics

```
Task: Add new metrics to Claude Orchestrator v10.1.0 observability system

Metric details:
- Metric name: [metric_name]
- Type: [counter|gauge|histogram]
- Purpose: [what it measures]
- Labels: [list label dimensions]
- Where to collect: [which component/operation]

Implementation:
1. Add metric collection in [component file]
2. Use MetricsCollector.record() or PerformanceMonitor.track_operation()
3. Add test in tests/test_integration_v9.py::TestObservability

Example from observability.py:
```python
collector.record("metric_name", value, labels={"label1": "val1"})
monitor.track_operation("operation", duration, success, labels)
```

Verify:
- Test passes
- Metric appears in get_summary()
- Dashboard displays metric
```

**When to use:** Adding metrics/monitoring

---

### Prompt 7: Modifying Configuration

```
Task: Add new configuration option to Claude Orchestrator v10.1.0

Configuration details:
- Parameter name: [param_name]
- Type: [int|str|bool|etc.]
- Default value: [default]
- Validation: [constraints, e.g., ge=1, le=100]
- Purpose: [what it controls]

Files to modify:
1. orchestrator/config.py (OrchestratorConfig dataclass)
2. orchestrator/core/validated_config.py (ValidatedConfig with validation)
3. tests/test_integration_v9.py::TestValidatedConfiguration

Steps:
1. Add field to OrchestratorConfig with type hint and default
2. Add to ValidatedConfig with Pydantic Field constraints
3. Add custom validator if needed (@validator)
4. Update from_env() to read from environment variable
5. Add test cases for valid/invalid values

Verify:
- Type checking: mypy orchestrator/config.py
- Tests: pytest tests/test_integration_v9.py::TestValidatedConfiguration -v
- Documentation: Update relevant docs
```

**When to use:** Adding configuration options

---

## 🐛 Debugging & Troubleshooting Prompts

### Prompt 8: Investigating Test Failure

```
Test failure in Claude Orchestrator v10.1.0

Failing test:
- File: tests/[test_file].py
- Test: [test_name]
- Error: [paste full error message and traceback]

Context:
- Recent changes: [describe recent modifications]
- Expected behavior: [what should happen]
- Actual behavior: [what's happening]

Please help:
1. Identify root cause
2. Suggest fix
3. Recommend additional tests to prevent regression

Run with:
pytest tests/[test_file].py::[test_name] -v --tb=short
```

**When to use:** Test failures

---

### Prompt 9: Debugging Type Errors

```
mypy type checking error in Claude Orchestrator v10.1.0

Error message:
[paste full mypy error]

File: [file_path]:[line_number]
Context: [paste relevant code section]

I've reviewed:
- mypy.ini configuration
- Type hints in file
- Related imports

Please help:
1. Explain the type error
2. Suggest correct type annotation
3. Show example from similar code in project

Verify fix with:
mypy [file_path] --config-file mypy.ini
```

**When to use:** Type checking errors

---

### Prompt 10: Performance Issue

```
Performance issue in Claude Orchestrator v10.1.0

Problem:
- Operation: [describe operation]
- Current performance: [metrics]
- Expected performance: [target metrics]
- Impact: [describe impact]

Profiling data (if available):
[paste profiling output]

Context:
- This started after: [recent change or version]
- Affects: [which components]

Please help:
1. Identify bottleneck
2. Suggest optimization
3. Recommend profiling approach if needed

Maintain:
- Code quality
- Test coverage
- API compatibility
```

**When to use:** Performance issues

---

## 🧪 Testing Prompts

### Prompt 11: Writing New Tests

```
Task: Write tests for new feature in Claude Orchestrator v10.1.0

Feature to test:
- Component: [file/class/function]
- Functionality: [describe what it does]
- Edge cases: [list edge cases to cover]

Test requirements:
- File: tests/[appropriate_test_file].py
- Follow patterns from: [reference existing similar tests]
- Coverage: Unit tests + integration tests (if applicable)

Test cases needed:
1. Happy path: [normal operation]
2. Edge cases: [list edge cases]
3. Error cases: [expected failures]
4. Integration: [component interactions]

Verify:
- All tests pass: pytest tests/[test_file].py -v
- Coverage: pytest tests/[test_file].py --cov=[module]
- Quality: No degradation in overall test suite
```

**When to use:** Writing new tests

---

### Prompt 12: Fixing Flaky Tests

```
Flaky test issue in Claude Orchestrator v10.1.0

Flaky test:
- Test: tests/[file].py::[test_name]
- Failure rate: [X% or "intermittent"]
- Error when fails: [paste error]

Observations:
- Passes when: [conditions]
- Fails when: [conditions]
- Possible causes: [hypotheses]

Context:
- Related to: [async operations|file I/O|timing|network|etc.]
- Windows/Unix specific?: [yes/no]

Please help:
1. Identify root cause of flakiness
2. Suggest stable alternative
3. Recommend improvements to test

Note: We maintain 100% functional test pass rate
```

**When to use:** Flaky test issues

---

## 📚 Documentation Prompts

### Prompt 13: Documenting New Feature

```
Task: Document new feature in Claude Orchestrator v10.1.0

Feature:
- Name: [feature name]
- Location: [files/modules]
- Purpose: [what it does]
- API: [public interface]

Documentation needed:
1. Docstrings (if missing)
2. User guide section (docs/user_guide.md)
3. API reference (docs/api_reference.md)
4. Example usage (examples/)
5. Update CHANGELOG.md

Follow style from:
- Existing docstrings in codebase
- Google Python docstring style
- Existing documentation format

Include:
- Clear descriptions
- Usage examples
- Parameter/return type documentation
- Edge cases and limitations
```

**When to use:** Documenting features

---

### Prompt 14: Updating Architecture Docs

```
Task: Update architecture documentation for Claude Orchestrator v10.1.0

Changes made:
- [describe architectural changes]
- New components: [list]
- Modified interactions: [describe]

Files to update:
1. ARCHITECTURE.md (system architecture)
2. CODEBASE_MAP.md (if file structure changed)
3. AI_DEVELOPMENT_GUIDE.md (if development process changed)

Please:
1. Review changes for accuracy
2. Update diagrams (ASCII art)
3. Update dependency graphs
4. Ensure consistency across docs

Maintain:
- Clear, concise language
- Accurate diagrams
- Complete cross-references
```

**When to use:** Architecture changes

---

## 🔍 Code Review Prompts

### Prompt 15: Pre-Commit Review

```
Code review request for Claude Orchestrator v10.1.0

Changes:
- Files modified: [list files]
- Purpose: [describe change]
- Lines changed: [+X -Y]

Please review for:
1. **Code Quality**
   - Follows existing patterns?
   - Proper error handling?
   - Type hints complete?

2. **Architecture**
   - Correct layer placement?
   - Dependencies appropriate?
   - SOLID principles followed?

3. **Testing**
   - Tests added/updated?
   - Edge cases covered?
   - All tests passing?

4. **Documentation**
   - Docstrings complete?
   - Comments where needed?
   - Docs updated?

5. **Quality Standards**
   - mypy passes?
   - World-class quality maintained?
   - No regressions?

Verify:
- pytest tests/ -v --tb=short --no-cov
- mypy orchestrator/ --config-file mypy.ini
```

**When to use:** Before committing changes

---

### Prompt 16: Security Review

```
Security review for Claude Orchestrator v10.1.0

Changes involving:
- Authentication/Authorization: [yes/no]
- Input validation: [yes/no]
- File operations: [yes/no]
- External commands: [yes/no]

Files: [list files]

Please review for:
1. **Input Validation**
   - All inputs validated?
   - Pydantic models used?
   - SQL injection prevented?
   - Path traversal prevented?

2. **Authentication**
   - API keys validated?
   - Rate limiting in place?
   - Proper error messages?

3. **Safety Controls**
   - Dangerous operations flagged?
   - AISafetyJudge consulted?
   - User approval required?

4. **Data Protection**
   - Secrets not logged?
   - Sensitive data encrypted?
   - Proper file permissions?

Reference:
- orchestrator/api/auth.py
- orchestrator/core/ai_safety_judge.py
- WEB_UI_REFACTORING_REPORT.md (security section)
```

**When to use:** Security-sensitive changes

---

## ♻️ Refactoring Prompts

### Prompt 17: Refactoring for Clarity

```
Refactoring task for Claude Orchestrator v10.1.0

Target:
- File: [file_path]
- Function/Class: [name]
- Lines: [start-end]

Issues:
- Complexity: [too long|too complex|unclear logic]
- Specific problems: [describe]

Goals:
1. Improve readability
2. Maintain functionality
3. Preserve tests
4. Keep API compatibility

Constraints:
- Don't break existing API
- Maintain type safety
- Keep tests passing
- Follow existing patterns

Steps:
1. Extract methods/functions
2. Rename for clarity
3. Add comments if complex
4. Update tests if needed

Verify:
- All tests pass: pytest tests/ -v
- Types correct: mypy [file]
- No behavioral changes
```

**When to use:** Code clarity improvements

---

### Prompt 18: Performance Refactoring

```
Performance refactoring for Claude Orchestrator v10.1.0

Target:
- Component: [describe]
- Current performance: [metrics]
- Target performance: [goals]

Profiling shows:
[paste profiling data]

Optimization ideas:
- [list potential optimizations]

Constraints:
- Maintain correctness
- Keep API compatible
- Preserve readability
- Don't premature optimize

Approach:
1. Profile to identify bottleneck
2. Implement optimization
3. Benchmark before/after
4. Verify correctness with tests

Verify:
- Tests still pass
- Performance improved
- No regressions
- Code still readable
```

**When to use:** Performance optimization

---

## 🎓 Learning Prompts

### Prompt 19: Understanding Design Decision

```
Question about Claude Orchestrator v10.1.0 design

Design element:
[describe the pattern/decision you want to understand]

Questions:
1. Why was this approach chosen?
2. What alternatives were considered?
3. What are the trade-offs?
4. When should I follow this pattern?

Context:
- Where I see this: [file/module]
- What I'm trying to do: [describe]

Please explain:
- The reasoning behind this design
- Related patterns in codebase
- Best practices for similar situations
```

**When to use:** Understanding design decisions

---

### Prompt 20: Best Practices Check

```
Best practices check for Claude Orchestrator v10.1.0

Code I wrote:
```python
[paste code]
```

Questions:
1. Does this follow project conventions?
2. Are there better patterns in the codebase?
3. Am I using the right abstractions?
4. Is error handling appropriate?
5. Are type hints complete?

Please review against:
- Existing similar code
- SOLID principles
- Project coding standards
- Clean Architecture layers

Suggest improvements to match world-class quality standards.
```

**When to use:** Checking code quality

---

## 🎯 Template Prompt Structure

### Effective Prompt Template

```
[TASK DESCRIPTION]
Task: [Clear, specific task description]

[CONTEXT]
Project: Claude Orchestrator v10.1.0
Component: [specific component/module]
Current state: [describe current state]

[REQUIREMENTS]
- Requirement 1
- Requirement 2
- Requirement 3

[CONSTRAINTS]
- Constraint 1 (e.g., maintain API compatibility)
- Constraint 2 (e.g., keep tests passing)

[REFERENCES]
- Similar code: [file:line]
- Documentation: [doc file]
- Related tests: [test file]

[EXPECTED OUTCOME]
[Describe what success looks like]

[VERIFICATION]
- Step 1: [how to verify]
- Step 2: [how to verify]
```

---

## ✅ Prompt Quality Checklist

Before sending a prompt, check:

- [ ] **Specific**: Clearly defined task or question
- [ ] **Context**: Version, files, recent changes mentioned
- [ ] **Complete**: All relevant information included
- [ ] **Actionable**: Clear what needs to be done
- [ ] **Verifiable**: How to confirm success
- [ ] **Constrained**: Boundaries and limits specified
- [ ] **Referenced**: Points to relevant docs/code

---

## 🎉 Examples of Great Prompts vs Poor Prompts

### ❌ Poor Prompt
```
The tests are failing. Can you fix them?
```
**Problems:** No context, which tests, what errors, no recent changes

### ✅ Great Prompt
```
Test failure in Claude Orchestrator v10.1.0

Failing test: tests/test_api_integration.py::TestAuthentication::test_invalid_api_key
Error: TypeError: Object of type datetime is not JSON serializable

Recent changes: Added timestamp field to ErrorResponse model

Full traceback:
[paste traceback]

Please help identify the issue and suggest a fix. I suspect it's
related to Pydantic serialization, as we have similar patterns in
other response models.

Verify with:
pytest tests/test_api_integration.py::TestAuthentication -v
```
**Why better:** Specific test, error message, context, hypothesis, verification

---

### ❌ Poor Prompt
```
Add logging somewhere
```
**Problems:** Where, what to log, what format, what level

### ✅ Great Prompt
```
Task: Add structured logging to task execution in Claude Orchestrator v10.1.0

Component: orchestrator/core/task_analyzer_service.py
Function: TaskAnalyzerService.analyze_and_split()

Log points needed:
1. Start of analysis (INFO level)
2. Task split decision (INFO level)
3. Subtasks created (INFO level with count)
4. Errors during analysis (ERROR level)

Use StructuredLogger from orchestrator/core/structured_logging.py
Follow patterns from orchestrator/api/app.py:orchestrate_task()

Include context:
- request_length
- is_splittable
- subtask_count
- analysis_duration_ms

Verify:
- Logs appear in JSON format
- All context fields present
- Performance tracking works
```
**Why better:** Specific location, what to log, format, examples, verification

---

## 📚 References

- **AI_DEVELOPMENT_GUIDE.md** - Development workflow
- **ARCHITECTURE.md** - System design
- **CODEBASE_MAP.md** - Code navigation
- **README.md** - Project overview

---

**Last Updated:** 2025-10-21
**Version:** v10.1.0
**Usage:** Copy and customize these prompts for your specific needs
