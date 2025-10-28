"""
Base window manager interface

Abstract base class defining the window management contract.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, TYPE_CHECKING, Any
from dataclasses import dataclass
import subprocess

if TYPE_CHECKING:
    from orchestrator.screenshot_manager import ScreenshotManager  # noqa: F401


@dataclass
class WindowInfo:
    """Information about a monitoring window"""

    worker_id: str
    task_name: str
    window_title: str
    batch_file: Optional[str] = None
    process: Optional["subprocess.Popen[Any]"] = None
    monitor_process: Optional["subprocess.Popen[Any]"] = None
    screenshot_path: Optional[str] = None


class WindowManagerBase(ABC):
    """
    Abstract base class for window management

    Defines the contract that all window manager implementations must follow.
    Uses the Strategy pattern to allow different implementations for different platforms.
    """

    def __init__(
        self,
        workspace_root: str,
        auto_close: bool = True,
        close_delay: int = 3,
        enable_screenshots: bool = True,
    ):
        """
        Initialize window manager

        Args:
            workspace_root: Root directory for workspace
            auto_close: Auto-close windows on completion
            close_delay: Delay before closing (seconds)
            enable_screenshots: Enable screenshot capture
        """
        self.workspace_root = Path(workspace_root)
        self.auto_close = auto_close
        self.close_delay = close_delay
        self.enable_screenshots = enable_screenshots
        self.windows: Dict[str, WindowInfo] = {}

        # Initialize screenshot manager if enabled
        self.screenshot_manager: Optional["ScreenshotManager"]
        if self.enable_screenshots:
            from orchestrator.screenshot_manager import ScreenshotManager

            self.screenshot_manager = ScreenshotManager(str(workspace_root))
        else:
            self.screenshot_manager = None

    @abstractmethod
    def create_monitoring_window(
        self, worker_id: str, task_name: str, output_file: str, error_file: Optional[str] = None
    ) -> WindowInfo:
        """
        Create a monitoring window for a worker

        Args:
            worker_id: Worker identifier
            task_name: Task name
            output_file: Output file path
            error_file: Error file path (optional)

        Returns:
            WindowInfo containing window details
        """
        pass

    @abstractmethod
    def close_window(self, worker_id: str) -> None:
        """
        Close a specific window

        Args:
            worker_id: Worker identifier
        """
        pass

    def close_all_windows(self) -> None:
        """Close all managed windows"""
        for worker_id in list(self.windows.keys()):
            try:
                self.close_window(worker_id)
            except Exception:
                pass  # Best effort cleanup

    def _capture_screenshot(
        self, worker_id: str, window_title: str, window_info: WindowInfo
    ) -> None:
        """
        Capture screenshot of window (common implementation)

        Args:
            worker_id: Worker identifier
            window_title: Window title for identification
            window_info: Window information to update
        """
        if not self.screenshot_manager:
            return

        try:
            print(f"[{worker_id}] Capturing window screenshot...")
            screenshot_path = self.screenshot_manager.capture_window(
                worker_id=worker_id,
                window_title=window_title,
                delay=3.0,  # Wait for window to fully open
            )
            if screenshot_path:
                window_info.screenshot_path = screenshot_path
                print(f"[{worker_id}] Screenshot saved: {screenshot_path}")
            else:
                print(f"[{worker_id}] Screenshot capture failed")
        except Exception as e:
            print(f"[{worker_id}] Screenshot error: {e}")

    def _sanitize_task_name(self, task_name: str, max_length: int = 50) -> str:
        """
        Sanitize task name for window title

        Args:
            task_name: Original task name
            max_length: Maximum length

        Returns:
            Sanitized task name
        """
        clean_name = task_name.replace("\n", " ").replace("\r", " ").strip()
        if len(clean_name) > max_length:
            clean_name = clean_name[: max_length - 3] + "..."
        return clean_name
