"""
Unit tests for dialogue WebSocket API

Tests DialogueFileMonitor, DialogueEntry, and ConnectionManager classes.

Coverage:
- DialogueEntry serialization
- DialogueFileMonitor initialization
- Historical entry retrieval
- New entry detection
- File modification handling
- Error handling (invalid JSON, missing files, etc.)
- ConnectionManager operations
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from typing import List

# Import with fallback for running from different contexts
try:
    from orchestrator.api.dialogue_ws import (
        DialogueEntry,
        DialogueFileMonitor,
        ConnectionManager
    )
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from orchestrator.api.dialogue_ws import (
        DialogueEntry,
        DialogueFileMonitor,
        ConnectionManager
    )


# ============================================================================
# DialogueEntry Tests
# ============================================================================

def test_dialogue_entry_creation():
    """DialogueEntry can be created with all fields."""
    entry = DialogueEntry(
        timestamp=1234567890.0,
        direction="worker→orchestrator",
        content="Test message",
        type="output",
        confirmation_type="bash",
        confirmation_message="Run ls?"
    )

    assert entry.timestamp == 1234567890.0
    assert entry.direction == "worker→orchestrator"
    assert entry.content == "Test message"
    assert entry.type == "output"
    assert entry.confirmation_type == "bash"
    assert entry.confirmation_message == "Run ls?"


def test_dialogue_entry_to_dict():
    """DialogueEntry.to_dict() returns proper dictionary."""
    entry = DialogueEntry(
        timestamp=1234567890.0,
        direction="orchestrator→worker",
        content="Approved",
        type="response",
        confirmation_type=None,
        confirmation_message=None
    )

    data = entry.to_dict()

    assert isinstance(data, dict)
    assert data['timestamp'] == 1234567890.0
    assert data['direction'] == "orchestrator→worker"
    assert data['content'] == "Approved"
    assert data['type'] == "response"
    assert data['confirmation_type'] is None
    assert data['confirmation_message'] is None


def test_dialogue_entry_minimal():
    """DialogueEntry works with minimal fields (optional fields are None)."""
    entry = DialogueEntry(
        timestamp=1234567890.0,
        direction="worker→orchestrator",
        content="Minimal",
        type="output"
    )

    data = entry.to_dict()
    assert data['confirmation_type'] is None
    assert data['confirmation_message'] is None


# ============================================================================
# DialogueFileMonitor Tests
# ============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "worker_001"
        workspace.mkdir()
        yield workspace


@pytest.fixture
def sample_entries():
    """Sample dialogue entries for testing."""
    return [
        {
            "timestamp": 1000.0,
            "direction": "worker→orchestrator",
            "content": "Running ls",
            "type": "output",
            "confirmation_type": "bash",
            "confirmation_message": "Run ls?"
        },
        {
            "timestamp": 1001.0,
            "direction": "orchestrator→worker",
            "content": "Approved",
            "type": "response",
            "confirmation_type": None,
            "confirmation_message": None
        },
        {
            "timestamp": 1002.0,
            "direction": "worker→orchestrator",
            "content": "file1.txt\nfile2.txt",
            "type": "output",
            "confirmation_type": None,
            "confirmation_message": None
        }
    ]


def test_dialogue_monitor_initialization(temp_workspace):
    """DialogueFileMonitor initializes correctly."""
    monitor = DialogueFileMonitor(temp_workspace)

    assert monitor.workspace == temp_workspace
    assert monitor.transcript_file == temp_workspace / "dialogue_transcript.jsonl"
    assert monitor._last_position == 0


def test_dialogue_monitor_with_existing_file(temp_workspace, sample_entries):
    """DialogueFileMonitor detects existing file and sets position."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Write sample entries
    with open(transcript, 'w', encoding='utf-8') as f:
        for entry in sample_entries:
            f.write(json.dumps(entry) + '\n')

    # Get file size
    initial_size = transcript.stat().st_size

    # Create monitor (should set position to end of file)
    monitor = DialogueFileMonitor(temp_workspace)

    assert monitor._last_position == initial_size


@pytest.mark.asyncio
async def test_get_historical_entries_empty(temp_workspace):
    """get_historical_entries returns empty list for non-existent file."""
    monitor = DialogueFileMonitor(temp_workspace)
    entries = await monitor.get_historical_entries()

    assert entries == []


