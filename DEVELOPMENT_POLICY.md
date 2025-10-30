# Parallel-Coding Development Policy

**Version**: 2.0.0
**Effective Date**: 2025-10-30
**Status**: 🟢 ACTIVE

---

## Core Principles

### 1. Universal Compatibility First 🌍

**Policy Statement**: All code MUST be compatible across different projects, environments, and platforms without manual configuration.

**Rationale**: parallel-coding is a shared development tool used across multiple projects. Any project-specific or environment-specific hardcoding creates technical debt and reduces tool adoption.

**Requirements**:
- ✅ **Zero Hardcoding**: No absolute paths, project names, or user-specific values in code
- ✅ **Auto-Detection**: Automatically discover system dependencies and configurations
- ✅ **Graceful Fallbacks**: Provide sensible defaults when auto-detection fails
- ✅ **Clear Error Messages**: Guide users to fix configuration issues
- ✅ **Cross-Platform**: Support Windows, Linux, macOS, and WSL environments

**Enforcement**:
- Pre-commit hook scans for hardcoded patterns
- CI/CD tests run in isolated Docker containers
- Code review checklist includes compatibility verification

---

### 2. Configuration Hierarchy 📋

**Policy Statement**: Configuration values MUST follow a clear precedence hierarchy.

**Hierarchy** (Highest to Lowest Priority):
1. **Environment Variables** - Set by user (e.g., `PARALLEL_CODING_WORKSPACE`)
2. **`.env` File** - Project-specific overrides
3. **Auto-Detection** - Discovered from system (e.g., `shutil.which("codex")`)
4. **Default Values** - Safe fallbacks defined in code

**Example**:
```python
# ✅ CORRECT: Use hierarchy
workspace = (
    os.getenv("PARALLEL_CODING_WORKSPACE")  # 1. Check env var
    or load_from_dotenv("WORKSPACE_PATH")    # 2. Check .env
    or auto_detect_workspace()               # 3. Auto-detect
    or Path.cwd() / "workspace"              # 4. Default
)

# ❌ WRONG: Hardcoded path
workspace = r"D:\user\ai_coding\AI_Investor\workspace"
```

---

### 3. Path Management Standards 📂

**Policy Statement**: All file system paths MUST be managed through standardized utilities.

**Required Patterns**:

#### A. Project-Relative Paths
```python
# ✅ CORRECT: Relative to project root
from orchestrator.utils.path_resolver import get_project_root

project_root = get_project_root()
workspace = project_root / "workspace"
config_file = project_root / "config" / "settings.yaml"
```

#### B. User Home Directory
```python
# ✅ CORRECT: Use Path.home()
from pathlib import Path

config_dir = Path.home() / ".parallel-coding"
cache_dir = Path.home() / ".cache" / "parallel-coding"

# ❌ WRONG: Hardcoded user path
config_dir = Path("C:/Users/chemi/.parallel-coding")
```

#### C. Temporary Directories
```python
# ✅ CORRECT: Use tempfile
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    test_workspace = Path(tmpdir) / "workspace"
    # ... run tests

# ❌ WRONG: Hardcoded test path
test_workspace = Path("D:/user/ai_coding/test_workspace")
```

#### D. Binary Discovery
```python
# ✅ CORRECT: Auto-discover binaries
from orchestrator.utils.binary_discovery import find_binary

codex_path = find_binary("codex", required=True)
claude_path = find_binary("claude", required=True)
git_path = find_binary("git", required=False)

# ❌ WRONG: Hardcoded binary path
codex_path = "/mnt/c/Users/chemi/AppData/Roaming/npm/codex"
```

---

### 4. Environment Variable Naming Convention 🏷️

**Policy Statement**: All environment variables MUST follow consistent naming.

**Convention**:
- Prefix: `PARALLEL_CODING_`
- Format: `PARALLEL_CODING_{CATEGORY}_{SETTING}`
- Example: `PARALLEL_CODING_WORKSPACE_ROOT`

**Standard Variables**:
```bash
# Core paths
PARALLEL_CODING_WORKSPACE_ROOT=/path/to/workspace
PARALLEL_CODING_CONFIG_DIR=/path/to/config
PARALLEL_CODING_CACHE_DIR=/path/to/cache

# Binary paths (optional - auto-detected if not set)
PARALLEL_CODING_CODEX_PATH=/path/to/codex
PARALLEL_CODING_CLAUDE_PATH=/path/to/claude
PARALLEL_CODING_GIT_BASH_PATH=/path/to/git-bash

# WSL configuration (optional)
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04
PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v22.21.0/bin

# Project metadata
PARALLEL_CODING_PROJECT_NAME=my-project
PARALLEL_CODING_ENVIRONMENT=development

# Feature flags
PARALLEL_CODING_ENABLE_SANDBOX=true
PARALLEL_CODING_ENABLE_WEB_UI=true
```

