# Phase 2.2: Core Monitoring Features - Implementation Plan

**Project**: Parallel AI Coding Tool
**Phase**: 2.2 - Core Monitoring Features
**Created**: 2025-10-24
**Status**: 🚀 Ready to Start
**Estimated Duration**: 1-2 weeks (20-26 hours)

---

## Overview

Phase 2.2 builds upon the validated Phase 1 foundation to add essential monitoring capabilities. These features transform the tool from a basic monitoring system into a comprehensive development insight platform.

**Prerequisites**:
- ✅ Phase 1.1: AI Dialogue Visualization (Complete)
- ✅ Phase 1.2: Terminal Grid Layout UI (Complete)
- ✅ Phase 1.3: Real-time Terminal Capture (Complete & Validated)
- ✅ Phase 2.1: Validation & Stability (Complete)

**Foundation Quality**: Production-ready (20/20 criteria met)

---

## Phase 2.2 Features (Tier 1 - Critical)

### Feature 1: Terminal Output Search & Filtering
**Priority**: 2A
**Effort**: 6-8 hours
**User Value**: High (essential for debugging)

**Capabilities**:
- Real-time search across terminal output
- Highlighted matches with navigation
- Case-sensitive toggle
- Regex support (optional)

### Feature 2: Performance Metrics Collection & Visualization
**Priority**: 2B
**Effort**: 10-12 hours
**User Value**: High (performance optimization)

**Metrics Tracked**:
- Execution time (start → complete)
- Confirmation request count
- Response latency (orchestrator decision time)
- Token usage (if available)
- Memory usage (process level)

### Feature 3: Continuous Output Polling
**Priority**: 2C
**Effort**: 4-6 hours
**User Value**: Medium-High (capture completeness)

**Implementation**:
- Background thread for non-blocking output capture
- Eliminates output gaps between confirmations
- Real-time streaming to log files

---

## Implementation Strategy

### Development Approach

**Principle**: Incremental, validated progress with visual verification

**Order of Implementation**:
1. **Feature 3** (Continuous Output Polling) - Foundation for other features
2. **Feature 2** (Performance Metrics) - Backend infrastructure
3. **Feature 1** (Terminal Search) - Frontend polish

**Rationale**:
- Continuous polling improves data quality for all features
- Metrics collection requires complete output capture
- Search features benefit from metrics for performance tracking

---

## Feature 3: Continuous Output Polling

### Current Limitation

**Problem**: Output only captured at confirmation points

**Impact**:
- Potential loss of rapid output bursts
- Delayed visibility of long-running processes
- Gaps in terminal capture

**Solution**: Background polling thread

### Implementation Design

#### Backend Changes

**File**: `orchestrator/core/worker_manager.py`

**New Method**: `_start_output_capture_thread()`

```python
def _start_output_capture_thread(self, session: WorkerSession) -> None:
    """
    Start background thread for continuous output capture.

    This eliminates gaps in terminal output by polling process stdout/stderr
    continuously rather than only at confirmation points.

    Args:
        session: Worker session to monitor
    """
    def capture_loop():
        """Main capture loop running in background thread"""
        try:
            while session.is_active and not session.stop_capture:
                try:
                    # Non-blocking read with short timeout
                    line = session.child_process.readline_nonblocking(timeout=0.1)

                    if line:
                        # Append to raw output (ANSI stripping already integrated)
                        self._append_raw_output(session, line)

                except pexpect.TIMEOUT:
                    # Expected - no output available, continue polling
                    continue

                except pexpect.EOF:
                    # Process ended, exit capture loop
                    self.logger.info(f"Capture thread: EOF detected for {session.worker_id}")
                    break

                except Exception as e:
                    self.logger.error(f"Capture thread error for {session.worker_id}: {e}")
                    break

        finally:
            session.capture_thread_active = False
            self.logger.info(f"Capture thread stopped for {session.worker_id}")

    # Start background thread
    thread = threading.Thread(
        target=capture_loop,
        name=f"capture-{session.worker_id}",
        daemon=True
    )

    session.capture_thread = thread
    session.capture_thread_active = True
    session.stop_capture = False

    thread.start()
    self.logger.info(f"Capture thread started for {session.worker_id}")
```

