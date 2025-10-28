# AI Consensus Review System - Design Specification

**Document Version**: 1.0
**Created**: 2025-10-28
**Status**: Planned (Future Enhancement)
**Priority**: Medium (Week 4-5 candidate)

---

## Executive Summary

AI Consensus Review System enables multiple AI workers to independently develop solutions, then cross-review each other's code to identify issues, alternative approaches, and best practices. This creates a deliberative system that improves code quality through diverse AI perspectives.

**Key Concept**: "AI合議制" (AI Consensus/Deliberation System)

---

## 1. System Overview

### 1.1 Architecture

```
Orchestrator
├── Task Assignment Phase
│   ├── Worker A: Implement Feature X (independent)
│   ├── Worker B: Implement Feature X (independent)
│   └── Worker C: Implement Feature X (independent)
│
├── Cross-Review Phase
│   ├── Worker A reviews B's code → Feedback A→B
│   ├── Worker A reviews C's code → Feedback A→C
│   ├── Worker B reviews A's code → Feedback B→A
│   ├── Worker B reviews C's code → Feedback B→C
│   ├── Worker C reviews A's code → Feedback C→A
│   └── Worker C reviews B's code → Feedback C→B
│
├── Synthesis Phase
│   ├── Aggregate feedback matrix
│   ├── Identify common issues (mentioned by 2+ reviewers)
│   ├── Extract best practices (praised by 2+ reviewers)
│   └── Generate consensus report
│
└── Integration Phase
    ├── Select best implementation (highest score)
    ├── Apply feedback from peer reviews
    └── Merge best ideas from all implementations
```

### 1.2 Core Principles

1. **Independence**: Workers develop without seeing each other's solutions
2. **Diversity**: Different AI models/temperatures for varied approaches
3. **Structured Feedback**: Standardized review format for comparison
4. **Consensus Detection**: Algorithmic identification of agreement/disagreement
5. **Best-of-Breed**: Select optimal components from multiple solutions

---

## 2. Use Cases

### UC-1: Parallel Algorithm Implementation

**Scenario**: Implement a complex sorting algorithm

**Flow**:
1. Three workers independently implement quicksort
2. Worker A uses recursive approach
3. Worker B uses iterative approach
4. Worker C uses hybrid approach
5. Cross-review reveals:
   - Worker A: "Worker B's iterative version avoids stack overflow risk"
   - Worker B: "Worker C's hybrid approach has better cache locality"
   - Worker C: "Worker A's recursive version is most readable"
6. Final implementation: Hybrid approach with readable structure

**Outcome**: Best algorithm with insights from all approaches

---

### UC-2: API Design Review

**Scenario**: Design RESTful API for user management

**Flow**:
1. Three workers design API endpoints independently
2. Worker A: Resource-oriented (users as primary resource)
3. Worker B: Action-oriented (register/login/logout actions)
4. Worker C: GraphQL-inspired (single endpoint with query language)
5. Cross-review identifies:
   - Common feedback: All agree authentication must be JWT-based
   - Divergent opinions: REST vs GraphQL tradeoffs
   - Security issues: Worker B missed rate limiting (caught by A & C)
6. Consensus report highlights security gaps and design tradeoffs

**Outcome**: Comprehensive design with security issues caught early

---

### UC-3: Bug Fix Verification

**Scenario**: Fix a concurrency bug in multi-threaded code

**Flow**:
1. Three workers independently fix the bug
2. Worker A: Uses mutex locks
3. Worker B: Uses atomic operations
4. Worker C: Refactors to avoid shared state
5. Cross-review findings:
   - Worker A's solution: Simple but potential deadlock risk
   - Worker B's solution: Fast but complex memory model
   - Worker C's solution: Safest but requires more refactoring
6. Consensus: Use Worker C's approach with Worker B's atomic primitives for critical sections

**Outcome**: Robust fix combining best ideas from all solutions

---

## 3. Technical Design

### 3.1 Data Models

