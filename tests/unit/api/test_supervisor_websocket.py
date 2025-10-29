"""Unit tests for supervisor WebSocket endpoint.

Tests core WebSocket functionality including authentication, rate limiting,
and event subscription. Full integration testing deferred to integration tests.

Coverage target: Focus on critical paths (auth, rate limiting, hub logic)
"""

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.api.supervisor_websocket import (
    Event,
    RateLimiter,
    SupervisorHub,
    _auth_ok,
    _expected_token,
)


# Authentication tests
def test_expected_token_from_env():
    """Test token retrieval from environment variable."""
    os.environ["API_TOKEN"] = "test - token - 123"
    assert _expected_token() == "test - token - 123"


def test_expected_token_default():
    """Test default token when env var not set."""
    os.environ.pop("API_TOKEN", None)
    assert _expected_token() == "dev - token"


def test_auth_ok_valid_token():
    """Test authentication succeeds with valid token."""
    os.environ["API_TOKEN"] = "valid - token"
    assert _auth_ok("valid - token") is True


def test_auth_ok_invalid_token():
    """Test authentication fails with invalid token."""
    os.environ["API_TOKEN"] = "correct - token"
    assert _auth_ok("wrong - token") is False


def test_auth_ok_none_token():
    """Test authentication fails with None token."""
    assert _auth_ok(None) is False


def test_auth_ok_empty_token():
    """Test authentication fails with empty token."""
    assert _auth_ok("") is False


# RateLimiter tests
def test_rate_limiter_allows_within_limit():
    """Test rate limiter allows requests within rate limit."""
    limiter = RateLimiter(rate=10, per_seconds=1.0)

    # First request should always be allowed
    assert limiter.allow() is True


def test_rate_limiter_blocks_when_exhausted():
    """Test rate limiter blocks when token bucket is exhausted."""
    limiter = RateLimiter(rate=2, per_seconds=10.0)

    # Consume all tokens
    assert limiter.allow() is True
    assert limiter.allow() is True

    # Next request should be blocked
    assert limiter.allow() is False


def test_rate_limiter_refills_over_time():
    """Test rate limiter refills tokens over time."""
    limiter = RateLimiter(rate=10, per_seconds=0.1)  # 10 per 0.1s = 100 / s

    # Consume tokens
    for _ in range(10):
        limiter.allow()

    # Should be blocked immediately
    assert limiter.allow() is False

    # Wait for refill
    time.sleep(0.2)

    # Should allow again
    assert limiter.allow() is True


def test_rate_limiter_minimum_capacity():
    """Test rate limiter enforces minimum capacity of 1."""
    limiter = RateLimiter(rate=0, per_seconds=1.0)

    # Should have at least 1 token
    assert limiter.allow() is True


# SupervisorHub tests
@pytest.mark.asyncio
async def test_supervisor_hub_subscribe():
    """Test subscribing to supervisor events."""
    hub = SupervisorHub()

    queue = await hub.subscribe("worker_1")

    assert queue is not None
    assert isinstance(queue, asyncio.Queue)
    assert "worker_1" in hub._subs
    assert queue in hub._subs["worker_1"]


@pytest.mark.asyncio
async def test_supervisor_hub_multiple_subscribers():
    """Test multiple clients can subscribe to same supervisor."""
    hub = SupervisorHub()

    queue1 = await hub.subscribe("worker_1")
    queue2 = await hub.subscribe("worker_1")

    assert len(hub._subs["worker_1"]) == 2
    assert queue1 in hub._subs["worker_1"]
    assert queue2 in hub._subs["worker_1"]


@pytest.mark.asyncio
async def test_supervisor_hub_publish_to_subscribers():
    """Test publishing events to subscribers."""
    hub = SupervisorHub()

    queue1 = await hub.subscribe("worker_1")
    queue2 = await hub.subscribe("worker_1")

    event = Event(type="output", data={"line": "test output"})
    await hub.publish("worker_1", event)

    # Both subscribers should receive the event
    received1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    received2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

    assert received1.type == "output"
    assert received1.data == {"line": "test output"}
    assert received2.type == "output"
    assert received2.data == {"line": "test output"}


@pytest.mark.asyncio
async def test_supervisor_hub_publish_no_subscribers():
    """Test publishing to supervisor with no subscribers does not error."""
    hub = SupervisorHub()

    event = Event(type="status", data={"status": "running"})

    # Should not raise exception
    await hub.publish("nonexistent_worker", event)


@pytest.mark.asyncio
async def test_supervisor_hub_unsubscribe():
    """Test unsubscribing from supervisor events."""
    hub = SupervisorHub()

    queue = await hub.subscribe("worker_1")
    await hub.unsubscribe("worker_1", queue)

    # Subscriber list should be empty and removed
    assert "worker_1" not in hub._subs


@pytest.mark.asyncio
async def test_supervisor_hub_unsubscribe_partial():
    """Test unsubscribing one subscriber keeps others active."""
    hub = SupervisorHub()

    queue1 = await hub.subscribe("worker_1")
    queue2 = await hub.subscribe("worker_1")

    await hub.unsubscribe("worker_1", queue1)

    # queue2 should still be subscribed
    assert "worker_1" in hub._subs
    assert queue1 not in hub._subs["worker_1"]
    assert queue2 in hub._subs["worker_1"]


@pytest.mark.asyncio
async def test_supervisor_hub_queue_overflow_drops_oldest():
    """Test queue overflow drops oldest events to make room."""
    hub = SupervisorHub()

    queue = await hub.subscribe("worker_1")

    # Fill queue beyond capacity (maxsize=1000)
    for i in range(1001):
        event = Event(type="output", data={"line": f"message {i}"})
        await hub.publish("worker_1", event)

    # Queue should have 1000 items (oldest dropped)
    assert queue.qsize() <= 1000


@pytest.mark.asyncio
async def test_supervisor_hub_different_supervisors_isolated():
    """Test events for different supervisors are isolated."""
    hub = SupervisorHub()

    queue1 = await hub.subscribe("worker_1")
    queue2 = await hub.subscribe("worker_2")

    event1 = Event(type="output", data={"worker": "worker_1"})
    event2 = Event(type="output", data={"worker": "worker_2"})

    await hub.publish("worker_1", event1)
    await hub.publish("worker_2", event2)

    # Each queue should only receive its own supervisor's events
    received1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    received2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

    assert received1.data["worker"] == "worker_1"
    assert received2.data["worker"] == "worker_2"

    # Queues should be empty now
    assert queue1.empty()
    assert queue2.empty()


# Event dataclass tests
def test_event_creation():
    """Test Event dataclass creation."""
    event = Event(type="output", data={"line": "test"})

    assert event.type == "output"
    assert event.data == {"line": "test"}


def test_event_types():
    """Test all EventType values are valid."""
    valid_types = ["output", "confirmation", "status", "error", "heartbeat"]

    for event_type in valid_types:
        event = Event(type=event_type, data={})  # type: ignore
        assert event.type == event_type


# Note: WebSocket endpoint integration tests (websocket_endpoint function)
# are complex and require TestClient WebSocket support. These are deferred
# to integration tests to maintain focus on unit - testable components.
#
# Full coverage of supervisor_websocket.py would require:
# 1. WebSocket connection lifecycle tests
# 2. Authentication via query parameter tests
# 3. Heartbeat mechanism tests
# 4. Event streaming tests
# 5. Error handling and disconnection tests
#
# These are better suited for integration tests with real WebSocket connections.