**Integration Point**: Call from `run_interactive_session()` after process spawn

```python
def run_interactive_session(self, worker_id: str, task: dict) -> dict:
    """Run worker in interactive mode"""
    # ... existing spawn code ...

    # Start continuous output capture (Phase 2.2)
    self._start_output_capture_thread(session)

    # ... existing confirmation loop ...
```

**Cleanup**: Ensure thread stops on session end

```python
def _cleanup_session(self, session: WorkerSession) -> None:
    """Clean up worker session"""
    # Signal capture thread to stop
    session.stop_capture = True

    # Wait for thread to finish (with timeout)
    if session.capture_thread and session.capture_thread_active:
        session.capture_thread.join(timeout=2.0)
        if session.capture_thread.is_alive():
            self.logger.warning(f"Capture thread did not stop cleanly for {session.worker_id}")

    # ... existing cleanup code ...
```

#### Testing Strategy

**Test 1**: Rapid Output Test
```python
# Test task that generates rapid output bursts
task = {
    "prompt": "Print numbers 1-100 with no delays. Use a loop."
}
# Verify: All 100 numbers captured in raw_terminal.log
```

**Test 2**: Long-Running Process
```python
# Test task with multi-minute execution
task = {
    "prompt": "List all files in a large directory tree. This may take 2-3 minutes."
}
# Verify: Output appears in real-time, no gaps
```

**Test 3**: Thread Cleanup
```python
# Spawn worker, let it run 10s, terminate
# Verify: Capture thread stops cleanly, no lingering threads
```

### Success Criteria

- ✅ Capture thread starts automatically with worker spawn
- ✅ Output appears within 100ms of process generation
- ✅ No data loss (100% capture)
- ✅ Thread stops cleanly on session end
- ✅ No memory leaks with multiple workers
- ✅ No performance degradation

### Risk Mitigation

**Risk**: Thread synchronization issues
**Mitigation**: Use thread-safe file writes (already implemented with `f.flush()`)

**Risk**: Thread doesn't stop on EOF
**Mitigation**: Implement timeout-based join, log warnings

**Risk**: High CPU usage from polling
**Mitigation**: Use 100ms timeout (10 polls/sec max)

---

## Feature 2: Performance Metrics Collection

### Metrics Design

#### Metric Schema

**File Format**: JSONL (JSON Lines) at `workspace/{worker_id}/metrics.jsonl`

**Metric Types**:

```typescript
// Worker lifecycle events
type WorkerLifecycleMetric = {
  type: "worker_lifecycle"
  timestamp: string  // ISO 8601
  worker_id: string
  event: "spawned" | "completed" | "failed" | "terminated"
  duration_seconds?: number  // For completion events
}

// Confirmation events
type ConfirmationMetric = {
  type: "confirmation"
  timestamp: string
  worker_id: string
  confirmation_number: number
  orchestrator_latency_ms: number  // Time to make decision
  response: "approved" | "rejected" | "pending"
}

// Output events
type OutputMetric = {
  type: "output"
  timestamp: string
  worker_id: string
  output_size_bytes: number
  line_count: number
}

// Performance snapshot
type PerformanceMetric = {
  type: "performance"
  timestamp: string
  worker_id: string
  memory_mb: number
  cpu_percent: number  // If available
}

type Metric = WorkerLifecycleMetric | ConfirmationMetric | OutputMetric | PerformanceMetric
```

### Implementation

#### Backend: Metrics Collector

**New File**: `orchestrator/core/metrics_collector.py`

