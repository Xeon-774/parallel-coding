# Validation Module - Proof-of-Change Pipeline

**Phase 1 - Task 6: Proof-of-change artifact generation with deterministic validators**

## Overview

The Validation module provides proof-of-change (PoC) artifact generation for all code changes, with deterministic validators running at T=0 (immediate validation). This ensures code quality and correctness before changes are committed.

## Features

- **Proof-of-Change Artifacts**: Immutable records of all code changes
- **Deterministic Validators**: Run at T=0 for immediate feedback
- **Mutation Testing**: Verify test quality and effectiveness
- **Validation Pipeline**: Coordinate multiple validators
- **Audit Trail**: SHA256-hashed artifacts for integrity verification

## Architecture

```
orchestrator/validation/
├── __init__.py              # Package exports
├── proof_of_change.py       # PoC artifact generation (268 lines)
├── validator.py             # Deterministic validators (369 lines)
├── mutation_test.py         # Mutation testing engine (317 lines)
└── README.md                # This file
```

## Components

### 1. Proof-of-Change (PoC)

Generate immutable artifacts for all code changes:

```python
from orchestrator.validation import ProofOfChangeGenerator

# Initialize generator
generator = ProofOfChangeGenerator(
    repo_path=".",
    output_dir="poc_artifacts"
)

# Generate PoC artifact
poc = generator.generate(
    rationale="Fix authentication bug in login endpoint",
    tests_added=["tests/test_auth.py"],
    metadata={"issue": "AUTH-123"}
)

print(f"Change ID: {poc.change_id}")
print(f"Files changed: {len(poc.files_changed)}")
print(f"Tests passed: {poc.tests_passed}")
print(f"Validation hash: {poc.validation_hash}")
```

**PoC Artifact Contents:**
- `change_id`: Unique identifier (SHA256 truncated)
- `timestamp`: ISO 8601 timestamp
- `files_changed`: List of modified files
- `diff`: Git diff output
- `rationale`: Human explanation of the change
- `tests_added`: Test files created/modified
- `tests_passed`: Boolean test result
- `validation_hash`: SHA256 hash for integrity
- `metadata`: Additional context

### 2. Deterministic Validators

Run validators at T=0 for immediate feedback:

```python
from orchestrator.validation import (
    ValidationPipeline,
    LintValidator,
    TypeCheckValidator,
    TestValidator,
    SecurityValidator
)

# Create validation pipeline
pipeline = ValidationPipeline(project_dir=".")

# Add validators
pipeline.add_validator(LintValidator(".", max_issues=0))
pipeline.add_validator(TypeCheckValidator(".", strict=True))
pipeline.add_validator(TestValidator(".", min_coverage=90.0))
pipeline.add_validator(SecurityValidator(".", max_issues=0))

# Run all validators
results = pipeline.run()

# Check if all passed
if pipeline.all_passed(results):
    print("✅ All validations passed!")
else:
    print("❌ Some validations failed:")
    for result in results:
        if not result:
            print(f"  - {result.validator_name}: {result.message}")
```

**Available Validators:**

1. **LintValidator**: Code style and quality (flake8)
   - Configurable max issues threshold
   - Pattern ignoring support

2. **TypeCheckValidator**: Type checking (mypy)
   - Strict mode support
   - Error counting and reporting

3. **TestValidator**: Test execution and coverage (pytest)
   - Minimum coverage threshold
   - Test failure detection

4. **SecurityValidator**: Security scanning (bandit)
   - Vulnerability detection
   - Issue counting

### 3. Mutation Testing

Verify test quality by introducing mutations:

```python
from orchestrator.validation.mutation_test import MutationTester

# Initialize tester
tester = MutationTester(
    project_dir=".",
    mutation_types=None  # All types
)

# Run mutation testing
result = tester.run(max_mutations=10)

print(f"Mutation Score: {result.score:.1f}%")
print(f"Killed: {result.killed_mutations}/{result.total_mutations}")
print(f"Survived: {result.survived_mutations}")

# Show survivors
if result.survivors:
    print("\nMutations that survived:")
    for mutation in result.survivors:
        print(f"  {mutation.file_path}:{mutation.line_number}")
        print(f"    {mutation.description}")
```

**Mutation Types:**
- `ARITHMETIC`: +/-, */%
- `COMPARISON`: </>/<=/>=, ==/!=
- `LOGICAL`: and/or
- `RETURN`: return True/False
- `CONSTANT`: 0/1, True/False

**Mutation Score:**
- `100%`: All mutations caught by tests (excellent)
- `80-99%`: Most mutations caught (good)
- `60-79%`: Some mutations missed (needs improvement)
- `<60%`: Many mutations missed (poor test quality)

## Usage Examples

### Example 1: Complete PoC Workflow

```python
from orchestrator.validation import ProofOfChangeGenerator

# 1. Make code changes
# 2. Generate PoC artifact
generator = ProofOfChangeGenerator(".", "poc_artifacts")
poc = generator.generate(
    rationale="Add user authentication feature",
    tests_added=["tests/test_auth.py"],
    metadata={
        "issue": "FEAT-456",
        "author": "developer@example.com"
    }
)

# 3. Verify artifact integrity
if generator.verify_artifact(poc):
    print("✅ Artifact verified")
else:
    print("❌ Artifact tampered")

# 4. Save to file (automatic)
print(f"Saved to: poc_artifacts/poc_{poc.change_id}.json")

# 5. Load later
loaded_poc = generator.load_artifact(poc.change_id)
print(f"Loaded change from {loaded_poc.timestamp}")
```

### Example 2: Pre-Commit Validation

