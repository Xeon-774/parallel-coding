"""WebSocket endpoint for hierarchical event streaming.

Provides a connection manager with simple depth filtering, heartbeat, and
rate limiting per connection. Events are broadcast via a lightweight pub / sub
in this module suitable for unit testing without external brokers.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

router = APIRouter()


@dataclass
class _Conn:
    ws: WebSocket
    min_depth: int
    max_depth: int
    last_sent: float
    tokens: float
    last_refill: float


class _RateLimiter:
    def __init__(self, rate_per_sec: float = 20.0, burst: int = 10) -> None:
        self.rate = rate_per_sec
        self.capacity = burst

    def refill(self, conn: _Conn) -> None:
        now = time.time()
        delta = now - conn.last_refill
        conn.last_refill = now
        conn.tokens = min(self.capacity, conn.tokens + delta * self.rate)

    def allow(self, conn: _Conn) -> bool:
        self.refill(conn)
        if conn.tokens >= 1.0:
            conn.tokens -= 1.0
            return True
        return False


class EventBus:
    """Simple in - process pub / sub for events."""

    def __init__(self) -> None:
        self._connections: Set[_Conn] = set()
        self._lock = asyncio.Lock()
        self._limiter = _RateLimiter(rate_per_sec=15.0, burst=8)

    async def connect(self, ws: WebSocket, min_depth: int, max_depth: int) -> _Conn:
        await ws.accept(subprotocol="json")
        conn = _Conn(
            ws=ws,
            min_depth=min_depth,
            max_depth=max_depth,
            last_sent=0.0,
            tokens=8.0,
            last_refill=time.time(),
        )
        async with self._lock:
            self._connections.add(conn)
        return conn

    async def disconnect(self, conn: _Conn) -> None:
        async with self._lock:
            self._connections.discard(conn)
        try:
            await conn.ws.close(code=status.WS_1000_NORMAL_CLOSURE)
        except Exception:
            pass

    async def broadcast(self, event: Dict[str, Any]) -> None:
        depth = int(event.get("data", {}).get("depth", 0))
        payload = json.dumps(event)
        async with self._lock:
            conns = list(self._connections)
        for c in conns:
            if not (c.min_depth <= depth <= c.max_depth):
                continue
            if self._limiter.allow(c):
                try:
                    await c.ws.send_text(payload)
                    c.last_sent = time.time()
                except Exception:
                    # Drop broken connection
                    await self.disconnect(c)


bus = EventBus()


@router.websocket("/ws / recursion")
async def ws_recursion(ws: WebSocket) -> None:
    # Parse query params for depth filter, defaults wide open
    qp = ws.query_params
    try:
        min_depth = int(qp.get("min_depth", 0))
        max_depth = int(qp.get("max_depth", 5))
        heartbeat = float(qp.get("heartbeat", 15.0))
    except ValueError:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    conn = await bus.connect(ws, min_depth=min_depth, max_depth=max_depth)
    try:
        while True:
            # Heartbeat and receive with timeout
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=heartbeat)
                if msg == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                # Proactively send heartbeat
                try:
                    await ws.send_text("ping")
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await bus.disconnect(conn)


async def publish_event(event: Dict[str, Any]) -> None:
    """Publish an event to connected websocket clients.

    Expected format:
        {"type": "job_submitted", "data": {"jobId": "...", "depth": 1}}
    """
    await bus.broadcast(event)
