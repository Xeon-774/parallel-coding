# Roadmap: Cross-Project Compatibility (Universal Portability Initiative)

**Version**: 1.0.0
**Created**: 2025-10-30
**Status**: 🔴 CRITICAL PRIORITY
**Completion Target**: Q1 2026 (Complete within 3 months)

---

## Vision Statement 🎯

**Transform parallel-coding into a truly universal development tool that works seamlessly across any project, platform, and environment without manual configuration.**

**Success Criteria**:
- ✅ Installation time: ≤5 minutes from `git clone` to first execution
- ✅ Zero hardcoded paths, names, or environment-specific values
- ✅ 100% success rate on fresh installations (Windows, Linux, macOS)
- ✅ Auto-detection of all system dependencies
- ✅ Clear, actionable error messages for missing dependencies
- ✅ Comprehensive documentation for any developer

---

## Current State Assessment 📊

### Critical Issues Identified (2025-10-30 Audit)

**Total Hardcoded References**: 106
- Project names (`"AI_Investor"`): 23 instances
- Absolute Windows paths (`D:\user\...`): 38 instances
- User-specific paths (`C:\Users\chemi`): 12 instances
- Environment-specific configs: 33 instances

**Impact**:
- 🔴 Tool cannot be used in fresh projects without manual editing
- 🔴 Tests fail in different environments
- 🔴 Silent failures with unclear error messages
- 🔴 High barrier to adoption in new projects

**Risk Level**: **CRITICAL** - Tool is effectively locked to AI_Investor project

---

## Implementation Phases

### Phase 0: Foundation & Policy (Week 1) ✅ COMPLETED

**Goal**: Establish standards and audit existing code

**Deliverables**:
- ✅ Complete codebase audit (106 issues documented)
- ✅ Create `DEVELOPMENT_POLICY.md`
- ✅ Create `COMPATIBILITY_AUDIT_REPORT.md`
- ✅ Update Excellence AI Standard with no-hardcoding rules
- ✅ Create this roadmap document

**Completion Date**: 2025-10-30

---

### Phase 1: Core Infrastructure (Week 2-3) 🔴 IN PROGRESS

**Goal**: Build foundational systems for configuration and path management

#### 1.1 Configuration System
**Deliverables**:
- [ ] Create `orchestrator/config/environment.py` - Auto-detection logic
- [ ] Create `orchestrator/config/defaults.py` - Safe default values
- [ ] Create `orchestrator/config/validator.py` - Configuration validation
- [ ] Create `.env.template` - User configuration template
- [ ] Update `orchestrator/config.py` to use new system

**Acceptance Criteria**:
- All environment variables follow `PARALLEL_CODING_*` naming
- Auto-detection works for WSL, binaries, paths
- Validation provides clear error messages
- Falls back gracefully when auto-detection fails

#### 1.2 Path Resolution Utility
**Deliverables**:
- [ ] Create `orchestrator/utils/path_resolver.py`
- [ ] Implement `get_project_root()` - Find project root dynamically
- [ ] Implement `get_workspace_path()` - Resolve workspace location
- [ ] Implement `get_config_dir()` - Resolve config directory
- [ ] Add comprehensive unit tests

**Acceptance Criteria**:
- Works with symlinks, submodules, different drives
- Handles Windows, Linux, macOS path conventions
- Returns Path objects (not strings)
- Cached for performance

#### 1.3 Binary Discovery Utility
**Deliverables**:
- [ ] Create `orchestrator/utils/binary_discovery.py`
- [ ] Implement `find_codex()` - Auto-discover Codex CLI
- [ ] Implement `find_claude()` - Auto-discover Claude CLI
- [ ] Implement `find_git()` - Auto-discover Git
- [ ] Implement `detect_wsl()` - Auto-detect WSL distribution
- [ ] Add caching mechanism

**Acceptance Criteria**:
- Checks PATH first, then common install locations
- Provides installation instructions if not found
- Handles npm global installs on Windows/Linux/macOS
- Detects WSL-mounted Windows binaries

**Timeline**: 1 week
**Assigned**: TBD
**Dependencies**: None

---

### Phase 2: Systematic Refactoring (Week 4-6)

**Goal**: Replace all 106 hardcoded references with dynamic resolution

#### 2.1 Configuration Files (10 instances)
**Files to Fix**:
- `config/phase1_execution_config.json`
- `.env` files (if any)
- Test configuration files

**Strategy**: Replace absolute paths with `${PROJECT_ROOT}` placeholders

