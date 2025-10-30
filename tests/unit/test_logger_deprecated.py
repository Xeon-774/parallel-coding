"""Unit tests for deprecated logger.py module.

Tests backward compatibility and deprecation warning.
"""

import warnings


def test_logger_imports_with_deprecation_warning():
    """Test that importing logger module issues deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import the deprecated module

        # Verify deprecation warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "orchestrator.logger is deprecated" in str(w[0].message)
        assert "orchestrator.core.structured_logging" in str(w[0].message)
        assert "v12.0" in str(w[0].message)


def test_logger_exports_all_classes():
    """Test that all classes are exported from deprecated module."""
    import orchestrator.logger as logger

    # Verify all expected exports are available
    assert hasattr(logger, "StructuredLogger")
    assert hasattr(logger, "LogLevel")
    assert hasattr(logger, "LogCategory")
    assert hasattr(logger, "LogContext")
    assert hasattr(logger, "LogEntry")
    assert hasattr(logger, "get_logger")


def test_logger_classes_are_functional():
    """Test that exported classes are functional."""
    import orchestrator.logger as logger

    # Test LogLevel enum
    assert hasattr(logger.LogLevel, "INFO")
    assert hasattr(logger.LogLevel, "WARNING")
    assert hasattr(logger.LogLevel, "ERROR")

    # Test LogCategory enum
    assert hasattr(logger.LogCategory, "SYSTEM")

    # Test get_logger function is callable
    assert callable(logger.get_logger)


def test_logger_all_attribute():
    """Test __all__ attribute contains expected exports."""
    import orchestrator.logger as logger

    expected_exports = [
        "StructuredLogger",
        "LogLevel",
        "LogCategory",
        "LogContext",
        "LogEntry",
        "get_logger",
    ]

    assert hasattr(logger, "__all__")
    assert set(logger.__all__) == set(expected_exports)
