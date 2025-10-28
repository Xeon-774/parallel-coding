"""
Raw Terminal WebSocket Streaming

Provides WebSocket endpoint to stream raw terminal output from worker processes.
Similar to dialogue_ws.py but streams the raw terminal log file.

Features:
- Real-time streaming of raw terminal output
- File monitoring with watchdog
- WebSocket communication
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncIterator, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


class TerminalFileMonitor(FileSystemEventHandler):
    """
    Monitors raw_terminal.log file for changes and streams new content via WebSocket
    """

    def __init__(
        self,
        workspace: Path,
        terminal_file: Optional[Path] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        Initialize terminal file monitor

        Args:
            workspace: Worker workspace directory
            terminal_file: Specific terminal file to monitor (defaults to raw_terminal.log)
            loop: Event loop for thread-safe async operations
        """
        super().__init__()
        self.workspace = workspace
        self.terminal_file = terminal_file if terminal_file else workspace / "raw_terminal.log"
        self._last_position = 0
        self._new_lines: Optional[asyncio.Queue] = None
        self._lock: Optional[asyncio.Lock] = None
        self._observer: Optional[Observer] = None
        self._loop = loop

        logger.info(f"TerminalFileMonitor initialized for {workspace}")

    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Called when terminal file is modified

        Args:
            event: File modification event
        """
        if not event.is_directory and event.src_path == str(self.terminal_file):
            # Schedule async task in the event loop (thread-safe)
            if self._loop and self._new_lines is not None:
                asyncio.run_coroutine_threadsafe(self._read_new_lines(), self._loop)

    async def _read_new_lines(self) -> None:
        """
        Read new lines from terminal file (incremental read)
        """
        if not self.terminal_file.exists():
            return

        try:
            async with self._lock:
                with open(self.terminal_file, "r", encoding="utf-8", errors="replace") as f:
                    # Seek to last position
                    f.seek(self._last_position)

                    # Read new lines
                    new_content = f.read()
                    if new_content:
                        # Split into lines but keep partial line at end
                        lines = new_content.split("\n")

                        # If file doesn't end with newline, keep last partial line for next read
                        if new_content.endswith("\n"):
                            for line in lines[:-1]:  # Skip empty last element
                                if line:
                                    await self._new_lines.put(line)
                        else:
                            # Process all complete lines
                            for line in lines[:-1]:
                                if line:
                                    await self._new_lines.put(line)
                            # Don't advance position past partial line
                            # (will re-read partial line next time)

                    # Update position
                    self._last_position = f.tell()

        except Exception as e:
            logger.error(f"Error reading new lines from terminal file: {e}")

    async def watch(self) -> AsyncIterator[str]:
        """
        Watch terminal file for changes and yield new lines

        Yields:
            New terminal output lines as they are written
        """
        # Initialize async resources in the event loop
        self._loop = asyncio.get_running_loop()
        self._new_lines = asyncio.Queue()
        self._lock = asyncio.Lock()

        # Read historical lines first
        if self.terminal_file.exists():
            logger.info(f"Reading historical terminal output from {self.terminal_file}")

            try:
                with open(self.terminal_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line:
                            yield line

                    self._last_position = f.tell()

            except Exception as e:
                logger.error(f"Error reading historical terminal output: {e}")

        # Start file watcher
        self._observer = Observer()
        self._observer.schedule(self, str(self.workspace), recursive=False)
        self._observer.start()

        logger.info(f"Started watching terminal file: {self.terminal_file}")

        try:
            # Yield new lines as they arrive
            while True:
                try:
                    line = await asyncio.wait_for(self._new_lines.get(), timeout=30.0)
                    yield line
                except asyncio.TimeoutError:
                    # No new lines for 30 seconds, yield keepalive
                    continue

        finally:
            # Cleanup
            if self._observer:
                self._observer.stop()
                self._observer.join()
                logger.info("Stopped terminal file observer")

    async def stop(self) -> None:
        """Stop monitoring"""
        if self._observer:
            self._observer.stop()
            self._observer.join()


async def terminal_websocket_endpoint(
    websocket,  # FastAPI WebSocket
    worker_id: str,
    workspace_root: str = "workspace",
    terminal_type: str = "worker",
) -> None:
    """
    WebSocket endpoint for streaming raw terminal output.

    This endpoint accepts WebSocket connections and streams terminal
    output lines for the specified worker in real-time.

    Args:
        websocket: FastAPI WebSocket connection
        worker_id: Worker identifier (e.g., "worker_001")
        workspace_root: Root workspace directory
        terminal_type: Type of terminal to stream ("worker" or "orchestrator")

    Raises:
        WebSocketDisconnect: Client disconnected

    Usage:
        # In FastAPI app:
        @app.websocket("/ws/terminal/{worker_id}")
        async def terminal_ws(websocket: WebSocket, worker_id: str, terminal_type: str = "worker"):
            await terminal_websocket_endpoint(websocket, worker_id, terminal_type=terminal_type)
    """
    from fastapi import WebSocketDisconnect
    from starlette import status

    # Accept connection
    await websocket.accept()
    logger.info(f"New terminal connection for worker {worker_id}")

    try:
        # Construct workspace path
        workspace = Path(workspace_root) / worker_id

        if not workspace.exists():
            await websocket.send_json({"type": "error", "message": f"Worker {worker_id} not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Worker not found")
            return

        # Determine which terminal file to stream based on type
        if terminal_type == "orchestrator":
            terminal_file = workspace / "orchestrator_terminal.log"
        else:
            terminal_file = workspace / "raw_terminal.log"

        if not terminal_file.exists():
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"{terminal_type.capitalize()} terminal output file not found for worker {worker_id}",
                }
            )
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Terminal file not found"
            )
            return

        # Create monitor
        monitor = TerminalFileMonitor(workspace, terminal_file=terminal_file)

        # Send ready signal
        await websocket.send_json(
            {
                "type": "ready",
                "worker_id": worker_id,
                "terminal_type": terminal_type,
                "message": f"{terminal_type.capitalize()} terminal stream ready for {worker_id}",
            }
        )

        # Stream terminal lines
        async for line in monitor.watch():
            await websocket.send_json({"type": "line", "worker_id": worker_id, "content": line})

    except WebSocketDisconnect:
        logger.info(f"Terminal client disconnected from {worker_id}")

    except Exception as e:
        logger.error(f"Error in terminal WebSocket: {e}")
        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
            )
        except:
            pass

    finally:
        await websocket.close()
        logger.info(f"Terminal connection closed for {worker_id}")