```python
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ConsensusPhase(str, Enum):
    """Phases of consensus review workflow"""
    TASK_ASSIGNMENT = "task_assignment"
    INDEPENDENT_DEVELOPMENT = "independent_development"
    CROSS_REVIEW = "cross_review"
    SYNTHESIS = "synthesis"
    INTEGRATION = "integration"

class WorkerImplementation(BaseModel):
    """Worker's implementation of assigned task"""
    worker_id: str
    task_description: str
    implementation_path: str  # Path to code files
    implementation_summary: str  # Brief description of approach
    execution_time_seconds: float
    test_results: Optional[Dict[str, Any]] = None
    self_assessment_score: float = Field(ge=0.0, le=100.0)

class PeerReviewFeedback(BaseModel):
    """Feedback from one worker reviewing another's code"""
    reviewer_id: str  # Worker who gave feedback
    reviewee_id: str  # Worker whose code was reviewed

    # Structured feedback (extends ReviewFeedback from base_review_provider)
    strengths: List[str] = Field(description="Identified strengths")
    weaknesses: List[str] = Field(description="Identified weaknesses")
    alternative_approaches: List[str] = Field(description="Alternative ideas")
    security_concerns: List[str] = Field(default_factory=list)
    performance_concerns: List[str] = Field(default_factory=list)

    overall_score: float = Field(ge=0.0, le=100.0)
    recommendation: str = Field(description="Accept/Revise/Reject with rationale")

class ConsensusReport(BaseModel):
    """Aggregated analysis of all implementations and reviews"""
    task_id: str
    implementations: List[WorkerImplementation]
    peer_reviews: List[PeerReviewFeedback]  # N*(N-1) reviews for N workers

    # Consensus analysis
    common_issues: List[str] = Field(description="Issues mentioned by 2+ reviewers")
    best_practices: List[str] = Field(description="Strengths praised by 2+ reviewers")
    controversial_points: List[str] = Field(description="Disagreements between reviewers")

    # Scoring
    implementation_scores: Dict[str, float] = Field(description="worker_id -> avg score")
    recommended_implementation: str = Field(description="worker_id of best implementation")

    # Integration plan
    integration_strategy: str = Field(description="How to merge best ideas")
    action_items: List[str] = Field(description="Specific improvements to apply")

class ConsensusReviewRequest(BaseModel):
    """Request to perform consensus review"""
    task_description: str
    worker_count: int = Field(ge=2, le=5, default=3)
    worker_configs: List[Dict[str, Any]] = Field(description="Per-worker settings")
    review_perspectives: List[ReviewPerspective] = Field(
        description="Perspectives for cross-review"
    )
    require_unanimous_approval: bool = Field(default=False)
    minimum_consensus_threshold: float = Field(
        ge=0.5, le=1.0, default=0.67,
        description="Fraction of workers that must agree"
    )
```

### 3.2 API Endpoints

```
POST /api/consensus/submit
    → Submit task for consensus review
    → Returns consensus_job_id

GET /api/consensus/jobs/{job_id}
    → Get status of consensus review
    → Returns phase, progress, ETA

GET /api/consensus/jobs/{job_id}/implementations
    → Get all worker implementations
    → Returns WorkerImplementation[]

GET /api/consensus/jobs/{job_id}/reviews
    → Get all peer review feedback
    → Returns PeerReviewFeedback[]

GET /api/consensus/jobs/{job_id}/report
    → Get consensus analysis report
    → Returns ConsensusReport

POST /api/consensus/jobs/{job_id}/integrate
    → Execute integration of best implementation
    → Applies feedback and merges ideas
```

### 3.3 Review Matrix

For N workers, generate N*(N-1) reviews (each worker reviews all others):

```
         │ Worker A │ Worker B │ Worker C
─────────┼──────────┼──────────┼─────────
Worker A │    -     │ Review A→B│ Review A→C
Worker B │ Review B→A│    -     │ Review B→C
Worker C │ Review C→A│ Review C→B│    -
```

