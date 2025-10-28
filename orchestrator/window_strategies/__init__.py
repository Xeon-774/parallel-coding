"""
Window management strategies

This package contains platform-specific implementations of window management
following the Strategy design pattern.
"""

from orchestrator.window_strategies.base import WindowManagerBase, WindowInfo
from orchestrator.window_strategies.windows_strategy import WindowsWindowManager
from orchestrator.window_strategies.wsl_strategy import WSLWindowManager
from orchestrator.window_strategies.factory import WindowManagerFactory

__all__ = [
    "WindowManagerBase",
    "WindowInfo",
    "WindowsWindowManager",
    "WSLWindowManager",
    "WindowManagerFactory",
]