```python
from orchestrator.validation import ValidationPipeline, LintValidator

# Create pre-commit validation
pipeline = ValidationPipeline(".")
pipeline.add_validator(LintValidator(".", max_issues=0))

# Run validation
results = pipeline.run()

# Block commit if validation fails
if not pipeline.all_passed(results):
    print("❌ Validation failed - commit blocked")
    exit(1)

print("✅ Validation passed - commit allowed")
```

### Example 3: CI/CD Integration

```python
from orchestrator.validation import (
    ProofOfChangeGenerator,
    ValidationPipeline,
    LintValidator,
    TestValidator
)

# 1. Generate PoC
generator = ProofOfChangeGenerator(".", "poc_artifacts")
poc = generator.generate(rationale="CI/CD build")

# 2. Run validators
pipeline = ValidationPipeline(".")
pipeline.add_validator(LintValidator(".", max_issues=50))
pipeline.add_validator(TestValidator(".", min_coverage=80.0))

results = pipeline.run()

# 3. Fail build if validation fails
if not pipeline.all_passed(results):
    print("❌ Build failed")
    exit(1)

print("✅ Build passed")
```

### Example 4: Mutation Testing in CI

```python
from orchestrator.validation.mutation_test import MutationTester

# Run mutation testing
tester = MutationTester(".")
result = tester.run(max_mutations=20)

# Require 80% mutation score
if result.score < 80.0:
    print(f"❌ Mutation score too low: {result.score:.1f}%")
    exit(1)

print(f"✅ Mutation score: {result.score:.1f}%")
```

## Artifact Storage

PoC artifacts are stored as JSON files:

```json
{
  "change_id": "a1b2c3d4e5f6g7h8",
  "timestamp": "2025-10-29T12:34:56Z",
  "files_changed": [
    "orchestrator/auth.py",
    "tests/test_auth.py"
  ],
  "diff": "--- a/orchestrator/auth.py\n+++ b/orchestrator/auth.py\n...",
  "rationale": "Add user authentication feature",
  "tests_added": ["tests/test_auth.py"],
  "tests_passed": true,
  "validation_hash": "sha256:abc123...",
  "metadata": {
    "issue": "FEAT-456",
    "author": "developer@example.com"
  }
}
```

## Validation Results

Validation results use a standardized format:

```python
@dataclass
class ValidationResult:
    status: ValidationStatus  # PASSED/FAILED/SKIPPED
    validator_name: str
    message: str
    details: dict[str, Any] | None = None
    errors: list[str] | None = None
```

Example results:

```python
# Passed
ValidationResult(
    status=ValidationStatus.PASSED,
    validator_name="LintValidator",
    message="Lint check passed (5 issues, max 10)",
    details={"issue_count": 5, "max_issues": 10}
)

# Failed
ValidationResult(
    status=ValidationStatus.FAILED,
    validator_name="TestValidator",
    message="Coverage too low (75.0%, min 90.0%)",
    details={"coverage": 75.0, "min_coverage": 90.0}
)
```

## Testing

Run validation module tests:

```bash
pytest tests/test_validation.py -v
```

**Test Coverage**: 21 tests, 100% passing

## Integration with Git Workflow

### Pre-Commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python -c "
from orchestrator.validation import ValidationPipeline, LintValidator
pipeline = ValidationPipeline('.')
pipeline.add_validator(LintValidator('.', max_issues=0))
results = pipeline.run()
exit(0 if pipeline.all_passed(results) else 1)
"
```

### GitHub Actions

Create `.github/workflows/validation.yml`:

```yaml
name: Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run validation pipeline
        run: |
          python -c "
          from orchestrator.validation import ValidationPipeline
          from orchestrator.validation import LintValidator, TestValidator
          pipeline = ValidationPipeline('.')
          pipeline.add_validator(LintValidator('.', max_issues=50))
          pipeline.add_validator(TestValidator('.', min_coverage=80.0))
          results = pipeline.run()
          exit(0 if pipeline.all_passed(results) else 1)
          "
```

## Best Practices

1. **Generate PoC for Every Change**
   - Always include rationale
   - Link to issue/ticket
   - Add relevant metadata

2. **Run Validators at T=0**
   - Immediate feedback
   - Fast iteration
   - Catch issues early

3. **Use Validation Pipeline**
   - Coordinate multiple validators
   - Consistent checking
   - Fail fast on errors

4. **Verify Artifact Integrity**
   - Check validation hash
   - Detect tampering
   - Ensure immutability

5. **Monitor Mutation Score**
   - Target 80%+ score
   - Improve weak tests
   - Increase coverage

## Performance

- **PoC Generation**: <1s for typical changes
- **Lint Validation**: 1-3s
- **Type Check**: 10-20s (strict mode)
- **Test Validation**: 30-60s (depends on test suite)
- **Mutation Testing**: 1-5 min (10 mutations)

## Troubleshooting

### PoC Generation Fails

```python
# Check git repository
git status

# Ensure changes are staged
git add .

# Generate PoC
poc = generator.generate(rationale="...")
```

### Validation Timeout

```python
# Increase timeout in validator
validator = TestValidator(".", min_coverage=90.0)
# Modify subprocess.run timeout parameter
```

### Mutation Testing Slow

```python
# Limit mutations
tester = MutationTester(".")
result = tester.run(max_mutations=5)  # Reduce from default

# Target specific files
tester = MutationTester(".", target_files=["auth.py"])
```

## References

- [Mutation Testing Concepts](https://en.wikipedia.org/wiki/Mutation_testing)
- [Deterministic Testing](https://martinfowler.com/articles/nonDeterminism.html)
- [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

---

**Phase 1 - Task 6 Complete** ✅

- Proof-of-Change: 268 lines
- Validators: 369 lines
- Mutation Testing: 317 lines
- Tests: 21 (100% passing)
- Documentation: Complete