```python
"""
Performance Metrics Collection System

Tracks worker execution metrics for performance analysis and visualization.
Phase 2.2 implementation.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class MetricType(Enum):
    """Metric type enumeration"""
    WORKER_LIFECYCLE = "worker_lifecycle"
    CONFIRMATION = "confirmation"
    OUTPUT = "output"
    PERFORMANCE = "performance"


class WorkerEvent(Enum):
    """Worker lifecycle events"""
    SPAWNED = "spawned"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class Metric:
    """Base metric class"""
    type: str
    timestamp: str
    worker_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class WorkerLifecycleMetric(Metric):
    """Worker lifecycle event metric"""
    event: str
    duration_seconds: Optional[float] = None


@dataclass
class ConfirmationMetric(Metric):
    """Confirmation request metric"""
    confirmation_number: int
    orchestrator_latency_ms: float
    response: str


@dataclass
class OutputMetric(Metric):
    """Output capture metric"""
    output_size_bytes: int
    line_count: int


@dataclass
class PerformanceMetric(Metric):
    """Performance snapshot metric"""
    memory_mb: float
    cpu_percent: Optional[float] = None


class MetricsCollector:
    """
    Collects and persists worker performance metrics.

    Metrics are written to workspace/{worker_id}/metrics.jsonl in JSONL format
    (one JSON object per line) for easy streaming and analysis.
    """

    def __init__(self, workspace_root: Path):
        """
        Initialize metrics collector.

        Args:
            workspace_root: Root workspace directory
        """
        self.workspace_root = workspace_root
        self.worker_start_times: Dict[str, float] = {}

    def _get_metrics_file(self, worker_id: str) -> Path:
        """Get metrics file path for worker"""
        worker_workspace = self.workspace_root / worker_id
        worker_workspace.mkdir(parents=True, exist_ok=True)
        return worker_workspace / "metrics.jsonl"

    def _write_metric(self, worker_id: str, metric: Metric) -> None:
        """
        Append metric to metrics file.

        Args:
            worker_id: Worker identifier
            metric: Metric to write
        """
        metrics_file = self._get_metrics_file(worker_id)

        try:
            with open(metrics_file, 'a', encoding='utf-8') as f:
                json.dump(metric.to_dict(), f, ensure_ascii=False)
                f.write('\n')
                f.flush()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to write metric: {e}")

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO 8601 format"""
        return datetime.utcnow().isoformat() + 'Z'

    # Worker lifecycle metrics

    def record_worker_spawned(self, worker_id: str) -> None:
        """Record worker spawn event"""
        self.worker_start_times[worker_id] = time.time()

        metric = WorkerLifecycleMetric(
            type=MetricType.WORKER_LIFECYCLE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            event=WorkerEvent.SPAWNED.value
        )
        self._write_metric(worker_id, metric)

    def record_worker_completed(self, worker_id: str) -> None:
        """Record worker completion event"""
        duration = None
        if worker_id in self.worker_start_times:
            duration = time.time() - self.worker_start_times[worker_id]
            del self.worker_start_times[worker_id]

        metric = WorkerLifecycleMetric(
            type=MetricType.WORKER_LIFECYCLE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            event=WorkerEvent.COMPLETED.value,
            duration_seconds=duration
        )
        self._write_metric(worker_id, metric)

    def record_worker_failed(self, worker_id: str) -> None:
        """Record worker failure event"""
        duration = None
        if worker_id in self.worker_start_times:
            duration = time.time() - self.worker_start_times[worker_id]
            del self.worker_start_times[worker_id]

        metric = WorkerLifecycleMetric(
            type=MetricType.WORKER_LIFECYCLE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            event=WorkerEvent.FAILED.value,
            duration_seconds=duration
        )
        self._write_metric(worker_id, metric)

    # Confirmation metrics

    def record_confirmation(
        self,
        worker_id: str,
        confirmation_number: int,
        orchestrator_latency_ms: float,
        response: str
    ) -> None:
        """
        Record confirmation request and orchestrator response.

        Args:
            worker_id: Worker identifier
            confirmation_number: Sequential confirmation number (1, 2, 3...)
            orchestrator_latency_ms: Time orchestrator took to make decision
            response: "approved", "rejected", or "pending"
        """
        metric = ConfirmationMetric(
            type=MetricType.CONFIRMATION.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            confirmation_number=confirmation_number,
            orchestrator_latency_ms=orchestrator_latency_ms,
            response=response
        )
        self._write_metric(worker_id, metric)

    # Output metrics

    def record_output(
        self,
        worker_id: str,
        output_size_bytes: int,
        line_count: int
    ) -> None:
        """
        Record output capture event.

        Args:
            worker_id: Worker identifier
            output_size_bytes: Size of captured output in bytes
            line_count: Number of lines captured
        """
        metric = OutputMetric(
            type=MetricType.OUTPUT.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            output_size_bytes=output_size_bytes,
            line_count=line_count
        )
        self._write_metric(worker_id, metric)

    # Performance metrics

    def record_performance(
        self,
        worker_id: str,
        memory_mb: float,
        cpu_percent: Optional[float] = None
    ) -> None:
        """
        Record performance snapshot.

        Args:
            worker_id: Worker identifier
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage (if available)
        """
        metric = PerformanceMetric(
            type=MetricType.PERFORMANCE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent
        )
        self._write_metric(worker_id, metric)

    # Query methods

    def get_metrics(self, worker_id: str) -> List[Dict[str, Any]]:
        """
        Get all metrics for a worker.

        Args:
            worker_id: Worker identifier

        Returns:
            List of metrics as dictionaries
        """
        metrics_file = self._get_metrics_file(worker_id)

        if not metrics_file.exists():
            return []

        metrics = []
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        metrics.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to read metrics: {e}")

        return metrics

    def get_metrics_summary(self, worker_id: str) -> Dict[str, Any]:
        """
        Get aggregated metrics summary for a worker.

        Returns:
            Dictionary with summary statistics
        """
        metrics = self.get_metrics(worker_id)

        if not metrics:
            return {
                "worker_id": worker_id,
                "total_metrics": 0,
                "status": "no_data"
            }

        # Aggregate by metric type
        confirmations = [m for m in metrics if m.get("type") == "confirmation"]
        outputs = [m for m in metrics if m.get("type") == "output"]
        lifecycles = [m for m in metrics if m.get("type") == "worker_lifecycle"]

        # Calculate summary stats
        total_confirmations = len(confirmations)
        avg_latency = (
            sum(m["orchestrator_latency_ms"] for m in confirmations) / total_confirmations
            if confirmations else 0
        )

        total_output_bytes = sum(m.get("output_size_bytes", 0) for m in outputs)
        total_lines = sum(m.get("line_count", 0) for m in outputs)

        # Get duration from completion event
        duration_seconds = None
        completed_event = next(
            (m for m in lifecycles if m.get("event") == "completed"),
            None
        )
        if completed_event:
            duration_seconds = completed_event.get("duration_seconds")

        return {
            "worker_id": worker_id,
            "total_metrics": len(metrics),
            "confirmations": {
                "count": total_confirmations,
                "avg_latency_ms": avg_latency
            },
            "output": {
                "total_bytes": total_output_bytes,
                "total_lines": total_lines
            },
            "execution": {
                "duration_seconds": duration_seconds
            }
        }
```