#### 2.2 Core Modules (45 instances)
**Files to Fix**:
- `orchestrator/core/cli_orchestrator.py` (3 instances)
- `orchestrator/core/hybrid_engine.py` (3 instances)
- `orchestrator/core/hybrid_integration.py` (1 instance)
- `orchestrator/core/worker/codex_executor.py` (already fixed - verify)
- `orchestrator/core/worker/worker_manager.py` (already fixed - verify)
- `orchestrator/core/ai_providers/*.py` (5 instances)

**Strategy**: Use `path_resolver` and `binary_discovery` utilities

#### 2.3 Test Suite (40 instances)
**Files to Fix**:
- `tests/test_cli_orchestrator.py` (9 instances)
- `tests/test_hybrid_engine.py` (12 instances)
- `tests/unit/ai_providers/*.py` (6 instances)
- `test_*.py` files in root (13 instances)

**Strategy**: Use pytest fixtures for all paths

#### 2.4 Documentation & Examples (11 instances)
**Files to Fix**:
- `autonomous_dev_week1.py` (3 instances)
- `scripts/test_codex_review.py` (1 instance)
- `orchestrator/utils/encoding_config.py` (2 instances)
- README examples
- Documentation comments

**Strategy**: Use generic placeholders like `{PROJECT_ROOT}`, `{USER_HOME}`

**Timeline**: 2 weeks
**Assigned**: TBD (Can be parallelized across 3 workers)
**Dependencies**: Phase 1 complete

---

### Phase 3: Testing & Validation (Week 7-8)

**Goal**: Ensure 100% compatibility across environments

#### 3.1 Test Suite Updates
**Deliverables**:
- [ ] Create `tests/conftest.py` with standard fixtures
- [ ] Refactor all tests to use `tmp_path` fixture
- [ ] Add tests for configuration auto-detection
- [ ] Add tests for binary discovery
- [ ] Add tests for path resolution

**Coverage Target**: 100% of path/config code

#### 3.2 Integration Testing
**Deliverables**:
- [ ] Create fresh installation test script
- [ ] Test on Windows 10/11 (with and without WSL)
- [ ] Test on Ubuntu 20.04/22.04/24.04
- [ ] Test on macOS 12+
- [ ] Test as Git submodule
- [ ] Test with different Python versions (3.10, 3.11, 3.12, 3.13)

**Acceptance Criteria**:
- 100% success rate on supported platforms
- All tests pass without manual configuration
- Clear error messages when dependencies missing

#### 3.3 Regression Testing
**Deliverables**:
- [ ] Test AI_Investor project (ensure no breakage)
- [ ] Test ai_trade_project_build0 project
- [ ] Verify all existing functionality works
- [ ] Performance benchmarks (no degradation)

**Timeline**: 1.5 weeks
**Assigned**: TBD
**Dependencies**: Phase 2 complete

---

### Phase 4: Documentation & Tooling (Week 9-10)

**Goal**: Provide world-class setup experience

#### 4.1 User Documentation
**Deliverables**:
- [ ] Create `INSTALLATION.md` - Step-by-step setup guide
- [ ] Create `CONFIGURATION.md` - Complete env var reference
- [ ] Create `TROUBLESHOOTING.md` - Common issues & solutions
- [ ] Update `README.md` - Quick start guide
- [ ] Create `MIGRATION_GUIDE.md` - For existing installations

**Quality Bar**:
- Any developer can install in ≤5 minutes
- Every config option is documented with examples
- Every error message is in troubleshooting guide

#### 4.2 Developer Tools
**Deliverables**:
- [ ] Create `parallel-coding doctor` command - Health check
- [ ] Create `parallel-coding init` command - Interactive setup
- [ ] Create `parallel-coding migrate` command - Auto-migrate old configs
- [ ] Add `--verify` flag to test installation

**Features**:
```bash
$ parallel-coding doctor
✓ Project root detected: /home/user/my-project
✓ Workspace path: /home/user/my-project/workspace
✓ Codex CLI found: /usr/local/bin/codex
✓ Claude CLI found: /home/user/.local/bin/claude
✓ WSL detected: Ubuntu-24.04
✓ Configuration valid
All checks passed! parallel-coding is ready to use.
```

#### 4.3 Pre-commit Hooks
**Deliverables**:
- [ ] Create `.pre-commit-config.yaml`
- [ ] Create `scripts/check_hardcoded_paths.sh` - Scan for violations
- [ ] Create `scripts/check_compatibility.py` - Validate code
- [ ] Integrate with CI/CD pipeline

**Checks**:
- No hardcoded absolute paths
- No project-specific names
- No user-specific paths
- All env vars documented