**Consensus Detection Algorithm**:
```python
def detect_consensus(reviews: List[PeerReviewFeedback], threshold: float) -> ConsensusReport:
    """
    Detect consensus by counting agreement frequency.

    Args:
        reviews: All peer review feedback
        threshold: Minimum fraction of reviewers that must agree

    Returns:
        ConsensusReport with aggregated findings
    """
    issue_counter = Counter()
    strength_counter = Counter()

    for review in reviews:
        for issue in review.weaknesses:
            issue_counter[issue] += 1
        for strength in review.strengths:
            strength_counter[strength] += 1

    n_reviewers = len(set(r.reviewer_id for r in reviews))
    min_count = math.ceil(n_reviewers * threshold)

    common_issues = [issue for issue, count in issue_counter.items() if count >= min_count]
    best_practices = [strength for strength, count in strength_counter.items() if count >= min_count]

    # Controversial: mentioned by some but not consensus
    controversial = [
        issue for issue, count in issue_counter.items()
        if 0 < count < min_count
    ]

    return ConsensusReport(
        common_issues=common_issues,
        best_practices=best_practices,
        controversial_points=controversial,
        ...
    )
```

---

## 4. Implementation Plan

### Phase 1: Core Infrastructure (Week 4 - 20h)

**Tasks**:
- [ ] Extend `JobOrchestrator` with consensus workflow
- [ ] Implement `ConsensusReviewProvider` (extends `BaseReviewProvider`)
- [ ] Add consensus phase state machine
- [ ] Create data models (Pydantic)
- [ ] Database schema for consensus jobs

**Deliverables**:
- `consensus_review_provider.py` (150 lines)
- `consensus_orchestrator.py` (200 lines)
- Database migrations
- Unit tests (80% coverage)

---

### Phase 2: Cross-Review Engine (Week 4 - 15h)

**Tasks**:
- [ ] Implement review matrix generation (N*(N-1) pairs)
- [ ] Create peer review prompt templates
- [ ] Build feedback aggregation logic
- [ ] Implement consensus detection algorithm
- [ ] Add scoring and ranking system

**Deliverables**:
- `peer_review_engine.py` (180 lines)
- Review templates (8 perspectives)
- Consensus detection unit tests
- Integration tests

---

### Phase 3: Synthesis & Integration (Week 5 - 15h)

**Tasks**:
- [ ] Implement consensus report generation
- [ ] Build integration strategy planner
- [ ] Create code merging logic (best-of-breed)
- [ ] Add action item extraction
- [ ] Generate human-readable reports

**Deliverables**:
- `consensus_synthesizer.py` (120 lines)
- Integration strategies (merge, cherry-pick, hybrid)
- Report templates (Markdown, JSON)
- End-to-end tests

---

### Phase 4: API & UI (Week 5 - 10h)

**Tasks**:
- [ ] Add consensus API endpoints (6 endpoints)
- [ ] Create UI for consensus job submission
- [ ] Build review matrix visualization
- [ ] Add consensus report dashboard
- [ ] Implement integration workflow UI

**Deliverables**:
- FastAPI routes (6 endpoints)
- React components (ConsensusView, ReviewMatrix)
- OpenAPI documentation
- Postman collection

---

## 5. Success Criteria

### Functional Requirements
- [ ] **FR-1**: System accepts task description and spawns N workers (N=2-5)
- [ ] **FR-2**: Workers develop solutions independently (no cross-contamination)
- [ ] **FR-3**: Each worker reviews N-1 other solutions (full cross-review)
- [ ] **FR-4**: Consensus algorithm detects agreements (≥67% threshold)
- [ ] **FR-5**: System generates comprehensive consensus report
- [ ] **FR-6**: Integration phase merges best ideas from all implementations
- [ ] **FR-7**: API endpoints return structured consensus data

### Non-Functional Requirements
- [ ] **NFR-1**: Test coverage ≥90% on consensus logic
- [ ] **NFR-2**: Consensus job completes in <5 minutes (3 workers, simple task)
- [ ] **NFR-3**: Review feedback follows Excellence AI Standard format
- [ ] **NFR-4**: Consensus report is human-readable and actionable
- [ ] **NFR-5**: System handles worker failures gracefully (partial consensus)

