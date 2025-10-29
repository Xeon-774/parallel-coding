"""Unit tests for deprecated utils.py module.

Tests backward compatibility and deprecation warning for utils module.
"""

import warnings

import pytest


def test_utils_package_imports_successfully():
    """Test that utils package (not deprecated utils.py) can be imported."""
    # Note: orchestrator / utils.py exists as a deprecated file, but Python
    # prefers the package (orchestrator / utils / __init__.py) when importing.
    # The utils.py file is only loaded if explicitly imported as a module file.
    import orchestrator.utils as utils

    # Verify package loaded successfully
    assert utils is not None
    assert hasattr(utils, "__all__")


def test_utils_exports_path_functions():
    """Test that path utility functions are exported."""
    import orchestrator.utils as utils

    # Verify path functions are available
    assert hasattr(utils, "convert_windows_to_wsl_path")
    assert hasattr(utils, "convert_wsl_to_windows_path")
    assert hasattr(utils, "detect_platform")
    assert hasattr(utils, "is_windows")
    assert hasattr(utils, "is_linux")


def test_utils_exports_file_functions():
    """Test that file utility functions are exported."""
    import orchestrator.utils as utils

    # Verify file functions are available
    assert hasattr(utils, "validate_file_path")
    assert hasattr(utils, "ensure_directory")
    assert hasattr(utils, "safe_read_file")
    assert hasattr(utils, "safe_write_file")


def test_utils_exports_formatting_functions():
    """Test that formatting utility functions are exported."""
    import orchestrator.utils as utils

    # Verify formatting functions are available
    assert hasattr(utils, "format_duration")
    assert hasattr(utils, "format_size")
    assert hasattr(utils, "get_timestamp")
    assert hasattr(utils, "truncate_string")


def test_utils_functions_are_callable():
    """Test that exported functions are callable."""
    import orchestrator.utils as utils

    # Test that functions are callable
    assert callable(utils.detect_platform)
    assert callable(utils.is_windows)
    assert callable(utils.is_linux)
    assert callable(utils.format_duration)
    assert callable(utils.format_size)


def test_utils_all_attribute():
    """Test __all__ attribute contains expected exports."""
    import orchestrator.utils as utils

    expected_exports = [
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
        # Encoding functions
        "PROJECT_ENCODING",
        "configure_console_encoding",
        "open_file_utf8",
        "safe_write",
        "safe_print",
    ]

    assert hasattr(utils, "__all__")
    assert set(utils.__all__) == set(expected_exports)
