"""Unit tests for WindowManager facade and WindowManagerFactory.

Tests facade pattern delegation and factory pattern creation.
"""

import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from orchestrator.window_manager import WindowManager
from orchestrator.window_strategies.base import WindowInfo, WindowManagerBase
from orchestrator.window_strategies.factory import WindowManagerFactory

# ======================= WindowManagerFactory Tests =======================


class TestWindowManagerFactory:
    """Test WindowManagerFactory pattern."""

    def test_create_windows_manager(self):
        """Test creating Windows window manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = WindowManagerFactory.create(
                execution_mode="windows",
                workspace_root=tmpdir,
                auto_close=True,
                close_delay=3,
                enable_screenshots=False,
            )

            assert manager is not None
            assert isinstance(manager, WindowManagerBase)

    def test_create_wsl_manager(self):
        """Test creating WSL window manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = WindowManagerFactory.create(
                execution_mode="wsl",
                workspace_root=tmpdir,
                auto_close=False,
                close_delay=5,
                enable_screenshots=False,
            )

            assert manager is not None
            assert isinstance(manager, WindowManagerBase)

    def test_create_case_insensitive_windows(self):
        """Test that execution_mode is case insensitive for windows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = WindowManagerFactory.create("WINDOWS", tmpdir, enable_screenshots=False)
            manager2 = WindowManagerFactory.create("Windows", tmpdir, enable_screenshots=False)
            manager3 = WindowManagerFactory.create("windows", tmpdir, enable_screenshots=False)

            assert all(isinstance(m, WindowManagerBase) for m in [manager1, manager2, manager3])

    def test_create_case_insensitive_wsl(self):
        """Test that execution_mode is case insensitive for wsl."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = WindowManagerFactory.create("WSL", tmpdir, enable_screenshots=False)
            manager2 = WindowManagerFactory.create("Wsl", tmpdir, enable_screenshots=False)
            manager3 = WindowManagerFactory.create("wsl", tmpdir, enable_screenshots=False)

            assert all(isinstance(m, WindowManagerBase) for m in [manager1, manager2, manager3])

    def test_create_invalid_execution_mode_raises_error(self):
        """Test that invalid execution_mode raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Unsupported execution mode: invalid"):
                WindowManagerFactory.create("invalid", tmpdir)

    def test_create_error_message_includes_supported_modes(self):
        """Test that error message includes supported modes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Supported modes: 'windows', 'wsl'"):
                WindowManagerFactory.create("macos", tmpdir)

    def test_create_with_all_parameters(self):
        """Test creating manager with all parameters specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = WindowManagerFactory.create(
                execution_mode="windows",
                workspace_root=tmpdir,
                auto_close=False,
                close_delay=10,
                enable_screenshots=False,
            )

            assert manager is not None


# ======================= WindowManager Facade Tests =======================


class TestWindowManagerFacade:
    """Test WindowManager facade pattern."""

    def test_init_default_execution_mode(self):
        """Test WindowManager initialization with default execution mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            assert wm is not None
            assert hasattr(wm, "_strategy")
            assert isinstance(wm._strategy, WindowManagerBase)

    def test_init_windows_mode(self):
        """Test WindowManager initialization with Windows mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(
                workspace_root=tmpdir,
                execution_mode="windows",
                enable_screenshots=False,
            )

            assert wm._strategy is not None

    def test_init_wsl_mode(self):
        """Test WindowManager initialization with WSL mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(
                workspace_root=tmpdir,
                execution_mode="wsl",
                enable_screenshots=False,
            )

            assert wm._strategy is not None

    def test_init_with_all_parameters(self):
        """Test WindowManager initialization with all parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(
                workspace_root=tmpdir,
                execution_mode="windows",
                auto_close=False,
                close_delay=5,
                enable_screenshots=False,
            )

            assert wm._strategy is not None

    def test_create_monitoring_window_delegates_to_strategy(self):
        """Test that create_monitoring_window delegates to strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            # Mock the strategy
            mock_window_info = WindowInfo(
                worker_id="w123",
                task_name="test_task",
                window_title="Test Window",
            )
            wm._strategy.create_monitoring_window = Mock(return_value=mock_window_info)

            # Call the facade method
            result = wm.create_monitoring_window(
                worker_id="w123",
                task_name="test_task",
                output_file="/tmp/output.txt",
                error_file="/tmp/error.txt",
            )

            # Verify delegation
            wm._strategy.create_monitoring_window.assert_called_once_with(
                worker_id="w123",
                task_name="test_task",
                output_file="/tmp/output.txt",
                error_file="/tmp/error.txt",
            )
            assert result == mock_window_info

    def test_close_window_delegates_to_strategy(self):
        """Test that close_window delegates to strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            # Mock the strategy
            wm._strategy.close_window = Mock()

            # Call the facade method
            wm.close_window("w123")

            # Verify delegation
            wm._strategy.close_window.assert_called_once_with("w123")

    def test_close_all_windows_delegates_to_strategy(self):
        """Test that close_all_windows delegates to strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            # Mock the strategy
            wm._strategy.close_all_windows = Mock()

            # Call the facade method
            wm.close_all_windows()

            # Verify delegation
            wm._strategy.close_all_windows.assert_called_once()

    def test_windows_property_delegates_to_strategy(self):
        """Test that windows property delegates to strategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            # Mock the strategy windows property
            mock_windows = {"w123": Mock()}
            wm._strategy.windows = mock_windows

            # Access the property
            result = wm.windows

            # Verify delegation
            assert result == mock_windows

    def test_facade_pattern_complete_workflow(self):
        """Test complete workflow through facade pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create facade
            wm = WindowManager(
                workspace_root=tmpdir,
                execution_mode="windows",
                auto_close=True,
                close_delay=3,
                enable_screenshots=False,
            )

            # Mock all strategy methods
            mock_window_info = WindowInfo(
                worker_id="w456",
                task_name="build",
                window_title="Task Window",
            )
            wm._strategy.create_monitoring_window = Mock(return_value=mock_window_info)
            wm._strategy.close_window = Mock()
            wm._strategy.close_all_windows = Mock()

            # Execute workflow
            window = wm.create_monitoring_window("w456", "build", "/tmp/out.txt")
            assert window.worker_id == "w456"

            wm.close_window("w456")
            wm.close_all_windows()

            # Verify all delegations occurred
            assert wm._strategy.create_monitoring_window.call_count == 1
            assert wm._strategy.close_window.call_count == 1
            assert wm._strategy.close_all_windows.call_count == 1

    def test_backwards_compatibility_interface(self):
        """Test that facade maintains backwards compatible interface."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            # Verify all expected methods exist
            assert hasattr(wm, "create_monitoring_window")
            assert hasattr(wm, "close_window")
            assert hasattr(wm, "close_all_windows")
            assert hasattr(wm, "windows")

            # Verify methods are callable
            assert callable(wm.create_monitoring_window)
            assert callable(wm.close_window)
            assert callable(wm.close_all_windows)