### Quality Metrics
- [ ] **QM-1**: Consensus detection accuracy ≥95% (validated against human consensus)
- [ ] **QM-2**: Best implementation selected matches expert choice ≥80% of time
- [ ] **QM-3**: Integration phase preserves all test passing status
- [ ] **QM-4**: Peer reviews identify 2-3x more issues than single AI review

---

## 6. Integration with Existing System

### 6.1 Extends Current Review System

```python
# Current: Single AI review
request = ReviewRequest(
    document_path="code.py",
    review_type=ReviewType.CODE,
    perspective=ReviewPerspective.SECURITY
)
result = await codex_provider.review_document(request)

# New: Consensus review
consensus_request = ConsensusReviewRequest(
    task_description="Implement user authentication with JWT",
    worker_count=3,
    review_perspectives=[
        ReviewPerspective.SECURITY,
        ReviewPerspective.ARCHITECTURE,
        ReviewPerspective.MAINTAINABILITY
    ]
)
consensus_report = await consensus_orchestrator.execute(consensus_request)
```

### 6.2 Leverages Existing Providers

- **CodexReviewProvider**: Used for structured peer reviews
- **JobOrchestrator**: Extended with consensus workflow
- **BaseReviewProvider**: Interface reused for consistency

### 6.3 Database Schema Addition

```sql
-- Consensus jobs table
CREATE TABLE consensus_jobs (
    job_id UUID PRIMARY KEY,
    task_description TEXT NOT NULL,
    worker_count INTEGER NOT NULL,
    phase VARCHAR(50) NOT NULL,  -- task_assignment, cross_review, synthesis, etc.
    status VARCHAR(20) NOT NULL,  -- running, completed, failed
    consensus_threshold FLOAT DEFAULT 0.67,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Worker implementations
CREATE TABLE worker_implementations (
    impl_id UUID PRIMARY KEY,
    consensus_job_id UUID REFERENCES consensus_jobs(job_id),
    worker_id VARCHAR(100) NOT NULL,
    implementation_path TEXT NOT NULL,
    implementation_summary TEXT,
    self_assessment_score FLOAT,
    execution_time_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Peer reviews
CREATE TABLE peer_reviews (
    review_id UUID PRIMARY KEY,
    consensus_job_id UUID REFERENCES consensus_jobs(job_id),
    reviewer_id VARCHAR(100) NOT NULL,
    reviewee_id VARCHAR(100) NOT NULL,
    strengths JSONB,
    weaknesses JSONB,
    alternative_approaches JSONB,
    overall_score FLOAT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consensus reports
CREATE TABLE consensus_reports (
    report_id UUID PRIMARY KEY,
    consensus_job_id UUID REFERENCES consensus_jobs(job_id) UNIQUE,
    common_issues JSONB,
    best_practices JSONB,
    controversial_points JSONB,
    implementation_scores JSONB,
    recommended_implementation VARCHAR(100),
    integration_strategy TEXT,
    action_items JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 7. Example Output

### 7.1 Consensus Report Example

```markdown
# Consensus Review Report

**Task**: Implement user authentication with JWT
**Workers**: 3 (Worker A, Worker B, Worker C)
**Completion Time**: 4m 32s
**Consensus Threshold**: 67%

---

## Implementation Scores

| Worker | Avg Score | Recommendation |
|--------|-----------|----------------|
| Worker C | 88.5 | ✅ **Selected** |
| Worker A | 82.0 | Good alternative |
| Worker B | 75.5 | Needs revision |

---

## Common Issues (Consensus: 3/3 reviewers)

1. **Security: Password hashing**
   - All reviewers noted need for Argon2id (not bcrypt)
   - Worker B used plain SHA-256 (critical vulnerability)

2. **Architecture: Token refresh logic**
   - All reviewers flagged missing refresh token rotation
   - Worker C implemented, but A & B missed it

---

## Best Practices (Consensus: 3/3 reviewers)

1. **JWT scope-based authorization**
   - Worker C's implementation praised by all
   - Clear separation of read/write scopes