@pytest.mark.asyncio
async def test_get_historical_entries_with_data(temp_workspace, sample_entries):
    """get_historical_entries returns all entries from file."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Write sample entries
    with open(transcript, 'w', encoding='utf-8') as f:
        for entry in sample_entries:
            f.write(json.dumps(entry) + '\n')

    monitor = DialogueFileMonitor(temp_workspace)
    entries = await monitor.get_historical_entries(limit=100)

    assert len(entries) == 3
    assert entries[0].timestamp == 1000.0
    assert entries[0].content == "Running ls"
    assert entries[1].direction == "orchestrator→worker"
    assert entries[2].content == "file1.txt\nfile2.txt"


@pytest.mark.asyncio
async def test_get_historical_entries_with_limit(temp_workspace, sample_entries):
    """get_historical_entries respects limit parameter."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Write sample entries
    with open(transcript, 'w', encoding='utf-8') as f:
        for entry in sample_entries:
            f.write(json.dumps(entry) + '\n')

    monitor = DialogueFileMonitor(temp_workspace)
    entries = await monitor.get_historical_entries(limit=2)

    # Should return last 2 entries
    assert len(entries) == 2
    assert entries[0].timestamp == 1001.0  # Second entry
    assert entries[1].timestamp == 1002.0  # Third entry


@pytest.mark.asyncio
async def test_read_new_entries(temp_workspace, sample_entries):
    """_read_new_entries detects and parses new entries."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Create monitor with empty file
    monitor = DialogueFileMonitor(temp_workspace)
    assert monitor._last_position == 0

    # Initialize async resources (normally done by watch())
    monitor._new_entries = asyncio.Queue()
    monitor._lock = asyncio.Lock()

    # Write entries
    with open(transcript, 'w', encoding='utf-8') as f:
        for entry in sample_entries:
            f.write(json.dumps(entry) + '\n')

    # Read new entries
    await monitor._read_new_entries()

    # Check that entries were queued
    assert monitor._new_entries.qsize() == 3

    # Verify entries
    entry1 = await monitor._new_entries.get()
    assert entry1.timestamp == 1000.0
    assert entry1.content == "Running ls"

    entry2 = await monitor._new_entries.get()
    assert entry2.direction == "orchestrator→worker"

    entry3 = await monitor._new_entries.get()
    assert entry3.content == "file1.txt\nfile2.txt"


@pytest.mark.asyncio
async def test_read_new_entries_incremental(temp_workspace):
    """_read_new_entries only reads new content (incremental)."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Write initial entry
    with open(transcript, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 1000.0, "direction": "test", "content": "initial", "type": "output"}) + '\n')

    # Create monitor (will set position to end)
    monitor = DialogueFileMonitor(temp_workspace)
    # Initialize async resources (normally done by watch())
    monitor._new_entries = asyncio.Queue()
    monitor._lock = asyncio.Lock()
    initial_position = monitor._last_position

    # Clear any queued entries from initialization
    while not monitor._new_entries.empty():
        await monitor._new_entries.get()

    # Append new entry
    with open(transcript, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 2000.0, "direction": "test", "content": "new", "type": "output"}) + '\n')

    # Read new entries
    await monitor._read_new_entries()

    # Should only have 1 new entry
    assert monitor._new_entries.qsize() == 1

    entry = await monitor._new_entries.get()
    assert entry.timestamp == 2000.0
    assert entry.content == "new"


@pytest.mark.asyncio
async def test_read_new_entries_handles_invalid_json(temp_workspace):
    """_read_new_entries skips invalid JSON lines."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Create monitor with empty file
    monitor = DialogueFileMonitor(temp_workspace)

    # Initialize async resources (normally done by watch())
    monitor._new_entries = asyncio.Queue()
    monitor._lock = asyncio.Lock()

    # Write mix of valid and invalid entries
    with open(transcript, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 1000.0, "direction": "test", "content": "valid1", "type": "output"}) + '\n')
        f.write('invalid json line\n')
        f.write(json.dumps({"timestamp": 2000.0, "direction": "test", "content": "valid2", "type": "output"}) + '\n')

    await monitor._read_new_entries()

    # Should have 2 valid entries (invalid skipped)
    assert monitor._new_entries.qsize() == 2

    entry1 = await monitor._new_entries.get()
    assert entry1.content == "valid1"

    entry2 = await monitor._new_entries.get()
    assert entry2.content == "valid2"


@pytest.mark.asyncio
async def test_read_new_entries_handles_file_truncation(temp_workspace):
    """_read_new_entries handles file truncation gracefully."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Write initial content
    with open(transcript, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 1000.0, "direction": "test", "content": "initial", "type": "output"}) + '\n')

    monitor = DialogueFileMonitor(temp_workspace)
    initial_position = monitor._last_position

    # Initialize async resources (normally done by watch())
    monitor._new_entries = asyncio.Queue()
    monitor._lock = asyncio.Lock()

    # Write shorter content (simulates file being replaced with smaller file)
    with open(transcript, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 2000.0, "direction": "test", "content": "new", "type": "output"}) + '\n')

    # Read new entries (should detect truncation and reset position)
    await monitor._read_new_entries()

    # Should have queued the new entry
    assert monitor._new_entries.qsize() == 1
    entry = await monitor._new_entries.get()
    assert entry.content == "new"