**Integration into WorkerManager**:

```python
# In orchestrator/core/worker_manager.py

from orchestrator.core.metrics_collector import MetricsCollector

class WorkerManager:
    def __init__(self, config: ConfigModel):
        # ... existing initialization ...

        # Initialize metrics collector (Phase 2.2)
        self.metrics = MetricsCollector(workspace_root=Path(config.workspace_root))

    def run_interactive_session(self, worker_id: str, task: dict) -> dict:
        """Run worker in interactive mode"""

        # Record spawn
        self.metrics.record_worker_spawned(worker_id)

        try:
            # ... existing code ...

            # Record completion
            self.metrics.record_worker_completed(worker_id)

        except Exception as e:
            # Record failure
            self.metrics.record_worker_failed(worker_id)
            raise

    def _handle_confirmation_request(self, session: WorkerSession, output: str) -> str:
        """Handle confirmation request"""

        # Record start time for latency measurement
        decision_start = time.time()

        # ... existing decision logic ...

        # Record confirmation metric
        decision_latency_ms = (time.time() - decision_start) * 1000
        self.metrics.record_confirmation(
            worker_id=session.worker_id,
            confirmation_number=session.confirmation_count,
            orchestrator_latency_ms=decision_latency_ms,
            response="approved"  # or "rejected" based on actual decision
        )

        return decision
```