2. **Comprehensive error handling**
   - Worker A's approach of custom exception classes
   - Adopted in final integration

---

## Controversial Points (No consensus)

1. **Token expiration time**
   - Worker A: 15 minutes (too short, says B & C)
   - Worker B: 24 hours (too long, says A)
   - Worker C: 1 hour (compromise, but A says still long)
   - **Resolution**: Make configurable (env variable)

---

## Integration Plan

**Selected Base**: Worker C's implementation (highest score)

**Improvements from Peer Reviews**:
1. Adopt Worker A's custom exception hierarchy
2. Add Worker B's rate limiting logic (not in C's version)
3. Make token expiration configurable (resolve controversy)
4. Apply security fixes noted by all reviewers

**Estimated Integration Time**: 2 hours
**Risk Level**: Low (Worker C's tests already pass)
```

---

## 8. Future Enhancements

### 8.1 Multi-Model Consensus

- Use different AI models for diversity (GPT-5, Claude Sonnet, Gemini)
- Compare model-specific strengths (e.g., GPT for algorithms, Claude for architecture)

### 8.2 Weighted Voting

- Give more weight to reviews from specialized perspectives
- Security reviews weighted higher for auth code

### 8.3 Iterative Refinement

- After integration, re-run consensus on improved version
- Iterate until unanimous approval or diminishing returns

### 8.4 Learning from Consensus

- Track which workers' implementations are selected most often
- Adjust worker configs to favor successful patterns

### 8.5 🌟 Ecosystem-Wide Retrospective Review (NEW)

**Concept**: Apply consensus review to entire existing codebase for continuous improvement

**Use Cases**:

1. **Legacy Code Review**
   - Review all existing implementations module by module
   - Identify technical debt systematically
   - Propose alternative implementations with better design

2. **Alternative Implementation Generation**
   - AI workers propose completely different architectural approaches
   - Compare current design vs. alternative designs
   - Evaluate migration feasibility

3. **Continuous Refactoring**
   - Periodic review of core modules (monthly/quarterly)
   - Track improvement opportunities over time
   - Prioritize refactoring based on consensus severity

**Architecture**:

```
Ecosystem Archive System
├── Archive Generator
│   ├── Codebase snapshot (git commit hash)
│   ├── Test results snapshot
│   ├── Documentation snapshot
│   ├── Performance metrics
│   └── Known issues / tech debt
│
├── Reference System
│   ├── Module dependency graph
│   ├── API contract history
│   ├── Architecture decision records (ADRs)
│   ├── Design patterns catalog
│   └── Evolution timeline
│
└── Consensus Review Engine
    ├── Load archived snapshot
    ├── Distribute to N workers
    ├── Generate alternative implementations
    ├── Cross-review alternatives vs. current
    └── Generate migration roadmap
```

**Workflow Example**:

```
Phase 1: Archive Current State
├── Generate codebase snapshot (git tag: v1.0-baseline)
├── Export test suite (coverage: 90%)
├── Document current architecture (ARCHITECTURE.md)
└── Catalog known issues (GitHub Issues + tech debt notes)

Phase 2: Distribute Review Tasks
├── Worker A: Review job_orchestrator.py (current implementation)
├── Worker B: Propose alternative orchestrator design (event-driven)
├── Worker C: Propose alternative orchestrator design (actor model)
└── Workers generate independent implementations

Phase 3: Cross-Review
├── Worker A reviews B's event-driven design
├── Worker A reviews C's actor model design
├── Worker B reviews current + C's design
├── Worker C reviews current + B's design
└── Consensus detection: Which approach has most merit?

Phase 4: Migration Planning
├── Aggregate feedback (current vs. alternatives)
├── Score implementations (maintenance, performance, testability)
├── Generate migration roadmap if alternative is superior
└── Estimate migration effort (LOC changes, test updates, risk)
```

**Data Models**:

```python
class EcosystemSnapshot(BaseModel):
    """Complete snapshot of codebase for future reference"""
    snapshot_id: str = Field(description="Unique snapshot ID (git hash + timestamp)")
    git_commit: str = Field(description="Git commit hash")
    created_at: datetime

    # Codebase state
    file_tree: Dict[str, str] = Field(description="path -> file hash")
    total_lines: int
    total_files: int

    # Test state
    test_coverage: float = Field(ge=0.0, le=100.0)
    test_count: int
    test_results: Dict[str, str] = Field(description="test_name -> status")

    # Documentation state
    documentation_files: List[str]
    architecture_diagram: Optional[str] = None

    # Quality metrics
    code_quality_score: float = Field(ge=0.0, le=100.0)
    technical_debt_items: List[str]

    # Performance baselines
    performance_benchmarks: Dict[str, float] = Field(description="benchmark_name -> value")

    # Dependencies
    dependencies: Dict[str, str] = Field(description="package -> version")

class AlternativeImplementation(BaseModel):
    """Alternative implementation proposed by AI worker"""
    alternative_id: str
    snapshot_id: str = Field(description="Reference to original snapshot")
    worker_id: str

    # Alternative design
    module_path: str = Field(description="Path to module being reimplemented")
    design_approach: str = Field(description="e.g., event-driven, actor model, functional")
    implementation_summary: str

    # Changes
    files_modified: List[str]
    files_added: List[str]
    files_deleted: List[str]
    total_lines_changed: int

    # Quality assessment
    self_assessment_score: float = Field(ge=0.0, le=100.0)
    test_coverage: float = Field(ge=0.0, le=100.0)
    performance_improvement: Optional[float] = None  # % improvement

    # Migration complexity
    migration_effort_hours: float
    breaking_changes: List[str]
    migration_risks: List[str]

class EcosystemConsensusReport(BaseModel):
    """Consensus report comparing current implementation vs. alternatives"""
    report_id: str
    snapshot_id: str
    module_path: str

    # Implementations compared
    current_implementation_score: float
    alternative_implementations: List[AlternativeImplementation]

    # Consensus findings
    consensus_recommendation: str = Field(
        description="Keep current / Migrate to Alternative X / Hybrid approach"
    )
    key_improvements: List[str] = Field(description="Improvements from alternatives")
    migration_blockers: List[str] = Field(description="Reasons not to migrate")

    # Migration plan (if recommended)
    migration_phases: Optional[List[str]] = None
    estimated_migration_time: Optional[float] = None
    rollback_strategy: Optional[str] = None
```

**API Endpoints**:

```
# Archive Management
POST /api/ecosystem/snapshots
    → Create new ecosystem snapshot
    → Returns snapshot_id

GET /api/ecosystem/snapshots/{snapshot_id}
    → Get snapshot details

GET /api/ecosystem/snapshots
    → List all snapshots (with filters)

# Alternative Implementation
POST /api/ecosystem/alternatives
    → Request AI workers to generate alternatives for module
    → Returns consensus_job_id

GET /api/ecosystem/alternatives/{job_id}
    → Get alternative implementations and cross-reviews

# Consensus Review
GET /api/ecosystem/consensus/{job_id}/report
    → Get ecosystem consensus report (current vs. alternatives)

POST /api/ecosystem/consensus/{job_id}/migrate
    → Execute migration to selected alternative
    → Returns migration_task_id
```

**Storage Structure**:

```
ecosystem_archive/
├── snapshots/
│   ├── 2025-10-28_fc91011/
│   │   ├── snapshot.json (metadata)
│   │   ├── codebase.tar.gz (full code snapshot)
│   │   ├── test_results.json
│   │   ├── architecture.md
│   │   └── metrics.json
│   └── 2025-11-15_abc1234/
│       └── ...
│
├── alternatives/
│   ├── job_orchestrator_alternatives/
│   │   ├── 2025-10-28_event_driven/
│   │   │   ├── implementation/ (code files)
│   │   │   ├── tests/
│   │   │   ├── design.md
│   │   │   └── metadata.json
│   │   └── 2025-10-28_actor_model/
│   │       └── ...
│   └── ...
│
└── consensus_reports/
    ├── job_orchestrator_consensus_2025-10-28.json
    └── ...
```

**Example Consensus Report**:

```json
{
  "report_id": "eco_consensus_20251028_001",
  "snapshot_id": "2025-10-28_fc91011",
  "module_path": "orchestrator/core/hierarchical/job_orchestrator.py",
  "current_implementation_score": 82.5,
  "alternative_implementations": [
    {
      "alternative_id": "alt_event_driven_001",
      "worker_id": "worker_b",
      "design_approach": "event-driven",
      "self_assessment_score": 88.0,
      "performance_improvement": 15.0,
      "migration_effort_hours": 40.0
    },
    {
      "alternative_id": "alt_actor_model_002",
      "worker_id": "worker_c",
      "design_approach": "actor model",
      "self_assessment_score": 85.5,
      "performance_improvement": 8.0,
      "migration_effort_hours": 60.0
    }
  ],
  "consensus_recommendation": "Migrate to Alternative: alt_event_driven_001 (Phased approach)",
  "key_improvements": [
    "Better separation of concerns (event-driven architecture)",
    "15% performance improvement (async event processing)",
    "Easier to add new job types (event handlers)",
    "Better testability (mock event bus)"
  ],
  "migration_blockers": [
    "Requires event bus infrastructure (not yet implemented)",
    "Breaking changes to API contracts (4 endpoints affected)",
    "Migration time: 40 hours"
  ],
  "migration_phases": [
    "Phase 1: Implement event bus infrastructure (10h)",
    "Phase 2: Migrate job submission to event-driven (15h)",
    "Phase 3: Migrate job lifecycle to event handlers (10h)",
    "Phase 4: Update API layer and tests (5h)"
  ],
  "estimated_migration_time": 40.0,
  "rollback_strategy": "Keep current implementation in parallel branch, feature flag migration"
}
```

**Benefits**:

1. **Historical Context**: Future AI workers can understand evolution
2. **Continuous Improvement**: Regular review finds incremental improvements
3. **Risk Mitigation**: Alternative approaches validated before migration
4. **Knowledge Capture**: Design decisions and tradeoffs documented
5. **Reproducibility**: Any snapshot can be restored and reviewed

**Implementation Priority**: Week 6-8 (Post-MVP)
- Depends on: AI Consensus Review System (Week 4-5)
- Estimated effort: 40 hours
  - Archive system: 15h
  - Alternative generation: 10h
  - Migration planning: 10h
  - UI integration: 5h

---

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Workers produce very similar solutions | Low value | Medium | Use diverse prompts/temperatures |
| Review time scales O(N²) | Performance | High | Parallelize cross-reviews |
| Consensus detection false positives | Wrong selection | Medium | Manual review gate for critical tasks |
| Integration conflicts between best ideas | Failed merge | Medium | Automated conflict detection + human override |

---

## 10. Roadmap Integration

### Recommended Timeline

**Week 4 (Optional Enhancement)**:
- Implement Phases 1-2 (Core + Cross-Review Engine)
- Basic consensus workflow working
- Manual integration (no automated merge)

**Week 5 (Polish)**:
- Implement Phases 3-4 (Synthesis + UI)
- Automated integration strategies
- Full dashboard with visualizations

**Future (Post-MVP)**:
- Multi-model consensus
- Weighted voting
- Iterative refinement

---

## 11. References

- [Base Review Provider](../orchestrator/core/ai_providers/base_review_provider.py)
- [Codex Review Provider](../orchestrator/core/ai_providers/codex_review_provider.py)
- [Job Orchestrator](../orchestrator/core/hierarchical/job_orchestrator.py)
- [Week 2 MVP Specification](./WEEK2_MVP_SPECIFICATION.md)
- [Session Report: Codex Review Applied](../../docs/conversations/SESSION_2025_10_28_CODEX_REVIEW_APPLIED.md)

---

**Document Status**: Ready for roadmap inclusion
**Next Action**: Add to roadmap as Week 4-5 optional enhancement
