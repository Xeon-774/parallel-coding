"""Supervisor WebSocket endpoint and event hub.

Provides real - time streaming of supervisor output, status changes, and
confirmation prompts to connected dashboard clients.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Dict, Final, List, Literal, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

AUTH_TOKEN_ENV: Final[str] = "API_TOKEN"
DEFAULT_TOKEN: Final[str] = "dev - token"
MAX_MSGS_PER_SEC: Final[int] = 10
IDLE_TIMEOUT_SECS: Final[float] = 30.0
HEARTBEAT_INTERVAL_SECS: Final[float] = 10.0


def _expected_token() -> str:
    return os.environ.get(AUTH_TOKEN_ENV, DEFAULT_TOKEN)


def _auth_ok(token: Optional[str]) -> bool:
    return bool(token) and token == _expected_token()


EventType = Literal["output", "confirmation", "status", "error", "heartbeat"]


@dataclass
class Event:
    type: EventType
    data: dict


class RateLimiter:
    """Simple token bucket limiter."""

    def __init__(self, rate: int, per_seconds: float) -> None:
        self._capacity = max(1, rate)
        self._tokens = self._capacity
        self._per = per_seconds
        self._last = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        delta = now - self._last
        refill = int(delta * (self._capacity / self._per))
        if refill > 0:
            self._tokens = min(self._capacity, self._tokens + refill)
            self._last = now
        if self._tokens <= 0:
            return False
        self._tokens -= 1
        return True


class SupervisorHub:
    """Connection hub for supervisor events.

    Allows publishers (WorkerManager) to broadcast events to subscribers
    (dashboard clients) per supervisor id.
    """

    def __init__(self) -> None:
        self._subs: Dict[str, List[asyncio.Queue[Event]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, supervisor_id: str) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue(maxsize=1000)
        async with self._lock:
            self._subs.setdefault(supervisor_id, []).append(q)
        return q

    async def unsubscribe(self, supervisor_id: str, q: asyncio.Queue[Event]) -> None:
        async with self._lock:
            lst = self._subs.get(supervisor_id)
            if lst and q in lst:
                lst.remove(q)
                if not lst:
                    self._subs.pop(supervisor_id, None)

    async def publish(self, supervisor_id: str, event: Event) -> None:
        async with self._lock:
            for q in self._subs.get(supervisor_id, []):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop oldest to make room
                    try:
                        _ = q.get_nowait()
                    except Exception:
                        pass
                    try:
                        q.put_nowait(event)
                    except Exception:
                        pass


hub = SupervisorHub()
router = APIRouter()


@router.websocket("/ws / supervisor")
async def supervisor_ws(websocket: WebSocket) -> None:
    """WebSocket for real - time supervisor events.

    Auth via query param `token` or `Authorization: Bearer <token>` header.
    Requires `supervisorId` query string to scope subscription.
    """
    sup_id, token = _extract_auth_params(websocket)

    if not sup_id or not _auth_ok(token):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    rate = RateLimiter(rate=MAX_MSGS_PER_SEC, per_seconds=1.0)
    queue = await hub.subscribe(sup_id)

    hb_task = asyncio.create_task(_send_heartbeat_loop(websocket))

    try:
        await _handle_websocket_messages(websocket, queue, rate)
    finally:
        hb_task.cancel()
        await hub.unsubscribe(sup_id, queue)


def _extract_auth_params(websocket: WebSocket) -> tuple[str | None, str | None]:
    """Extract supervisor ID and auth token from WebSocket."""
    params = websocket.query_params
    sup_id = params.get("supervisorId")
    token = params.get("token")

    if not token:
        auth = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

    return sup_id, token


async def _send_heartbeat_loop(websocket: WebSocket) -> None:
    """Send periodic heartbeat messages."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECS)
        try:
            await websocket.send_json({"type": "heartbeat", "data": {"timestamp": time.time()}})
        except Exception:
            break


async def _handle_websocket_messages(
    websocket: WebSocket, queue: asyncio.Queue, rate: RateLimiter
) -> None:
    """Handle WebSocket message loop with idle timeout."""
    last_msg = time.monotonic()

    while True:
        if _check_idle_timeout(last_msg):
            await websocket.close(code=4408)
            break

        try:
            last_msg = await _process_message_or_event(websocket, queue, rate, last_msg)
        except WebSocketDisconnect:
            break
        except Exception:
            await websocket.send_json({"type": "error", "data": {"error": "internal"}})


def _check_idle_timeout(last_msg: float) -> bool:
    """Check if idle timeout exceeded."""
    return time.monotonic() - last_msg > IDLE_TIMEOUT_SECS


async def _process_message_or_event(
    websocket: WebSocket, queue: asyncio.Queue, rate: RateLimiter, last_msg: float
) -> float:
    """Process incoming message or queue event, return updated last_msg time."""
    recv_task = asyncio.create_task(websocket.receive_text())
    get_task = asyncio.create_task(queue.get())

    done, pending = await asyncio.wait(
        {recv_task, get_task}, timeout=1.0, return_when=asyncio.FIRST_COMPLETED
    )

    if recv_task in done:
        _ = recv_task.result()
        last_msg = time.monotonic()
    else:
        recv_task.cancel()

    if get_task in done:
        event = get_task.result()
        if rate.allow():
            await websocket.send_json({"type": event.type, "data": event.data})

    return last_msg


# Helper publish functions for other layers
async def publish_output(supervisor_id: str, content: str) -> None:
    await hub.publish(
        supervisor_id, Event("output", {"supervisorId": supervisor_id, "content": content})
    )


async def publish_status(supervisor_id: str, status: str) -> None:
    await hub.publish(
        supervisor_id, Event("status", {"supervisorId": supervisor_id, "status": status})
    )


async def publish_confirmation(supervisor_id: str, prompt: dict) -> None:
    await hub.publish(
        supervisor_id,
        Event("confirmation", {"supervisorId": supervisor_id, "prompt": prompt}),
    )