#### Backend: Metrics API

**New File**: `orchestrator/api/metrics_api.py`

```python
"""
Metrics API Endpoints

Provides access to worker performance metrics for visualization.
Phase 2.2 implementation.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List, Dict, Any

from orchestrator.core.metrics_collector import MetricsCollector
from orchestrator.config import get_config

router = APIRouter(prefix="/api/v1", tags=["metrics"])

# Initialize metrics collector
config = get_config()
metrics_collector = MetricsCollector(workspace_root=Path(config.workspace_root))


@router.get("/workers/{worker_id}/metrics")
async def get_worker_metrics(worker_id: str) -> Dict[str, Any]:
    """
    Get all metrics for a worker.

    Returns:
        {
            "worker_id": str,
            "metrics": [...]
        }
    """
    metrics = metrics_collector.get_metrics(worker_id)

    return {
        "worker_id": worker_id,
        "metrics": metrics,
        "count": len(metrics)
    }


@router.get("/workers/{worker_id}/metrics/summary")
async def get_worker_metrics_summary(worker_id: str) -> Dict[str, Any]:
    """
    Get aggregated metrics summary for a worker.

    Returns:
        {
            "worker_id": str,
            "total_metrics": int,
            "confirmations": {...},
            "output": {...},
            "execution": {...}
        }
    """
    summary = metrics_collector.get_metrics_summary(worker_id)
    return summary
```

**Register routes in main app**:

```python
# In orchestrator/api/main.py

from orchestrator.api import metrics_api

app.include_router(metrics_api.router)
```

### Testing Strategy

**Unit Tests**: `tests/test_metrics_collector.py`

```python
def test_worker_lifecycle_metrics():
    """Test worker lifecycle event recording"""
    # Record spawn, completion
    # Verify metrics.jsonl contains correct entries
    # Verify duration calculation

def test_confirmation_metrics():
    """Test confirmation metric recording"""
    # Record multiple confirmations
    # Verify latency tracking
    # Verify sequential numbering

def test_metrics_summary():
    """Test summary aggregation"""
    # Create sample metrics
    # Get summary
    # Verify averages, counts
```

**Integration Test**: `tests/test_metrics_integration.py`

```python
def test_end_to_end_metrics():
    """Test metrics collection during actual worker execution"""
    # Run validation task
    # Verify all metric types recorded
    # Verify API endpoints work
```

---

## Feature 1: Terminal Output Search

### UI Design

**Component Hierarchy**:
```
TerminalView
├── TerminalSearchBar (NEW)
│   ├── SearchInput
│   ├── CaseSensitiveToggle
│   ├── RegexToggle
│   └── NavigationButtons (Next/Prev)
└── TerminalContent (MODIFIED)
    └── Highlighted matches in yellow
```

### Frontend Implementation

**New File**: `frontend/src/components/TerminalSearchBar.tsx`