@pytest.mark.asyncio
async def test_read_new_entries_handles_empty_lines(temp_workspace):
    """_read_new_entries skips empty lines."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Create monitor with empty file
    monitor = DialogueFileMonitor(temp_workspace)

    # Initialize async resources (normally done by watch())
    monitor._new_entries = asyncio.Queue()
    monitor._lock = asyncio.Lock()

    # Write entries with empty lines
    with open(transcript, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 1000.0, "direction": "test", "content": "entry1", "type": "output"}) + '\n')
        f.write('\n')
        f.write('   \n')
        f.write(json.dumps({"timestamp": 2000.0, "direction": "test", "content": "entry2", "type": "output"}) + '\n')

    await monitor._read_new_entries()

    # Should have 2 entries (empty lines skipped)
    assert monitor._new_entries.qsize() == 2


# ============================================================================
# ConnectionManager Tests
# ============================================================================

class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.sent_messages = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.sent_messages.append(data)

    async def close(self, code=None, reason=None):
        self.closed = True


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """ConnectionManager registers new connections."""
    manager = ConnectionManager()
    ws = MockWebSocket()

    await manager.connect("worker_001", ws)

    assert ws.accepted
    assert "worker_001" in manager.active_connections
    assert ws in manager.active_connections["worker_001"]


@pytest.mark.asyncio
async def test_connection_manager_multiple_connections():
    """ConnectionManager handles multiple connections for same worker."""
    manager = ConnectionManager()
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect("worker_001", ws1)
    await manager.connect("worker_001", ws2)

    assert len(manager.active_connections["worker_001"]) == 2
    assert ws1 in manager.active_connections["worker_001"]
    assert ws2 in manager.active_connections["worker_001"]


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """ConnectionManager unregisters connections."""
    manager = ConnectionManager()
    ws = MockWebSocket()

    await manager.connect("worker_001", ws)
    await manager.disconnect("worker_001", ws)

    assert "worker_001" not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_send_to_worker_clients():
    """ConnectionManager sends messages to all worker clients."""
    manager = ConnectionManager()
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect("worker_001", ws1)
    await manager.connect("worker_001", ws2)

    message = {"type": "test", "data": "hello"}
    await manager.send_to_worker_clients("worker_001", message)

    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert ws1.sent_messages[0] == message
    assert ws2.sent_messages[0] == message


@pytest.mark.asyncio
async def test_connection_manager_handles_send_errors():
    """ConnectionManager removes disconnected clients on send errors."""
    manager = ConnectionManager()

    # Create mock that fails on send
    class FailingWebSocket(MockWebSocket):
        async def send_json(self, data):
            raise Exception("Connection lost")

    ws_failing = FailingWebSocket()
    ws_working = MockWebSocket()

    await manager.connect("worker_001", ws_failing)
    await manager.connect("worker_001", ws_working)

    message = {"type": "test", "data": "hello"}
    await manager.send_to_worker_clients("worker_001", message)

    # Failing connection should be removed
    assert ws_failing not in manager.active_connections["worker_001"]
    # Working connection should remain
    assert ws_working in manager.active_connections["worker_001"]
    # Working connection should have received message
    assert len(ws_working.sent_messages) == 1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_monitor_watch_with_pre_existing_entries(temp_workspace):
    """Integration test: Reading entries after file is written."""
    transcript = temp_workspace / "dialogue_transcript.jsonl"

    # Create monitor with no file yet
    monitor = DialogueFileMonitor(temp_workspace)

    # Initialize async resources (normally done by watch())
    monitor._new_entries = asyncio.Queue()
    monitor._lock = asyncio.Lock()

    # Write entries after creating monitor
    with open(transcript, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": 1000.0, "direction": "test", "content": "entry1", "type": "output"}) + '\n')
        f.write(json.dumps({"timestamp": 2000.0, "direction": "test", "content": "entry2", "type": "output"}) + '\n')

    # Manually trigger reading (simulating what watch() does)
    await monitor._read_new_entries()

    # Verify entries were queued
    assert monitor._new_entries.qsize() == 2

    entry1 = await monitor._new_entries.get()
    assert entry1.content == "entry1"

    entry2 = await monitor._new_entries.get()
    assert entry2.content == "entry2"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
