"""
DEPRECATED: This module is deprecated. Use orchestrator.utils package instead.

This file provides backward compatibility by re - exporting from the new location.
Will be removed in v12.0.

Migration guide:
    Old: from orchestrator.utils import convert_windows_to_wsl_path
    New: from orchestrator.utils import convert_windows_to_wsl_path  # same!

The import statement stays the same because utils is now a package.
"""

import warnings

from orchestrator.utils.helpers import (
    convert_windows_to_wsl_path,
    convert_wsl_to_windows_path,
    detect_platform,
    ensure_directory,
    format_duration,
    format_size,
    get_timestamp,
    is_linux,
    is_windows,
    safe_read_file,
    safe_write_file,
    truncate_string,
    validate_file_path,
)

# Issue deprecation warning
warnings.warn(
    "Importing from orchestrator.utils module directly is deprecated. "
    "Use 'from orchestrator.utils import ...' which now imports from the utils package. "
    "This compatibility module will be removed in v12.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
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
]
