# Policy Engine (OPA/Rego)

**Phase 1 - Task 5: Policy-based decision making with Open Policy Agent**

## Overview

The Policy Engine provides deny-by-default policy enforcement using Open Policy Agent (OPA) and Rego policy language. It enables fine-grained access control for autonomous execution workflows.

## Features

- **Deny-by-Default**: All actions denied unless explicitly allowed by policy
- **OPA Integration**: Native integration with OPA server
- **Rego Policies**: Declarative policy files for different resources
- **Audit Logging**: Immutable audit trail of all policy decisions
- **Risk-Based Control**: Policies vary by risk level (LOW/MEDIUM/HIGH)
- **Context-Aware**: Policy decisions based on execution context

## Architecture

```
orchestrator/policy/
├── __init__.py           # Package exports
├── opa_engine.py         # OPA integration engine (280 lines)
├── policy_schemas.py     # Policy data models (57 lines)
└── README.md             # This file

policies/
├── sandbox/
│   └── execute.rego      # Sandbox execution policies
├── filesystem/
│   └── write.rego        # File system write policies
└── network/
    └── access.rego       # Network access policies
```

## Quick Start

### 1. Start OPA Server

```bash
# Download OPA (Linux/macOS)
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x opa

# Download OPA (Windows)
curl -L -o opa.exe https://openpolicyagent.org/downloads/latest/opa_windows_amd64.exe

# Start OPA server
./opa run --server --addr localhost:8181
```

### 2. Initialize Policy Engine

```python
from orchestrator.policy import OPAEngine, PolicyRequest

# Create engine
engine = OPAEngine(
    opa_url="http://localhost:8181",
    policy_dir="policies",
    deny_by_default=True,
    audit_log_path="policy_audit.log"
)

# Load policies
engine.load_policies()
```

### 3. Evaluate Policies

```python
# Create policy request
request = PolicyRequest(
    action="execute",
    resource="sandbox",
    context={
        "risk_level": "LOW",
        "network_access": False,
        "filesystem_readonly": True
    }
)

# Evaluate
result = engine.evaluate_policy(request)

if result.allowed:
    print("✅ Action ALLOWED")
    print(f"Reasons: {result.reasons}")
else:
    print("❌ Action DENIED")
    print(f"Violations: {result.violations}")
    print(f"Reasons: {result.reasons}")
```

## Policy Files

### Sandbox Execution (`policies/sandbox/execute.rego`)

Controls sandbox execution based on risk level:

- **LOW risk**: Allowed without restrictions
- **MEDIUM risk**: Requires network_access=false and filesystem_readonly=true
- **HIGH risk**: Requires approval + MEDIUM restrictions

### Filesystem Write (`policies/filesystem/write.rego`)

Controls file system writes:

- ✅ **Allowed**: `/workspace/`, `/tmp/`
- ❌ **Denied**: `/etc/`, `/bin/`, `/usr/`, `/sys/`, `/proc/`
- ❌ **Denied**: Sensitive patterns (`.ssh/`, `.aws/`, `.env`, `credentials`, `secrets`)

### Network Access (`policies/network/access.rego`)

Controls network access:

- ✅ **Allowed**: Approved domains (github.com, pypi.org, etc.)
- ✅ **Allowed**: localhost (development only)
- ❌ **Denied**: Internal networks in production (192.168.*, 10.*, 172.16.*)
- ❌ **Denied**: Cloud metadata services (169.254.169.254, metadata.google.internal)

## Usage Examples

### Example 1: LOW Risk Sandbox Execution

```python
request = PolicyRequest(
    action="execute",
    resource="sandbox",
    context={"risk_level": "LOW"}
)

result = engine.evaluate_policy(request)
# ✅ ALLOWED
```

### Example 2: HIGH Risk Sandbox Execution (Denied)

```python
request = PolicyRequest(
    action="execute",
    resource="sandbox",
    context={
        "risk_level": "HIGH",
        "approved_by": None  # No approval
    }
)

result = engine.evaluate_policy(request)
# ❌ DENIED - "HIGH risk execution requires approval"
```

### Example 3: File System Write (Allowed)

```python
request = PolicyRequest(
    action="file_write",
    resource="filesystem",
    context={"path": "/workspace/output.txt"}
)

result = engine.evaluate_policy(request)
# ✅ ALLOWED
```

