"""
Window manager facade (Refactored v6.0)

This module provides a simple facade to the window management strategies.
The actual implementations are in orchestrator/window_strategies/.

This maintains backwards compatibility while using the Strategy pattern internally.
"""

from typing import Optional, Any
from orchestrator.window_strategies import WindowManagerFactory, WindowManagerBase, WindowInfo

# Re-export for backwards compatibility
__all__ = ["WindowManager", "WindowInfo"]


class WindowManager:
    """
    Window manager facade

    This class provides backwards-compatible interface while delegating
    to platform-specific strategies internally.

    Refactored in v6.0 to use Strategy pattern for better separation of concerns.
    """

    def __init__(
        self,
        workspace_root: str,
        execution_mode: str = "windows",
        auto_close: bool = True,
        close_delay: int = 3,
        enable_screenshots: bool = True,
    ):
        """
        Initialize window manager

        Args:
            workspace_root: Workspace root directory
            execution_mode: Execution mode ("windows" or "wsl")
            auto_close: Auto-close windows on completion
            close_delay: Delay before closing (seconds)
            enable_screenshots: Enable screenshot capture
        """
        # Delegate to appropriate strategy via factory
        self._strategy: WindowManagerBase = WindowManagerFactory.create(
            execution_mode=execution_mode,
            workspace_root=workspace_root,
            auto_close=auto_close,
            close_delay=close_delay,
            enable_screenshots=enable_screenshots,
        )

    def create_monitoring_window(
        self, worker_id: str, task_name: str, output_file: str, error_file: Optional[str] = None
    ) -> WindowInfo:
        """
        Create monitoring window (delegates to strategy)

        Args:
            worker_id: Worker identifier
            task_name: Task name
            output_file: Output file path
            error_file: Error file path (optional)

        Returns:
            WindowInfo
        """
        return self._strategy.create_monitoring_window(
            worker_id=worker_id, task_name=task_name, output_file=output_file, error_file=error_file
        )

    def close_window(self, worker_id: str) -> None:
        """Close a specific window (delegates to strategy)"""
        self._strategy.close_window(worker_id)

    def close_all_windows(self) -> None:
        """Close all windows (delegates to strategy)"""
        self._strategy.close_all_windows()

    @property
    def windows(self) -> Any:
        """Get managed windows (delegates to strategy)"""
        return self._strategy.windows
