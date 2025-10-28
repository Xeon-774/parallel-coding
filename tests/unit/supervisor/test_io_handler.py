import asyncio
import types

import pytest

from orchestrator.core.supervisor.io_handler import IOHandlerConfig, ProcessIOHandler


class FakeChild:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self._alive = True

    def read_nonblocking(self, size=1024, timeout=0):  # noqa: ARG002
        if not self._chunks:
            self._alive = False
            raise Exception("empty")
        return self._chunks.pop(0)

    def isalive(self):
        return self._alive


@pytest.mark.asyncio
async def test_read_async_yields_lines():
    chunks = [b"hello\nwor", b"ld\nlast\n"]
    child = FakeChild(chunks)
    io = ProcessIOHandler(child, IOHandlerConfig(chunk_size=16, poll_interval=0.001))

    out = []
    async for line in io.read_async():
        out.append(line)

    assert out == ["hello", "world", "last"]


@pytest.mark.asyncio
async def test_read_async_strips_ansi():
    chunks = ["\x1b[31mError\x1b[0m\n".encode()]
    child = FakeChild(chunks)
    io = ProcessIOHandler(child)
    lines = [line async for line in io.read_async()]
    assert lines == ["Error"]


@pytest.mark.asyncio
async def test_close_stops_stream():
    class SlowChild(FakeChild):
        def read_nonblocking(self, size=1024, timeout=0):  # noqa: ARG002
            return b"partial"

    child = SlowChild([b"partial"] * 10)
    io = ProcessIOHandler(child, IOHandlerConfig(poll_interval=0.001))
    task = asyncio.create_task(_collect(io))
    await asyncio.sleep(0.01)
    await io.close()
    await asyncio.wait_for(task, 1)
    # No assertion needed; just ensure no hang


async def _collect(io):
    async for _ in io.read_async():
        await asyncio.sleep(0)

