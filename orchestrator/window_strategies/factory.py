"""
Window manager factory

Creates appropriate window manager based on execution mode.
"""

from orchestrator.window_strategies.base import WindowManagerBase
from orchestrator.window_strategies.windows_strategy import WindowsWindowManager
from orchestrator.window_strategies.wsl_strategy import WSLWindowManager


class WindowManagerFactory:
    """
    Factory for creating platform-specific window managers

    Uses the Factory pattern to instantiate the correct window manager
    implementation based on the execution mode.
    """

    @staticmethod
    def create(
        execution_mode: str,
        workspace_root: str,
        auto_close: bool = True,
        close_delay: int = 3,
        enable_screenshots: bool = True,
    ) -> WindowManagerBase:
        """
        Create appropriate window manager for the execution mode

        Args:
            execution_mode: Either "windows" or "wsl"
            workspace_root: Workspace root directory
            auto_close: Auto-close windows on completion
            close_delay: Delay before closing
            enable_screenshots: Enable screenshot capture

        Returns:
            WindowManagerBase instance (either Windows or WSL implementation)

        Raises:
            ValueError: If execution_mode is not supported
        """
        if execution_mode.lower() == "windows":
            return WindowsWindowManager(
                workspace_root=workspace_root,
                auto_close=auto_close,
                close_delay=close_delay,
                enable_screenshots=enable_screenshots,
            )
        elif execution_mode.lower() == "wsl":
            return WSLWindowManager(
                workspace_root=workspace_root,
                auto_close=auto_close,
                close_delay=close_delay,
                enable_screenshots=enable_screenshots,
            )
        else:
            raise ValueError(
                f"Unsupported execution mode: {execution_mode}. "
                f"Supported modes: 'windows', 'wsl'"
            )
