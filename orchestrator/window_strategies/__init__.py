"""
Window management strategies

This package contains platform - specific implementations of window management
following the Strategy design pattern.
"""

from orchestrator.window_strategies.base import WindowInfo, WindowManagerBase
from orchestrator.window_strategies.factory import WindowManagerFactory
from orchestrator.window_strategies.windows_strategy import WindowsWindowManager
from orchestrator.window_strategies.wsl_strategy import WSLWindowManager

__all__ = [
    "WindowManagerBase",
    "WindowInfo",
    "WindowsWindowManager",
    "WSLWindowManager",
    "WindowManagerFactory",
]