```typescript
import React, { useState } from 'react';

interface TerminalSearchBarProps {
  onSearch: (query: string, caseSensitive: boolean, useRegex: boolean) => void;
  currentMatch: number;
  totalMatches: number;
  onNext: () => void;
  onPrevious: () => void;
}

export const TerminalSearchBar: React.FC<TerminalSearchBarProps> = ({
  onSearch,
  currentMatch,
  totalMatches,
  onNext,
  onPrevious
}) => {
  const [query, setQuery] = useState('');
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [useRegex, setUseRegex] = useState(false);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    setQuery(newQuery);
    onSearch(newQuery, caseSensitive, useRegex);
  };

  return (
    <div className="terminal-search-bar">
      <input
        type="text"
        value={query}
        onChange={handleSearchChange}
        placeholder="Search terminal output..."
        className="search-input"
      />

      <label>
        <input
          type="checkbox"
          checked={caseSensitive}
          onChange={(e) => {
            setCaseSensitive(e.target.checked);
            onSearch(query, e.target.checked, useRegex);
          }}
        />
        Case sensitive
      </label>

      <label>
        <input
          type="checkbox"
          checked={useRegex}
          onChange={(e) => {
            setUseRegex(e.target.checked);
            onSearch(query, caseSensitive, e.target.checked);
          }}
        />
        Regex
      </label>

      {query && (
        <div className="match-navigation">
          <span className="match-count">
            {totalMatches > 0 ? `${currentMatch + 1} of ${totalMatches}` : 'No matches'}
          </span>
          <button onClick={onPrevious} disabled={totalMatches === 0}>
            ↑ Previous
          </button>
          <button onClick={onNext} disabled={totalMatches === 0}>
            ↓ Next
          </button>
        </div>
      )}
    </div>
  );
};
```

**New Hook**: `frontend/src/hooks/useTerminalSearch.ts`

```typescript
import { useState, useMemo } from 'react';

interface SearchMatch {
  lineIndex: number;
  startIndex: number;
  endIndex: number;
  text: string;
}

export const useTerminalSearch = (lines: string[]) => {
  const [query, setQuery] = useState('');
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [useRegex, setUseRegex] = useState(false);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);

  // Find all matches
  const matches = useMemo<SearchMatch[]>(() => {
    if (!query) return [];

    const results: SearchMatch[] = [];

    try {
      const pattern = useRegex
        ? new RegExp(query, caseSensitive ? 'g' : 'gi')
        : null;

      lines.forEach((line, lineIndex) => {
        if (useRegex && pattern) {
          // Regex search
          let match;
          while ((match = pattern.exec(line)) !== null) {
            results.push({
              lineIndex,
              startIndex: match.index,
              endIndex: match.index + match[0].length,
              text: match[0]
            });
          }
        } else {
          // Plain text search
          const searchLine = caseSensitive ? line : line.toLowerCase();
          const searchQuery = caseSensitive ? query : query.toLowerCase();

          let index = 0;
          while ((index = searchLine.indexOf(searchQuery, index)) !== -1) {
            results.push({
              lineIndex,
              startIndex: index,
              endIndex: index + query.length,
              text: line.substring(index, index + query.length)
            });
            index += query.length;
          }
        }
      });
    } catch (e) {
      // Invalid regex, return no matches
      console.warn('Invalid search pattern:', e);
    }

    return results;
  }, [lines, query, caseSensitive, useRegex]);

  const handleSearch = (newQuery: string, newCaseSensitive: boolean, newUseRegex: boolean) => {
    setQuery(newQuery);
    setCaseSensitive(newCaseSensitive);
    setUseRegex(newUseRegex);
    setCurrentMatchIndex(0); // Reset to first match
  };

  const goToNextMatch = () => {
    if (matches.length > 0) {
      setCurrentMatchIndex((prev) => (prev + 1) % matches.length);
    }
  };

  const goToPreviousMatch = () => {
    if (matches.length > 0) {
      setCurrentMatchIndex((prev) => (prev - 1 + matches.length) % matches.length);
    }
  };

  return {
    query,
    matches,
    currentMatchIndex,
    currentMatch: matches[currentMatchIndex],
    totalMatches: matches.length,
    handleSearch,
    goToNextMatch,
    goToPreviousMatch
  };
};
```

**Modified Component**: `frontend/src/components/TerminalView.tsx`

