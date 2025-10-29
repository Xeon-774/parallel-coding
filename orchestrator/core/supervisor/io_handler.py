"""Non - blocking process I / O handling.

Provides an async interface to stream output from `pexpect`/`wexpect`
children in a resource - efficient manner, with ANSI - stripping and line
buffering.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from orchestrator.utils.ansi_utils import strip_ansi

DEFAULT_CHUNK_SIZE = 1024
DEFAULT_POLL_INTERVAL = 0.02
MAX_BUFFER_SIZE = 1_000_000


@dataclass
class IOHandlerConfig:
    """Configuration for ProcessIOHandler.

    Attributes:
        chunk_size: Max bytes to read per iteration.
        poll_interval: Seconds to wait between polls when idle.
        max_buffer_size: Soft limit for internal buffer length.
    """

    chunk_size: int = DEFAULT_CHUNK_SIZE
    poll_interval: float = DEFAULT_POLL_INTERVAL
    max_buffer_size: int = MAX_BUFFER_SIZE


class ProcessIOHandler:
    """Async wrapper to stream output lines from an expect child.

    Usage:
        async with ProcessIOHandler(child) as io:
            async for line in io.read_async():
                ...
    """

    def __init__(self, child: object, config: Optional[IOHandlerConfig] = None) -> None:
        self._child = child
        self._config = config or IOHandlerConfig()
        self._buffer: str = ""
        self._closed = False

    async def __aenter__(self) -> "ProcessIOHandler":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the handler and cleanup internal state."""

        self._closed = True
        self._buffer = ""

    async def read_async(self) -> AsyncGenerator[str, None]:
        """Stream sanitized lines from the child process.

        Yields:
            Lines of output without ANSI sequences.
        """

        while not self._closed:
            if not self._isalive():
                # Flush any remaining buffered line
                if self._buffer:
                    line, self._buffer = self._buffer, ""
                    yield strip_ansi(line)
                break

            chunk = await self._read_chunk()
            if chunk:
                for line in self._parse_output(chunk):
                    yield strip_ansi(line)
                continue

            await asyncio.sleep(self._config.poll_interval)

    async def _read_chunk(self) -> str:
        """Read a small chunk from the child without blocking the loop."""

        def _read() -> str:
            try:
                # pexpect / wexpect share read_nonblocking
                data = self._child.read_nonblocking(size=self._config.chunk_size, timeout=0)  # type: ignore[attr-defined]
                return (
                    data.decode("utf - 8", errors="replace")
                    if isinstance(data, (bytes, bytearray))
                    else str(data)
                )
            except Exception:
                return ""

        return await asyncio.to_thread(_read)

    def _parse_output(self, data: str) -> list[str]:
        """Accumulate and split lines from stream data.

        Args:
            data: New chunk of decoded text.

        Returns:
            Completed lines ready to emit.
        """

        if not data:
            return []

        self._buffer += data
        if len(self._buffer) > self._config.max_buffer_size:
            # Keep last N chars to bound memory
            self._buffer = self._buffer[-self._config.max_buffer_size :]

        lines = self._buffer.splitlines(keepends=True)
        complete: list[str] = []

        for i, segment in enumerate(lines):
            if segment.endswith("\n") or segment.endswith("\r"):
                complete.append(segment.rstrip("\r\n"))
            else:
                # Remainder becomes the new buffer
                self._buffer = "".join(lines[i:])
                break
        else:
            # All lines ended with newline; clear buffer
            self._buffer = ""

        return complete

    def _isalive(self) -> bool:
        """Check if child is alive safely."""

        try:
            return bool(getattr(self._child, "isalive")())
        except Exception:
            return False
