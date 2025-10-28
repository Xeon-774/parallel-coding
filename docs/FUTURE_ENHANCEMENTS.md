# Future Enhancements - Claude Orchestrator

**Last Updated**: 2025-10-22
**Status**: Planning / Backlog

---

## Overview

This document tracks potential future enhancements for the Claude Orchestrator tool. These features are not currently prioritized but may be implemented when time and resources allow.

---

## 🔐 Authentication Enhancements

### API Key & Subscribe Token Login

**Status**: 🟡 Backlog (Low Priority)
**Effort**: 2-3 days
**Value**: Medium

#### Description:

Implement alternative authentication methods beyond WSL Claude CLI:

1. **API Key Authentication**:
   - Direct API key input via `.env` file
   - Validate `sk-ant-` format
   - Use Anthropic API directly (no Claude CLI required)

2. **Subscribe Token Authentication**:
   - Session token from Claude web interface
   - Browser extension integration
   - Auto-refresh token mechanism

#### Use Cases:

- **Environments without WSL**: Linux, macOS users who prefer direct API
- **CI/CD Pipelines**: Automated testing with API keys
- **Enterprise**: Organizations with API key management systems
- **Development**: Quick prototyping without WSL setup

#### Implementation Plan:

```python
# orchestrator/utils/auth_manager.py

class AuthManager:
    """Unified authentication manager supporting multiple methods"""

    def __init__(self):
        self.methods = [
            WSLCLIAuth(),      # Priority 1: WSL Claude CLI (current)
            APIKeyAuth(),      # Priority 2: API Key (future)
            SubscribeTokenAuth()  # Priority 3: Subscribe Token (future)
        ]

    def authenticate(self) -> bool:
        """Try authentication methods in order"""
        for method in self.methods:
            if method.is_available():
                if method.authenticate():
                    self.current_method = method
                    return True
        return False

class APIKeyAuth:
    """API Key authentication via .env"""

    def is_available(self) -> bool:
        return os.getenv("CLAUDE_API_KEY") is not None

    def authenticate(self) -> bool:
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key.startswith("sk-ant-"):
            return False

        # Validate API key with test request
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key},
            json={"model": "claude-3-sonnet-20240229", "max_tokens": 1, "messages": []}
        )

        return response.status_code == 200

class SubscribeTokenAuth:
    """Subscribe token authentication via browser"""

    def is_available(self) -> bool:
        return os.getenv("CLAUDE_SUBSCRIBE_TOKEN") is not None

    def authenticate(self) -> bool:
        token = os.getenv("CLAUDE_SUBSCRIBE_TOKEN")

        # Validate token via Claude web API
        response = requests.get(
            "https://claude.ai/api/auth/current_user",
            headers={"Cookie": f"sessionKey={token}"}
        )

        return response.status_code == 200
```

#### Configuration Example:

```bash
# .env file

# Method 1: WSL Claude CLI (Current - Highest Priority)
# Just login via: wsl -d Ubuntu-24.04 && claude

# Method 2: API Key (Future - Fallback)
CLAUDE_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXX

# Method 3: Subscribe Token (Future - Fallback)
CLAUDE_SUBSCRIBE_TOKEN=sess-XXXXXXXXXXXXXXXXXXXX
```

#### Benefits:

- ✅ **Flexibility**: Users can choose authentication method
- ✅ **Fallback**: If WSL fails, try API key
- ✅ **CI/CD Friendly**: API keys work in automated pipelines
- ✅ **Developer Experience**: Quick setup for prototyping

#### Challenges:

- ⚠️ **Token Management**: API keys need secure storage
- ⚠️ **Token Refresh**: Subscribe tokens expire, need refresh logic
- ⚠️ **Error Handling**: Clear error messages for each method
- ⚠️ **Documentation**: More complex setup instructions

#### Dependencies:

- Anthropic API client library
- Token validation logic
- Secure storage mechanism (keyring?)

#### Testing:

```python
# tests/test_auth_manager.py

def test_wsl_cli_auth_priority():
    """WSL CLI should be tried first"""
    manager = AuthManager()
    assert isinstance(manager.methods[0], WSLCLIAuth)

def test_api_key_fallback():
    """API key should work if WSL unavailable"""
    os.environ["CLAUDE_API_KEY"] = "sk-ant-api03-test"
    # Mock WSL as unavailable
    # ... test API key auth

def test_subscribe_token_fallback():
    """Subscribe token should work as last resort"""
    os.environ["CLAUDE_SUBSCRIBE_TOKEN"] = "sess-test"
    # ... test subscribe token auth
```

#### Priority:

- 🟡 **Low Priority** (Phase 2 or later)
- Current WSL CLI method is sufficient for most use cases
- Implement only when:
  - Multiple users request it
  - CI/CD integration becomes critical
  - WSL approach shows limitations

---

## 🚀 Other Future Enhancements

### 1. Multi-Cloud Support

**Status**: 🟡 Backlog
**Effort**: 1-2 weeks

- Support AWS Bedrock Claude API
- Support Google Cloud Vertex AI
- Support Azure OpenAI Service (if Claude available)

### 2. Enhanced Monitoring

**Status**: 🟡 Backlog
**Effort**: 3-5 days

- Prometheus metrics export
- Grafana dashboards
- Alert system (Slack, Email)

### 3. Cost Tracking

**Status**: 🟡 Backlog
**Effort**: 2-3 days

- Track API usage per worker
- Cost estimation before execution
- Budget alerts

### 4. Worker Persistence

**Status**: 🟡 Backlog
**Effort**: 1 week

- Save worker state to disk
- Resume interrupted orchestration
- Crash recovery

### 5. Advanced Task Decomposition

**Status**: 🟡 Backlog
**Effort**: 2-3 weeks

- AI-driven task splitting
- Dependency graph analysis
- Optimal parallelization strategy

---

## 📋 Tracking

### How to Promote to Active Development:

1. Create GitHub Issue with enhancement proposal
2. Gather user feedback
3. Create detailed design document
4. Estimate effort and prioritize
5. Add to sprint backlog

### Decision Criteria:

- **User Demand**: 3+ users request it
- **Value**: High impact on productivity
- **Effort**: Reasonable implementation time
- **Risk**: Low risk to existing functionality

---

## 🤝 Contributing

If you'd like to implement any of these enhancements:

1. Open a GitHub Issue to discuss
2. Get approval from maintainers
3. Create feature branch
4. Implement with tests
5. Submit Pull Request

---

**Note**: This document is a living backlog. Features may be added, removed, or reprioritized based on project needs.

**Contact**: AI Architecture Team
**Last Review**: 2025-10-22