```typescript
import { useTerminalSearch } from '../hooks/useTerminalSearch';
import { TerminalSearchBar } from './TerminalSearchBar';

export const TerminalView: React.FC<TerminalViewProps> = ({ workerId, terminalType }) => {
  // ... existing code ...

  const {
    query,
    matches,
    currentMatchIndex,
    currentMatch,
    totalMatches,
    handleSearch,
    goToNextMatch,
    goToPreviousMatch
  } = useTerminalSearch(lines);

  // Render line with highlighted matches
  const renderLine = (line: string, lineIndex: number) => {
    const lineMatches = matches.filter(m => m.lineIndex === lineIndex);

    if (lineMatches.length === 0) {
      return <span>{line}</span>;
    }

    // Build line with highlighted segments
    const segments: JSX.Element[] = [];
    let lastIndex = 0;

    lineMatches.forEach((match, i) => {
      // Text before match
      if (match.startIndex > lastIndex) {
        segments.push(
          <span key={`text-${i}`}>
            {line.substring(lastIndex, match.startIndex)}
          </span>
        );
      }

      // Highlighted match
      const isCurrent = matches[currentMatchIndex] === match;
      segments.push(
        <span
          key={`match-${i}`}
          className={isCurrent ? 'search-match-current' : 'search-match'}
        >
          {match.text}
        </span>
      );

      lastIndex = match.endIndex;
    });

    // Text after last match
    if (lastIndex < line.length) {
      segments.push(
        <span key="text-end">
          {line.substring(lastIndex)}
        </span>
      );
    }

    return <>{segments}</>;
  };

  // Auto-scroll to current match
  useEffect(() => {
    if (currentMatch) {
      const lineElement = document.querySelector(
        `[data-line-index="${currentMatch.lineIndex}"]`
      );
      lineElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [currentMatch]);

  return (
    <div className="terminal-view">
      <TerminalSearchBar
        onSearch={handleSearch}
        currentMatch={currentMatchIndex}
        totalMatches={totalMatches}
        onNext={goToNextMatch}
        onPrevious={goToPreviousMatch}
      />

      <div className="terminal-content">
        {lines.map((line, index) => (
          <div
            key={index}
            className="terminal-line"
            data-line-index={index}
          >
            {renderLine(line, index)}
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Styles**: `frontend/src/styles/TerminalSearch.css`

```css
.terminal-search-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: #2a2a2a;
  border-bottom: 1px solid #444;
}

.search-input {
  flex: 1;
  padding: 0.5rem;
  background: #1a1a1a;
  border: 1px solid #444;
  color: #00ff00;
  font-family: 'Courier New', monospace;
}

.search-input:focus {
  outline: none;
  border-color: #00ff00;
}