**Timeline**: 1.5 weeks
**Assigned**: TBD
**Dependencies**: Phase 3 complete

---

### Phase 5: CI/CD & Release (Week 11-12)

**Goal**: Automate testing and prepare for release

#### 5.1 Continuous Integration
**Deliverables**:
- [ ] Set up GitHub Actions workflow
- [ ] Matrix testing: OS × Python version
- [ ] Fresh install testing in Docker
- [ ] Compatibility checks on every PR
- [ ] Auto-generate compatibility matrix

**Platforms**:
- Windows 10/11 (with WSL)
- Ubuntu 20.04, 22.04, 24.04
- macOS 12, 13, 14

**Python Versions**: 3.10, 3.11, 3.12, 3.13

#### 5.2 Release Preparation
**Deliverables**:
- [ ] Version bump to v2.0.0 (breaking changes)
- [ ] Create `CHANGELOG.md` entry
- [ ] Tag release in Git
- [ ] Create GitHub release with notes
- [ ] Update all projects to use v2.0.0

**Migration Plan**:
- Deprecation period: 3 months for v1.x
- Auto-migration tool available
- Side-by-side compatibility for transition

**Timeline**: 1.5 weeks
**Assigned**: TBD
**Dependencies**: Phase 4 complete

---

## Success Metrics 📈

### Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Hardcoded References | 106 | 0 | `grep -r` scan |
| Installation Time | N/A | ≤5 min | Timed fresh install |
| Success Rate | Unknown | ≥99% | CI/CD across platforms |
| Documentation Coverage | ~60% | 100% | All env vars documented |
| Test Coverage (paths/config) | ~40% | 100% | pytest --cov |

### Qualitative Metrics

- [ ] Any developer can install without external help
- [ ] Error messages are clear and actionable
- [ ] No manual code edits required for different projects
- [ ] Tool works on first try in fresh environment
- [ ] Community feedback is positive

---

## Risk Management ⚠️

### High-Impact Risks

#### Risk 1: Breaking Changes in v2.0.0
**Impact**: High - Existing users may face disruption
**Mitigation**:
- 3-month deprecation period
- Auto-migration tool
- Detailed migration guide
- Side-by-side v1/v2 support

#### Risk 2: Platform-Specific Edge Cases
**Impact**: Medium - Some environments may have unique issues
**Mitigation**:
- Comprehensive testing matrix
- Community beta testing
- Fallback to manual configuration
- Clear troubleshooting docs

#### Risk 3: Performance Degradation
**Impact**: Medium - Auto-detection may slow startup
**Mitigation**:
- Cache discovered paths
- Lazy loading for non-critical paths
- Performance benchmarks in CI
- Optimize hot paths

#### Risk 4: Incomplete Refactoring
**Impact**: High - Missing hardcoded references break compatibility
**Mitigation**:
- Automated scanning tools
- Pre-commit hooks
- Code review checklist
- Manual audit before release

---

## Resource Requirements 👥

### Team Composition

**Recommended**: 3 parallel workers + 1 reviewer

**Worker 1**: Configuration & Path Resolution
- Phase 1.1, 1.2
- Estimated: 20 hours

**Worker 2**: Binary Discovery & Core Refactoring
- Phase 1.3, 2.2
- Estimated: 25 hours

**Worker 3**: Test Suite & Documentation
- Phase 2.3, 3.1, 4.1
- Estimated: 30 hours

**Reviewer**: Integration, Testing, Release
- Phases 3.2, 3.3, 5.1, 5.2
- Estimated: 20 hours

**Total Effort**: ~95 hours (12 days @ 8 hrs/day)

---

## Dependencies & Prerequisites 🔗

### External Dependencies
- ✅ Python 3.10+ installed
- ✅ Git installed
- ⚠️ Codex CLI (optional - auto-detected)
- ⚠️ Claude CLI (optional - auto-detected)
- ⚠️ WSL (Windows only - auto-detected)

### Internal Dependencies
- None - This is foundational work

---

## Rollout Strategy 📅

### Beta Testing (Week 11)
- Deploy to ai_trade_project_build0 (already using submodule)
- Deploy to AI_Investor (main project)
- Gather feedback from internal testing
- Fix any critical issues

### Soft Launch (Week 12)
- Release v2.0.0-beta
- Invite community testing
- Monitor GitHub issues
- Iterate based on feedback

### General Availability (Month 4)
- Release v2.0.0 stable
- Deprecate v1.x (3-month timeline)
- Update all documentation
- Announce on relevant channels

---

## Long-Term Vision (Beyond Q1 2026) 🔮

