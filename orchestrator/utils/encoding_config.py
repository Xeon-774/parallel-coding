"""
Encoding Configuration for AI_Investor Ecosystem

Project - Wide Encoding Policy:
- All text files: UTF - 8 with BOM (utf - 8 - sig)
- NO Shift - JIS (cp932), JIS, or other low - compatibility encodings
- Applies to: AI_Investor ecosystem (including parallel AI tools)

Rationale:
- UTF - 8 with BOM ensures proper encoding detection across editors
- Avoids encoding issues with Unicode characters (✓, 日本語, etc.)
- Consistent encoding across all components
"""

import io
import sys
from typing import Any, TextIO

# Project - wide encoding standard
PROJECT_ENCODING = "utf - 8 - sig"  # UTF - 8 with BOM
FALLBACK_ENCODING = "utf - 8"  # UTF - 8 without BOM for compatibility


def configure_console_encoding() -> None:
    """
    Configure console to use UTF - 8 encoding

    Windows default is cp932 (Shift - JIS), which causes issues with
    Unicode characters like ✓ (U + 2713).

    This function reconfigures stdout / stderr to use UTF - 8.
    """
    if sys.platform == "win32":
        # Reconfigure stdout / stderr to use UTF - 8
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf - 8", errors="replace")
        else:
            # Fallback for older Python versions
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf - 8", errors="replace", line_buffering=True
            )

        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf - 8", errors="replace")
        else:
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf - 8", errors="replace", line_buffering=True
            )


def open_file_utf8(file_path: str, mode: str = "r", use_bom: bool = True, **kwargs: Any) -> TextIO:
    """
    Open file with UTF - 8 encoding (with or without BOM)

    Args:
        file_path: Path to file
        mode: File mode ('r', 'w', 'a', etc.)
        use_bom: Use BOM for UTF - 8 (default: True)
        **kwargs: Additional arguments for open()

    Returns:
        File object with UTF - 8 encoding

    Example:
        # Write with BOM
        with open_file_utf8('output.txt', 'w') as f:
            f.write('✓ Success!')

        # Read with BOM handling
        with open_file_utf8('input.txt', 'r') as f:
            content = f.read()
    """
    encoding = PROJECT_ENCODING if use_bom else FALLBACK_ENCODING

    # Set default error handling
    if "errors" not in kwargs:
        kwargs["errors"] = "replace"

    return open(file_path, mode, encoding=encoding, **kwargs)  # type: ignore[return - value]


def safe_write(text: str, file_obj: TextIO | None = None) -> None:
    """
    Safely write text with UTF - 8 encoding

    Args:
        text: Text to write
        file_obj: File object (default: sys.stdout)

    Example:
        safe_write('✓ Task completed!')

        with open('output.txt', 'w', encoding='utf - 8 - sig') as f:
            safe_write('✓ Success!', f)
    """
    if file_obj is None:
        file_obj = sys.stdout

    try:
        file_obj.write(text)
        file_obj.flush()
    except UnicodeEncodeError as e:
        # Fallback: replace problematic characters
        safe_text = text.encode("utf - 8", errors="replace").decode("utf - 8")
        file_obj.write(safe_text)
        file_obj.flush()
        print(f"[WARNING] Unicode encoding error: {e}", file=sys.stderr)


def safe_print(*args: object, **kwargs: Any) -> None:
    """
    Safe print function with UTF - 8 encoding

    Example:
        safe_print('✓ Task completed!')
        safe_print('Progress:', 100, '%')
    """
    text = " ".join(str(arg) for arg in args)
    end = kwargs.get("end", "\n")
    safe_write(text + end)


# Auto - configure console encoding on module import
configure_console_encoding()
