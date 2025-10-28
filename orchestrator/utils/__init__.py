"""
Utility modules for Claude Orchestrator
"""

# Helper functions (path conversion, platform detection, etc.)
from orchestrator.utils.helpers import (
    convert_windows_to_wsl_path,
    convert_wsl_to_windows_path,
    detect_platform,
    is_windows,
    is_linux,
    validate_file_path,
    ensure_directory,
    format_duration,
    format_size,
    get_timestamp,
    truncate_string,
    safe_read_file,
    safe_write_file,
)

# Encoding configuration (UTF-8 with BOM)
from orchestrator.utils.encoding_config import (
    PROJECT_ENCODING,
    configure_console_encoding,
    open_file_utf8,
    safe_write,
    safe_print,
)

# Authentication helpers and WSL setup utilities are imported lazily
# to avoid tkinter dependency in headless environments (Docker/API server)
# Import them explicitly when needed:
#   from orchestrator.utils.auth_helper import setup_claude_token
#   from orchestrator.utils.wsl_setup import WSLClaudeSetup

__all__ = [
    # Helper functions
    "convert_windows_to_wsl_path",
    "convert_wsl_to_windows_path",
    "detect_platform",
    "is_windows",
    "is_linux",
    "validate_file_path",
    "ensure_directory",
    "format_duration",
    "format_size",
    "get_timestamp",
    "truncate_string",
    "safe_read_file",
    "safe_write_file",
    # Encoding (UTF-8 with BOM - No JIS/Shift-JIS)
    "PROJECT_ENCODING",
    "configure_console_encoding",
    "open_file_utf8",
    "safe_write",
    "safe_print",
]
