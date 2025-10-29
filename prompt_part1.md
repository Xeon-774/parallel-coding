# GENERIC_PROMPT_V6.1_EN.md

**Version**: 6.1
**Date**: 2025-10-28
**Author**: Claude Code + User
**Changelog**: Added Session Management Policy (Section 18)

---

## 🌐 Language Policy

**User Communication**: ✅ Japanese ONLY
**Technical Content**: ✅ English ONLY (code, comments, git, docs)

---

## 【Mandatory Standards】

### 1-14. [Same as V6.0]

All standards from v6.0 remain unchanged. See [GENERIC_PROMPT_V6_EN.md](GENERIC_PROMPT_V6_EN.md) for:
- Excellence AI Standard (100% compliance)
- Development Guidelines
- Roadmap Reference
- Parallel AI Task Division
- Chat History Preservation
- Refactoring, Git Commits, Session End
- Token Efficiency
- Development Tools Auto-Update
- GitHub Actions Integration
- Codex AI Review System
- AI Consensus Review System
- AI Review Auto-Application
- Codex-Driven Implementation (Sections 15-17)

---

## 🆕 New in v6.1

### 18. 🔄 Session Management Policy

**Philosophy**:
- ✅ **Efficiency First**: Continue sessions when beneficial
- ✅ **Context Preservation**: Leverage existing conversation history
- ⚠️ **Strategic Reset**: Use `/clear` only when necessary

---

#### 18.1 Session Continuation Guidelines

**✅ Continue Session (Recommended)**:
```
Conditions (ALL must be true):
✓ Token remaining > 50,000
✓ Task continuity (related work)
✓ No confusion or repeated errors
✓ Context still relevant

Benefits:
- No need to re-explain context
- Faster task execution
- Better understanding of project state
```

**⚠️ Consider /clear**:
```
Conditions (ANY is true):
! Token remaining < 50,000 (Warning)
! Token remaining < 30,000 (Strong recommendation)
! Major task switch (different project/domain)
! Repeated errors or confusion
! Context became cluttered
```

**🔴 Must /clear**:
```
Conditions (ANY is true):
!! Token remaining < 20,000 (Critical)
!! After compaction message from system
!! Complete project switch
!! User explicitly requests fresh start
```

---

#### 18.2 Token Budget Management

**Token Thresholds**:
```
Budget: 200,000 tokens per session

Zones:
🟢 Green (150K-200K available): Continue freely
🟡 Yellow (50K-150K available): Continue with monitoring
🟠 Orange (30K-50K available): Consider /clear at next milestone
🔴 Red (<30K available): Plan /clear soon
⚫ Critical (<20K available): Execute /clear immediately

Current Status Report (to user, Japanese):
「トークン残量: X,XXX / 200,000 (XX%)
 状態: [🟢継続推奨 | 🟡継続可 | 🟠区切り検討 | 🔴更新推奨]」
```

**Monitoring Strategy**:
```python
# Check token status periodically
if tokens_remaining < 50000:
    inform_user("トークン残量が50K未満です。次の区切りで/clear推奨")

if tokens_remaining < 30000:
    inform_user("🟠 トークン残量が30K未満です。/clear強く推奨")

if tokens_remaining < 20000:
    inform_user("🔴 トークン残量が20K未満です。今すぐ/clear推奨")
```

---

#### 18.3 Session Transition Strategy

**Natural Break Points** (Good times to /clear):
```
✓ Phase completion (Week 2 MVP Phase 1 → Phase 2)
✓ Major milestone (All tests passing, Release ready)
✓ Task category change (Testing → Documentation)
✓ End of work day (preserving progress)
✓ Before major refactoring
```

**Bad Break Points** (Avoid /clear):
```
✗ Middle of debugging
✗ Partial implementation
✗ Active problem-solving
✗ Complex context being built
```

**Handoff Document Template** (Before /clear):
```markdown
## 📊 Session Handoff Document

### Current Status
**Completed**:
- [List completed tasks with file references]

**In Progress**:
- [Current task with status percentage]

**Pending**:
- [Upcoming tasks in priority order]

### 🔧 Environment State
**Setup Completed**:
- Python venv: `venv/` (Python 3.13)
- Dependencies: All installed from requirements.txt
- Database: orchestrator.db (Alembic migrations applied)

**Configuration**:
- Database URL: sqlite:///./orchestrator.db
- JWT: Using calendar.timegm() for exp timestamps
- Test framework: pytest with coverage

### 📝 Important Notes
**Model Field Mappings**:
- Worker: id, workspace_id, status (6 values), metadata
- Job: id, parent_job_id, depth, worker_count, task_description
- IdempotencyKey: request_id (not "key")
- ResourceAllocation: depth, worker_count (not worker_id)

**Known Issues**:
- [List any workarounds or temporary solutions]

**Critical Decisions**:
- [Architecture or implementation choices made]

### ⏭️ Next Steps
1. [Immediate next task] - [Estimated: Xh, Y tokens]
2. [Second priority] - [Estimated: Xh, Y tokens]
3. [Third priority] - [Estimated: Xh, Y tokens]

**Commands to Run**:
```bash
cd dev-tools/parallel-coding
./venv/Scripts/pytest tests/integration/test_week2_api_modules.py -v
./venv/Scripts/pytest tests/integration/test_week2_end_to_end.py -v
```

### 📚 Key Files
- [file:path](path) - Description
- [file:path](path) - Description

### 📊 Test Results
- test_week2_core_foundation.py: 16/16 passed ✅
- test_week2_api_modules.py: Not run yet
- test_week2_end_to_end.py: Not run yet

### 💡 Recommendations
