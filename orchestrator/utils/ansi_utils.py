"""ANSI utilities.

Provides helpers to sanitize terminal output by removing ANSI escape
sequences. Designed for performance and safety.

Example:
    >>> from orchestrator.utils.ansi_utils import strip_ansi
    >>> strip_ansi("\x1b[31mError\x1b[0m")
    'Error'
"""

from __future__ import annotations

import re
from typing import Final

_ANSI_RE: Final[re.Pattern[str]] = re.compile(
    r"\x1b\[[0-9;?]*[A-Za-z]"
)


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from a string.

    Args:
        text: Input string that may contain ANSI escape sequences.

    Returns:
        The input without ANSI sequences.

    Examples:
        >>> strip_ansi("\x1b[1mBold\x1b[0m")
        'Bold'
        >>> strip_ansi("No color")
        'No color'
    """

    if not text:
        return text
    return _ANSI_RE.sub("", text)


# Backward compatibility alias
strip_ansi_codes = strip_ansi