---

### 5. Testing Standards 🧪

**Policy Statement**: All code MUST be testable in isolated environments.

**Requirements**:

#### A. Test Isolation
```python
# ✅ CORRECT: Use pytest fixtures for paths
@pytest.fixture
def temp_workspace(tmp_path):
    """Create isolated temporary workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace

def test_worker_execution(temp_workspace):
    """Test worker runs in isolated workspace."""
    worker = spawn_worker(workspace=temp_workspace)
    assert worker.success

# ❌ WRONG: Use shared/hardcoded workspace
def test_worker_execution():
    workspace = Path("D:/user/ai_coding/test_workspace")
    worker = spawn_worker(workspace=workspace)
```

#### B. Environment Mocking
```python
# ✅ CORRECT: Mock environment variables
def test_config_loading(monkeypatch):
    """Test config loads from environment."""
    monkeypatch.setenv("PARALLEL_CODING_WORKSPACE_ROOT", "/tmp/test")
    config = load_config()
    assert config.workspace_root == Path("/tmp/test")
```

#### C. Multi-Platform Testing
- CI/CD MUST test on: Windows, Linux, macOS
- CI/CD MUST test with: Python 3.10, 3.11, 3.12, 3.13
- CI/CD MUST test: Fresh install scenario (no .env file)

---

### 6. Documentation Standards 📚

**Policy Statement**: All configurable values MUST be documented.

**Requirements**:

#### A. Inline Documentation
```python
# ✅ CORRECT: Document environment variable usage
def get_workspace_path() -> Path:
    """
    Get workspace path from configuration.

    Resolution order:
    1. PARALLEL_CODING_WORKSPACE_ROOT environment variable
    2. workspace.path in .env file
    3. Auto-detection from project root
    4. Default: {PROJECT_ROOT}/workspace

    Returns:
        Path: Absolute path to workspace directory

    Raises:
        ConfigurationError: If workspace cannot be determined

    Environment Variables:
        PARALLEL_CODING_WORKSPACE_ROOT: Override workspace location

    Examples:
        >>> # Use default
        >>> workspace = get_workspace_path()
        >>> # Override with environment variable
        >>> os.environ["PARALLEL_CODING_WORKSPACE_ROOT"] = "/custom/path"
        >>> workspace = get_workspace_path()
        >>> assert workspace == Path("/custom/path")
    """
    ...
```

#### B. Configuration Guide
- MUST maintain `CONFIGURATION.md` with all variables
- MUST provide `.env.template` with examples
- MUST document auto-detection behavior
- MUST provide troubleshooting guide

---

### 7. Error Handling Standards ⚠️

**Policy Statement**: Configuration errors MUST provide actionable guidance.

**Requirements**:

#### A. Clear Error Messages
```python
# ✅ CORRECT: Helpful error message
if not codex_path:
    raise ConfigurationError(
        "Codex CLI not found.\n\n"
        "Installation options:\n"
        "  1. Install globally: npm install -g @openai/codex\n"
        "  2. Set environment variable: PARALLEL_CODING_CODEX_PATH=/path/to/codex\n"
        "  3. Add to .env: codex.path=/path/to/codex\n\n"
        "For more help, see: https://docs.parallel-coding.dev/setup/codex"
    )

# ❌ WRONG: Vague error
if not codex_path:
    raise FileNotFoundError("Codex not found")
```

#### B. Validation on Startup
```python
# ✅ CORRECT: Validate configuration early
def validate_config(config: OrchestratorConfig) -> None:
    """Validate configuration on startup."""
    errors = []

    if not config.workspace_root.exists():
        errors.append(f"Workspace does not exist: {config.workspace_root}")

    if not config.codex_command_path.exists():
        errors.append(f"Codex CLI not found: {config.codex_command_path}")

    if errors:
        raise ConfigurationError(
            "Configuration validation failed:\n"
            + "\n".join(f"  - {err}" for err in errors)
        )
```

---

### 8. Migration Policy 🔄

**Policy Statement**: Existing installations MUST be migrated gracefully.

**Requirements**:

#### A. Backward Compatibility Window
- Major version changes (v1.x → v2.x): 6-month deprecation period
- Minor version changes (v2.1 → v2.2): 3-month deprecation period
- Patch version changes (v2.1.0 → v2.1.1): Immediate

#### B. Deprecation Warnings
```python
# ✅ CORRECT: Warn about deprecated configuration
if "AI_Investor" in config_dict:
    warnings.warn(
        "Project-specific names in config are deprecated and will be removed in v3.0. "
        "Use PARALLEL_CODING_PROJECT_NAME environment variable instead.",
        DeprecationWarning,
        stacklevel=2
    )
```

#### C. Auto-Migration Tool
- Provide `migrate-config.py` script
- Automatically convert old .env format to new format
- Create backup before migration