### Example 4: File System Write (Denied)

```python
request = PolicyRequest(
    action="file_write",
    resource="filesystem",
    context={"path": "/etc/passwd"}
)

result = engine.evaluate_policy(request)
# ❌ DENIED - "Cannot write to system directory: /etc/"
```

### Example 5: Network Access (Allowed)

```python
request = PolicyRequest(
    action="network_access",
    resource="network",
    context={
        "url": "https://api.github.com/repos",
        "environment": "production"
    }
)

result = engine.evaluate_policy(request)
# ✅ ALLOWED
```

### Example 6: Network Access (Denied)

```python
request = PolicyRequest(
    action="network_access",
    resource="network",
    context={
        "url": "http://169.254.169.254/latest/meta-data",
        "environment": "production"
    }
)

result = engine.evaluate_policy(request)
# ❌ DENIED - "Cannot access sensitive endpoint: 169.254.169.254"
```

## Audit Logging

All policy decisions are logged to the audit log file:

```json
{
  "action": "execute",
  "resource": "sandbox",
  "context": {"risk_level": "HIGH", "approved_by": null},
  "decision": "deny",
  "allowed": false,
  "reasons": ["HIGH risk execution requires approval"],
  "violations": ["policy_violation:ai_investor/sandbox/execute"],
  "policy_path": "ai_investor/sandbox/execute"
}
```

## Health Check

```python
# Check if OPA server is healthy
if engine.is_healthy():
    print("✅ OPA server is healthy")
else:
    print("❌ OPA server is not responding")
```

## Context Manager

```python
# Use as context manager
with OPAEngine() as engine:
    engine.load_policies()
    result = engine.evaluate_policy(request)
    # Client automatically closed
```

## Testing

Run policy engine tests:

```bash
pytest tests/test_policy_engine.py -v
```

**Test Coverage**: 15 tests, 100% passing

## Integration

### With Sandbox Execution

```python
from orchestrator.sandbox import DockerSandbox
from orchestrator.policy import OPAEngine, PolicyRequest

engine = OPAEngine()
sandbox = DockerSandbox()

# Evaluate policy before execution
request = PolicyRequest(
    action="execute",
    resource="sandbox",
    context={
        "risk_level": sandbox.config.risk_level,
        "network_access": sandbox.config.network_access,
        "filesystem_readonly": sandbox.config.filesystem_readonly
    }
)

result = engine.evaluate_policy(request)

if result.allowed:
    # Execute in sandbox
    output = sandbox.execute(command)
else:
    raise PermissionError(f"Policy denied: {result.reasons}")
```

## Policy Development

### Writing New Policies

1. Create Rego file in `policies/` directory
2. Use package naming: `ai_investor.<resource>.<action>`
3. Implement `default allow = false` for deny-by-default
4. Define `allow` rules for allowed cases
5. Define `reasons` for denial explanations

Example:

```rego
package ai_investor.custom.action

# Default deny
default allow = false

# Allow rule
allow {
    input.context.condition == "value"
    input.action == "custom_action"
}

# Denial reasons
reasons contains reason {
    not allow
    not input.context.condition
    reason := "condition must be specified"
}
```

## Configuration

### Environment Variables

```bash
# OPA server URL
export OPA_URL="http://localhost:8181"

# Policy directory
export POLICY_DIR="policies"

# Deny by default (true/false)
export DENY_BY_DEFAULT="true"

# Audit log path
export AUDIT_LOG_PATH="policy_audit.log"
```

## References

- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/latest/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [OPA REST API](https://www.openpolicyagent.org/docs/latest/rest-api/)

## Troubleshooting

### OPA Server Not Running

```bash
# Check if OPA is running
curl http://localhost:8181/health

# Start OPA server
./opa run --server --addr localhost:8181
```

### Policy Not Found

If you get "Policy not found" errors:

1. Verify policy files are in `policies/` directory
2. Run `engine.load_policies()` to load all policies
3. Check policy path matches package name in Rego file

### Permission Denied

Check audit log for denial reasons:

```bash
tail -f policy_audit.log | jq
```

---

**Phase 1 - Task 5 Complete** ✅

- OPA Engine: 280 lines
- Policy Schemas: 57 lines
- Rego Policies: 3 files
- Tests: 15 (100% passing)
- Documentation: Complete