.match-navigation {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.match-count {
  color: #00ff00;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.search-match {
  background-color: #ffff00;
  color: #000;
  font-weight: bold;
}

.search-match-current {
  background-color: #ff9900;
  color: #000;
  font-weight: bold;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

---

## Implementation Timeline

### Week 1 (Days 1-3): Continuous Output Polling

**Day 1**: Implementation
- ✅ Add capture thread to `worker_manager.py`
- ✅ Implement `_start_output_capture_thread()`
- ✅ Implement graceful shutdown
- ✅ Integration with existing code

**Day 2**: Testing
- ✅ Write unit tests
- ✅ Run rapid output test
- ✅ Run long-running process test
- ✅ Verify thread cleanup

**Day 3**: Validation
- ✅ Multi-worker stress test
- ✅ Performance profiling
- ✅ Documentation update

### Week 1-2 (Days 4-8): Performance Metrics

**Day 4-5**: Backend Implementation
- ✅ Create `metrics_collector.py`
- ✅ Define metric schemas
- ✅ Implement collection methods
- ✅ Integrate into `worker_manager.py`

**Day 6**: API Implementation
- ✅ Create `metrics_api.py`
- ✅ Implement endpoints
- ✅ Register routes
- ✅ Test API

**Day 7-8**: Testing & Validation
- ✅ Unit tests for collector
- ✅ Integration test with real worker
- ✅ Verify JSONL format
- ✅ Documentation

### Week 2 (Days 9-12): Terminal Search

**Day 9-10**: Frontend Implementation
- ✅ Create `TerminalSearchBar` component
- ✅ Create `useTerminalSearch` hook
- ✅ Modify `TerminalView` for highlighting

**Day 11**: Styling & UX
- ✅ Add CSS for search UI
- ✅ Implement auto-scroll to match
- ✅ Test keyboard navigation

**Day 12**: Testing & Refinement
- ✅ Test with large terminal outputs
- ✅ Test regex patterns
- ✅ Performance optimization

### Week 2 (Day 13): Integration & Documentation

**Day 13**: Final Integration
- ✅ End-to-end testing of all features
- ✅ Update ROADMAP.md
- ✅ Create Phase 2.2 completion report
- ✅ User testing preparation

---

## Success Criteria

### Functional Requirements

- ✅ **Continuous Polling**: Output captured within 100ms, no gaps
- ✅ **Metrics Collection**: All metric types recorded correctly
- ✅ **Metrics API**: Endpoints return correct data
- ✅ **Terminal Search**: Finds all matches, highlights correctly
- ✅ **Search Navigation**: Next/Previous work smoothly
- ✅ **Auto-scroll**: Current match visible in viewport

### Non-Functional Requirements

- ✅ **Performance**: Search response < 100ms for 10,000 lines
- ✅ **Stability**: No crashes during long sessions
- ✅ **Resource Usage**: CPU < 5% when idle
- ✅ **Code Quality**: 80%+ test coverage
- ✅ **Documentation**: All features documented

### User Experience

- ✅ **Discoverability**: Search bar clearly visible
- ✅ **Responsiveness**: UI updates feel instant
- ✅ **Error Handling**: Invalid regex shows helpful message
- ✅ **Accessibility**: Keyboard shortcuts work

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Thread synchronization bugs | High | Low | Comprehensive testing, thread-safe writes |
| Search performance with large outputs | Medium | Medium | Debounce search, virtualize rendering |
| Regex injection vulnerabilities | Low | Low | Catch regex errors, no server-side eval |
| Memory leaks in metrics collector | Medium | Low | Limit JSONL file size, rotation |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Features take longer than estimated | Medium | Prioritize Tier 1, defer Tier 2 if needed |
| Testing reveals critical bugs | High | Allocate buffer days for fixes |
| Integration issues with Phase 1 | Low | Phase 1 already validated |

---

## Testing Strategy

### Unit Tests

**Files to Test**:
- `metrics_collector.py` (all methods)
- `useTerminalSearch.ts` (search logic)
- ANSI stripping (already tested)

**Coverage Target**: >80%

### Integration Tests

**Test Scenarios**:
1. End-to-end worker execution with metrics collection
2. Terminal search with real captured output
3. Multiple workers with continuous polling
4. API endpoints with actual metrics data

### Performance Tests

**Benchmarks**:
- Search 10,000 lines: < 100ms
- Metrics file write: < 1ms
- Capture thread CPU: < 1%
- Memory growth: < 10MB per hour

### User Acceptance Tests

**Scenarios**:
1. User runs worker, sees real-time output
2. User searches terminal, finds relevant logs
3. User views metrics dashboard
4. User runs multiple workers simultaneously

---

## Next Steps After Phase 2.2

### Phase 2.3 Features (Optional)

- Export functionality (JSON, HTML, PDF)
- ANSI-to-HTML conversion (colored terminal output)
- Multi-workspace support
- Session replay

### Phase 3 Planning

- Dynamic worker scaling
- Intelligent task distribution
- Failure recovery mechanisms
- Version control integration

---

## Notes

**User Feedback Integration**: This plan incorporates lessons from Phase 1:
- Visual verification first (search highlighting)
- Incremental implementation (one feature at a time)
- Comprehensive testing (no feature deployed untested)

**Professional Standards**:
- "Cathedral" approach: validate each feature before next
- Documentation-driven development
- User-centric design

**Go/No-Go Decision Points**:
1. After Feature 3: Verify continuous polling works before metrics
2. After Feature 2: Verify metrics collection before search UI
3. After Feature 1: Decide whether Phase 2.3 is needed

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Status**: Ready for Implementation
**Next Action**: Begin Feature 3 (Continuous Output Polling)