---

### 9. Code Review Checklist ✅

**Policy Statement**: All code changes MUST pass compatibility review.

**Checklist for Reviewers**:

- [ ] **No Hardcoded Paths**: Verified with `grep -r "D:/" "C:/" "/d/user"` ✅
- [ ] **No Project Names**: Verified with `grep -r "AI_Investor" "ai_trade_project"` ✅
- [ ] **Environment Variables**: All configs use env vars or auto-detection ✅
- [ ] **Path Utilities**: All paths use `path_resolver` or `Path` methods ✅
- [ ] **Tests Use Fixtures**: No hardcoded paths in tests ✅
- [ ] **Documentation Updated**: New env vars documented in CONFIGURATION.md ✅
- [ ] **Error Messages**: Clear and actionable ✅
- [ ] **Backward Compatibility**: Deprecation warnings added if needed ✅

---

### 10. Continuous Integration Standards 🔁

**Policy Statement**: CI/CD MUST enforce compatibility standards.

**Required CI Checks**:

#### A. Pre-Commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-hardcoded-paths
        name: Check for hardcoded paths
        entry: scripts/check_hardcoded_paths.sh
        language: script
        pass_filenames: false

      - id: check-compatibility
        name: Check cross-project compatibility
        entry: python scripts/check_compatibility.py
        language: python
        pass_filenames: false
```

#### B. CI Pipeline Stages
1. **Lint & Format**: Run black, flake8, mypy
2. **Compatibility Check**: Scan for hardcoded patterns
3. **Unit Tests**: Run in isolated environment
4. **Integration Tests**: Run in Docker container (fresh install)
5. **Platform Tests**: Run on Windows, Linux, macOS
6. **Documentation Build**: Ensure docs are up-to-date

---

### 11. Backward Compatibility Policy 🔄

**Policy Statement**: During active development (pre-v1.0 or major version releases), optimal architecture takes precedence over backward compatibility.

**Rationale**:
- Early-stage projects benefit from rapid iteration and architectural improvements
- Maintaining backward compatibility creates technical debt and slows innovation
- Clear versioning and migration paths provide sufficient user support

**Development Phase Guidelines**:

#### Pre-v1.0 (Current: v2.0.0-dev)
- ❌ **NO backward compatibility required**
- ✅ **Breaking changes are acceptable and encouraged**
- ✅ **Focus on finding the optimal architecture**
- ✅ **Document breaking changes in CHANGELOG**

**Example - Acceptable Breaking Change**:
```python
# v1.x (Old - Hardcoded)
config = OrchestratorConfig(
    workspace="D:\\user\\ai_coding\\AI_Investor\\workspace"
)

