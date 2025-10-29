"""
Stream monitoring module for real-time worker output

Handles real-time reading and monitoring of worker stdout/stderr streams
with proper encoding handling and concurrent file writing.
"""

import threading
from pathlib import Path
from typing import IO, List, Optional

from orchestrator.interfaces import ILogger


class StreamMonitor:
    """
    Real-time stream monitor for worker processes

    Monitors stdout/stderr streams in separate threads, writes to files,
    and optionally displays output in real-time.
    """

    def __init__(self, logger: ILogger, enable_realtime_display: bool = True):
        """
        Initialize stream monitor

        Args:
            logger: Logger instance for recording events
            enable_realtime_display: Whether to print output in real-time
        """
        self.logger = logger
        self.enable_realtime_display = enable_realtime_display
        self._active_monitors: List[threading.Thread] = []

    def monitor_stream(
        self,
        stream: IO[str],
        output_file: Path,
        lines_list: List[str],
        worker_id: str,
        stream_name: str,
    ) -> threading.Thread:
        """
        Start monitoring a stream in a separate thread

        Args:
            stream: Input stream to monitor (stdout or stderr)
            output_file: File path to write output
            lines_list: List to store read lines
            worker_id: Worker identifier
            stream_name: Stream type ("stdout" or "stderr")

        Returns:
            The monitoring thread (already started)
        """
        thread = threading.Thread(
            target=self._stream_reader,
            args=(stream, output_file, lines_list, worker_id, stream_name),
            daemon=True,
        )
        thread.start()
        self._active_monitors.append(thread)
        return thread

    def _stream_reader(
        self,
        stream: IO[str],
        output_file: Path,
        lines_list: List[str],
        worker_id: str,
        stream_name: str,
    ) -> None:
        """
        Read stream lines and write to file in real-time

        This method runs in a separate thread for each stream.

        Args:
            stream: Stream to read from
            output_file: Output file path
            lines_list: List to append read lines
            worker_id: Worker identifier
            stream_name: Stream type ("stdout" or "stderr")
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in stream:
                    # Append to memory list
                    lines_list.append(line)

                    # Write to file immediately
                    f.write(line)
                    f.flush()  # Force write to disk

                    # Display in real-time if enabled
                    if self.enable_realtime_display:
                        line_stripped = line.rstrip("\n\r")
                        if line_stripped:  # Skip empty lines
                            if stream_name == "stderr":
                                print(f"  [STDERR] {worker_id}: {line_stripped}")
                            else:
                                print(f"  [OUTPUT] {worker_id}: {line_stripped}")

                    # Log stderr output
                    if stream_name == "stderr" and line.strip():
                        self.logger.debug(f"Worker {worker_id} stderr", line=line.rstrip())
        except Exception as e:
            self.logger.error(f"Stream reader error for {worker_id} ({stream_name})", error=str(e))

    def wait_for_all(self, timeout: Optional[float] = None) -> None:
        """
        Wait for all monitoring threads to complete

        Args:
            timeout: Maximum time to wait (seconds), None for no limit
        """
        for thread in self._active_monitors:
            thread.join(timeout=timeout)

    def stop_all(self) -> None:
        """Stop all active stream monitors"""
        # Threads are daemon threads, so they will automatically stop
        # when the main thread exits. This method is here for completeness.
        self._active_monitors.clear()
