"""Unit tests for small utility modules.

Tests common / models.py, ansi_utils.py, and window_manager.py.
"""

import time

from orchestrator.core.common.models import (
    ConfirmationRequest,
    ConfirmationType,
)
from orchestrator.utils.ansi_utils import strip_ansi, strip_ansi_codes
from orchestrator.window_manager import WindowInfo, WindowManager

# ======================= Common Models Tests =======================


class TestConfirmationType:
    """Test ConfirmationType enum."""

    def test_all_confirmation_types(self):
        """Test all confirmation type values."""
        assert ConfirmationType.FILE_WRITE == "file_write"
        assert ConfirmationType.FILE_DELETE == "file_delete"
        assert ConfirmationType.FILE_READ == "file_read"
        assert ConfirmationType.COMMAND_EXECUTE == "command_execute"
        assert ConfirmationType.PACKAGE_INSTALL == "package_install"
        assert ConfirmationType.NETWORK_ACCESS == "network_access"
        assert ConfirmationType.PERMISSION_REQUEST == "permission_request"
        assert ConfirmationType.UNKNOWN == "unknown"


class TestConfirmationRequest:
    """Test ConfirmationRequest dataclass."""

    def test_create_confirmation_request(self):
        """Test creating a confirmation request."""
        req = ConfirmationRequest(
            worker_id="w123",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Write to file",
            details={"path": "/tmp / test.txt"},
        )

        assert req.worker_id == "w123"
        assert req.confirmation_type == ConfirmationType.FILE_WRITE
        assert req.message == "Write to file"
        assert req.details == {"path": "/tmp / test.txt"}
        assert req.timestamp > 0

    def test_is_dangerous_file_delete(self):
        """Test that file delete is marked as dangerous."""
        req = ConfirmationRequest(
            worker_id="w123",
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete file",
            details={},
        )

        assert req.is_dangerous() is True

    def test_is_dangerous_command_execute(self):
        """Test that command execute is marked as dangerous."""
        req = ConfirmationRequest(
            worker_id="w123",
            confirmation_type=ConfirmationType.COMMAND_EXECUTE,
            message="Run command",
            details={},
        )

        assert req.is_dangerous() is True

    def test_is_not_dangerous_file_write(self):
        """Test that file write is not marked as dangerous."""
        req = ConfirmationRequest(
            worker_id="w123",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Write file",
            details={},
        )

        assert req.is_dangerous() is False

    def test_is_not_dangerous_file_read(self):
        """Test that file read is not marked as dangerous."""
        req = ConfirmationRequest(
            worker_id="w123",
            confirmation_type=ConfirmationType.FILE_READ,
            message="Read file",
            details={},
        )

        assert req.is_dangerous() is False

    def test_timestamp_auto_generated(self):
        """Test that timestamp is auto - generated."""
        before = time.time()
        req = ConfirmationRequest(
            worker_id="w123",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Test",
            details={},
        )
        after = time.time()

        assert before <= req.timestamp <= after


# ======================= ANSI Utils Tests =======================


class TestStripAnsi:
    """Test strip_ansi function."""

    def test_strip_ansi_with_color_codes(self):
        """Test stripping ANSI color codes."""
        text = "\x1b[31mError\x1b[0m"
        result = strip_ansi(text)
        assert result == "Error"

    def test_strip_ansi_with_bold(self):
        """Test stripping ANSI bold codes."""
        text = "\x1b[1mBold text\x1b[0m"
        result = strip_ansi(text)
        assert result == "Bold text"

    def test_strip_ansi_no_codes(self):
        """Test text without ANSI codes."""
        text = "Plain text"
        result = strip_ansi(text)
        assert result == "Plain text"

    def test_strip_ansi_empty_string(self):
        """Test with empty string."""
        result = strip_ansi("")
        assert result == ""

    def test_strip_ansi_multiple_codes(self):
        """Test with multiple ANSI codes."""
        text = "\x1b[1m\x1b[31mBold Red\x1b[0m\x1b[0m"
        result = strip_ansi(text)
        assert result == "Bold Red"

    def test_strip_ansi_complex_sequence(self):
        """Test with complex ANSI sequences."""
        text = "\x1b[38;5;214mOrange\x1b[0m"
        result = strip_ansi(text)
        assert result == "Orange"

    def test_strip_ansi_codes_alias(self):
        """Test backward compatibility alias."""
        text = "\x1b[32mGreen\x1b[0m"
        result = strip_ansi_codes(text)
        assert result == "Green"


# ======================= Window Manager Tests =======================


class TestWindowManager:
    """Test WindowManager facade."""

    def test_create_window_manager_no_screenshots(self):
        """Test creating WindowManager without screenshots."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            assert wm is not None

    def test_create_window_manager_with_options(self):
        """Test creating WindowManager with custom options."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(
                workspace_root=tmpdir,
                execution_mode="windows",
                auto_close=False,
                close_delay=5,
                enable_screenshots=False,
            )

            assert wm is not None

    def test_create_window_manager_wsl_mode(self):
        """Test creating WindowManager in WSL mode."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(
                workspace_root=tmpdir, execution_mode="wsl", enable_screenshots=False
            )

            assert wm is not None

    def test_window_manager_has_strategy(self):
        """Test that WindowManager delegates to a strategy."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            # WindowManager should have a _strategy attribute
            assert hasattr(wm, "_strategy")
            assert wm._strategy is not None

    def test_window_manager_create_monitoring_window_method(self):
        """Test that WindowManager has create_monitoring_window method."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            assert hasattr(wm, "create_monitoring_window")
            assert callable(wm.create_monitoring_window)

    def test_window_manager_close_window_method(self):
        """Test that WindowManager has close_window method."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            assert hasattr(wm, "close_window")
            assert callable(wm.close_window)

    def test_window_manager_close_all_windows_method(self):
        """Test that WindowManager has close_all_windows method."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            assert hasattr(wm, "close_all_windows")
            assert callable(wm.close_all_windows)

    def test_window_manager_windows_property(self):
        """Test that WindowManager has windows property."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            wm = WindowManager(workspace_root=tmpdir, enable_screenshots=False)

            assert hasattr(wm, "windows")


class TestWindowInfo:
    """Test WindowInfo dataclass."""

    def test_window_info_import(self):
        """Test that WindowInfo can be imported."""
        assert WindowInfo is not None

    def test_window_info_is_class(self):
        """Test that WindowInfo is a class."""
        assert isinstance(WindowInfo, type)