# v2.x (New - Auto-detected) ✅ BETTER ARCHITECTURE
config = OrchestratorConfig.from_env()  # Auto-detects workspace
```

#### Post-v1.0 (Stable Releases)
- ✅ **Backward compatibility REQUIRED within major versions**
- ✅ **Use Semantic Versioning strictly**:
  - MAJOR: Breaking changes (v1.0 → v2.0)
  - MINOR: New features, backward compatible (v1.0 → v1.1)
  - PATCH: Bug fixes, backward compatible (v1.0.0 → v1.0.1)
- ✅ **Deprecation warnings before removal** (at least 1 minor version)
- ✅ **Migration guides for major version upgrades**

**Professional Requirements** (All Phases):

1. **Semantic Versioning** ✅
   - Major version bump (v1.0 → v2.0) for breaking changes
   - Clear version number indicates compatibility expectations

2. **CHANGELOG.md** ✅
   ```markdown
   ## [2.0.0] - 2025-11-30
   ### BREAKING CHANGES
   - Configuration system completely rewritten for auto-detection
   - All hardcoded paths removed - use environment variables or auto-detection
   - See MIGRATION.md for upgrade instructions
   ```

3. **Migration Guide** ✅
   - Document all breaking changes
   - Provide step-by-step upgrade instructions
   - Include code examples: "Before" vs "After"
   - Estimate migration time

4. **Deprecation Process** (Post-v1.0) ✅
   ```python
   # Version 1.5.0 - Add deprecation warning
   @deprecated(version="1.5.0", removal="2.0.0",
               alternative="OrchestratorConfig.from_env()")
   def legacy_config_loader():
       warnings.warn("legacy_config_loader is deprecated...")

   # Version 2.0.0 - Remove deprecated code
   # (Only after 1+ minor versions with warning)
   ```

**Decision Matrix**:

| Scenario | Pre-v1.0 Action | Post-v1.0 Action |
|----------|----------------|------------------|
| **Better Architecture Found** | ✅ Implement immediately | ⚠️ Deprecate old → Remove in next major |
| **Performance Improvement (Breaking)** | ✅ Implement immediately | ⚠️ Major version only |
| **Bug Fix (Breaking)** | ✅ Fix immediately | ⚠️ Evaluate severity - may warrant major version |
| **API Design Improvement** | ✅ Implement immediately | ⚠️ Major version only |
| **Security Issue (Breaking)** | ✅ Fix immediately | ✅ Fix immediately (document as exception) |

**Current Project Status**:
- **Version**: 2.0.0-dev (Pre-stable)
- **Policy**: Breaking changes ENCOURAGED for better architecture
- **Target**: Reach stable v2.0.0 by 2025-12-15 (Phase 5 completion)
- **Post-Stable**: Switch to strict backward compatibility within v2.x

**Communication Standards**:
```markdown
# Pull Request Template for Breaking Changes
## Breaking Change Checklist
- [ ] Updated CHANGELOG.md with [BREAKING] tag
- [ ] Incremented major version number
- [ ] Created/updated MIGRATION.md guide
- [ ] Added examples showing old vs new usage
- [ ] Documented in upgrade path
```

**References**:
- Semantic Versioning 2.0.0: https://semver.org/
- Keep a Changelog: https://keepachangelog.com/
- Rust's Stability Promise: https://doc.rust-lang.org/book/appendix-07-nightly-rust.html

---

## Compatibility Commitment 🤝

### World-Class Standard Definition

**parallel-coding commits to**:

1. ✅ **Installation Time**: ≤5 minutes from `git clone` to first execution
2. ✅ **Configuration Time**: ≤2 minutes to customize for specific project
3. ✅ **Success Rate**: ≥99% installation success on supported platforms
4. ✅ **Error Clarity**: 100% of errors provide actionable fix instructions
5. ✅ **Documentation Quality**: Any developer can install without external help
6. ✅ **Zero Manual Edits**: No code changes required for different projects

### Supported Platforms

**Tier 1 (Full Support)**:
- Windows 10/11 with WSL 2 (Ubuntu 20.04+)
- Ubuntu 20.04+ (native)
- macOS 12+ (Monterey and later)

**Tier 2 (Best Effort)**:
- Windows 10/11 (native, without WSL)
- Other Linux distributions (Debian, Fedora, Arch)
- macOS 11 (Big Sur)

**Tier 3 (Community Supported)**:
- Older OS versions
- BSD variants
- Windows with Cygwin

---

## Violation Handling 🚨

### Severity Levels

**CRITICAL** (🔴):
- Hardcoded absolute paths in production code
- Project-specific names in core modules
- Tests that fail in different environments

**HIGH** (🟠):
- Missing documentation for environment variables
- Unclear error messages
- No auto-detection for required binaries

**MEDIUM** (🟡):
- Suboptimal default values
- Missing examples in documentation
- Incomplete test coverage

**LOW** (🟢):
- Code style inconsistencies
- Minor documentation issues
- Non-critical deprecation warnings

### Response Times

- **CRITICAL**: Fix within 24 hours
- **HIGH**: Fix within 1 week
- **MEDIUM**: Fix within 1 month
- **LOW**: Fix in next minor release

---

## Policy Review & Updates 🔄

**Review Frequency**: Quarterly (every 3 months)
**Review Responsible**: Core maintainers
**Update Process**: RFC (Request for Comments) → Review → Vote → Implement

**Next Review Date**: 2025-01-30

---

## Acknowledgments 🙏

This policy is inspired by industry best practices from:
- The Twelve-Factor App methodology
- Django project configuration standards
- Kubernetes configuration management
- Cloud-native application principles

---

**Policy Approved By**: Claude (Sonnet 4.5)
**Date**: 2025-10-30
**Version**: 2.0.0
**Status**: Active

---

## Quick Reference Card 📇

```bash
# ✅ DO: Use environment variables
workspace = os.getenv("PARALLEL_CODING_WORKSPACE_ROOT", default_workspace())

# ❌ DON'T: Use hardcoded paths
workspace = "D:\\user\\ai_coding\\AI_Investor\\workspace"

# ✅ DO: Use path resolution
from orchestrator.utils.path_resolver import get_project_root
config_file = get_project_root() / "config" / "settings.yaml"

# ❌ DON'T: Use absolute paths
config_file = "D:\\user\\ai_coding\\config\\settings.yaml"

# ✅ DO: Auto-discover binaries
codex_path = find_binary("codex")

# ❌ DON'T: Hardcode binary locations
codex_path = "/mnt/c/Users/chemi/AppData/Roaming/npm/codex"

# ✅ DO: Use temporary directories for tests
with tempfile.TemporaryDirectory() as tmpdir:
    test_workspace = Path(tmpdir)

# ❌ DON'T: Use hardcoded test paths
test_workspace = Path("D:/user/ai_coding/test")
```

---

**For questions or clarifications, see**: [CONFIGURATION.md](./CONFIGURATION.md)