### Phase 6: Package Distribution
- [ ] Publish to PyPI as `parallel-coding`
- [ ] Create standalone CLI tool
- [ ] Support `pip install parallel-coding`
- [ ] Auto-update mechanism

### Phase 7: IDE Integration
- [ ] VS Code extension
- [ ] PyCharm plugin
- [ ] Sublime Text package
- [ ] Vim/Neovim plugin

### Phase 8: Advanced Features
- [ ] Multi-language support (TypeScript, Rust, Go)
- [ ] Cloud worker support (run on cloud instances)
- [ ] Web-based dashboard (monitor all projects)
- [ ] Marketplace for custom workers

---

## Communication Plan 📣

### Internal Communication
- Weekly status updates in team meetings
- Slack channel: #parallel-coding-v2
- GitHub project board for tracking

### External Communication
- Blog post: "Achieving Universal Compatibility"
- Tutorial video: "Installing parallel-coding in 5 minutes"
- Case study: "How we eliminated 106 hardcoded references"

---

## Review & Adaptation 🔄

**Review Frequency**: Bi-weekly
**Review Team**: Core maintainers + stakeholders
**Adaptation Process**:
1. Identify blockers or risks
2. Adjust timeline if needed
3. Re-allocate resources
4. Update roadmap document

**Next Review**: 2025-11-13 (2 weeks from now)

---

## Appendix: Technical Details

### Environment Variable Schema

```bash
# Core Configuration
PARALLEL_CODING_WORKSPACE_ROOT=/path/to/workspace  # Default: {PROJECT_ROOT}/workspace
PARALLEL_CODING_CONFIG_DIR=/path/to/config         # Default: {PROJECT_ROOT}/config
PARALLEL_CODING_CACHE_DIR=/path/to/cache           # Default: {USER_HOME}/.cache/parallel-coding

# Binary Paths (auto-detected if not set)
PARALLEL_CODING_CODEX_PATH=/path/to/codex          # Default: auto-detect
PARALLEL_CODING_CLAUDE_PATH=/path/to/claude        # Default: auto-detect
PARALLEL_CODING_GIT_BASH_PATH=/path/to/git-bash    # Default: auto-detect (Windows)

# WSL Configuration (auto-detected if not set)
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04      # Default: auto-detect
PARALLEL_CODING_NVM_PATH=/path/to/nvm/bin          # Default: $NVM_DIR/current/bin

# Project Metadata
PARALLEL_CODING_PROJECT_NAME=my-project            # Default: directory name
PARALLEL_CODING_ENVIRONMENT=development            # Default: development

# Feature Flags
PARALLEL_CODING_ENABLE_SANDBOX=true                # Default: true
PARALLEL_CODING_ENABLE_WEB_UI=true                 # Default: true
PARALLEL_CODING_LOG_LEVEL=INFO                     # Default: INFO
```

### File Structure After Refactoring

```
parallel-coding/
├── .env.template                    # NEW: Configuration template
├── .pre-commit-config.yaml          # NEW: Pre-commit hooks
├── INSTALLATION.md                  # NEW: Setup guide
├── CONFIGURATION.md                 # NEW: Config reference
├── TROUBLESHOOTING.md               # NEW: Problem solving
├── MIGRATION_GUIDE.md               # NEW: v1 → v2 migration
├── DEVELOPMENT_POLICY.md            # ✅ Created
├── COMPATIBILITY_AUDIT_REPORT.md    # ✅ Created
├── ROADMAP_CROSS_PROJECT_COMPATIBILITY.md  # This file
├── orchestrator/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── environment.py           # NEW: Auto-detection
│   │   ├── defaults.py              # NEW: Safe defaults
│   │   └── validator.py             # NEW: Validation
│   ├── utils/
│   │   ├── path_resolver.py         # NEW: Path utilities
│   │   └── binary_discovery.py      # NEW: Binary discovery
│   └── ...
├── scripts/
│   ├── check_hardcoded_paths.sh     # NEW: Pre-commit check
│   ├── check_compatibility.py       # NEW: Compatibility validator
│   ├── parallel-coding              # NEW: CLI entry point
│   └── ...
└── tests/
    ├── conftest.py                  # NEW: Pytest fixtures
    ├── test_environment.py          # NEW: Config tests
    ├── test_path_resolver.py        # NEW: Path tests
    └── test_binary_discovery.py     # NEW: Discovery tests
```

---

**Document Owner**: Core Maintainers
**Last Updated**: 2025-10-30
**Status**: Living Document (updated bi-weekly)
**Version**: 1.0.0
