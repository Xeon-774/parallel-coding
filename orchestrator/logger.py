"""
DEPRECATED: This module is deprecated. Use orchestrator.core.structured_logging instead.

This file provides backward compatibility by re - exporting from the new location.
Will be removed in v12.0.
"""

import warnings

from orchestrator.core.structured_logging import (
    LogCategory,
    LogContext,
    LogEntry,
    LogLevel,
    StructuredLogger,
    get_logger,
)

# Issue deprecation warning
warnings.warn(
    "orchestrator.logger is deprecated. Use orchestrator.core.structured_logging instead. "
    "This module will be removed in v12.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "StructuredLogger",
    "LogLevel",
    "LogCategory",
    "LogContext",
    "LogEntry",
    "get_logger",
]
