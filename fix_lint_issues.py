#!/usr / bin / env python3
"""
Automated lint issue fixer
Fixes common flake8 issues in the codebase
"""

import re
import subprocess
from pathlib import Path
from typing import Tuple


def fix_f_string_placeholders(file_path: Path) -> int:
    """
    Fix F541: f - string without placeholders
    Replace "string" with "string" if no {placeholders}
    """
    try:
        content = file_path.read_text(encoding="utf - 8")
        original = content

        # Replace f - strings without placeholders
        # Pattern: "..." or '...' with no {variables}
        patterns = [
            (r'"([^"{]*)"', r'"\1"'),  # "text" -> "text"
            (r"'([^'{]*)'", r"'\1'"),  # 'text' -> 'text'
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original:
            file_path.write_text(content, encoding="utf - 8")
            return 1
        return 0
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return 0


def remove_unused_imports(file_path: Path) -> int:
    """
    Remove unused imports using autoflake
    """
    try:
        result = subprocess.run(
            [
                "autoflake",
                "--in - place",
                "--remove - unused - variables",
                "--remove - all - unused - imports",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return 1 if result.returncode == 0 else 0
    except FileNotFoundError:
        # autoflake not installed, skip
        return 0
    except Exception as e:
        print(f"Error removing imports from {file_path}: {e}")
        return 0


def remove_trailing_whitespace(file_path: Path) -> int:
    """
    Remove trailing whitespace and blank lines at EOF
    """
    try:
        content = file_path.read_text(encoding="utf - 8")
        original = content

        # Remove trailing whitespace from each line
        lines = content.split("\n")
        lines = [line.rstrip() for line in lines]

        # Remove blank lines at end of file
        while lines and lines[-1] == "":
            lines.pop()

        # Ensure single newline at end
        content = "\n".join(lines) + "\n"

        if content != original:
            file_path.write_text(content, encoding="utf - 8")
            return 1
        return 0
    except Exception as e:
        print(f"Error fixing whitespace in {file_path}: {e}")
        return 0


def fix_arithmetic_spacing(file_path: Path) -> int:
    """
    Fix E226: Add whitespace around arithmetic operators
    """
    try:
        content = file_path.read_text(encoding="utf - 8")
        original = content

        # Add spaces around arithmetic operators (simple cases)
        patterns = [
            (r"(\w)(\+)(\w)", r"\1 \2 \3"),  # a + b -> a + b
            (r"(\w)(-)(\w)", r"\1 \2 \3"),  # a - b -> a - b
            (r"(\w)(\*)(\w)", r"\1 \2 \3"),  # a * b -> a * b
            (r"(\w)(/)(\w)", r"\1 \2 \3"),  # a / b -> a / b
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original:
            file_path.write_text(content, encoding="utf - 8")
            return 1
        return 0
    except Exception as e:
        print(f"Error fixing spacing in {file_path}: {e}")
        return 0


def process_python_files(root_dir: Path) -> Tuple[int, int, int, int]:
    """
    Process all Python files in directory
    Returns: (f_string_fixes, import_fixes, whitespace_fixes, spacing_fixes)
    """
    f_string_count = 0
    import_count = 0
    whitespace_count = 0
    spacing_count = 0

    python_files = list(root_dir.rglob("*.py"))
    total = len(python_files)

    print(f"Processing {total} Python files...")

    for i, file_path in enumerate(python_files, 1):
        if i % 50 == 0:
            print(f"  Progress: {i}/{total} files...")

        # Skip certain directories
        skip_dirs = ["venv", "env", ".venv", "__pycache__", "node_modules", ".git"]
        if any(skip in file_path.parts for skip in skip_dirs):
            continue

        f_string_count += fix_f_string_placeholders(file_path)
        import_count += remove_unused_imports(file_path)
        whitespace_count += remove_trailing_whitespace(file_path)
        spacing_count += fix_arithmetic_spacing(file_path)

    return f_string_count, import_count, whitespace_count, spacing_count


def main():
    """Main execution"""
    print("=" * 60)
    print("Automated Lint Issue Fixer")
    print("=" * 60)

    root = Path.cwd()
    print(f"Working directory: {root}")

    # Run fixes
    f_string, imports, whitespace, spacing = process_python_files(root)

    # Summary
    print("\n" + "=" * 60)
    print("Fix Summary")
    print("=" * 60)
    print(f"F541 (f - string placeholders): {f_string} files fixed")
    print(f"F401 (unused imports): {imports} files fixed")
    print(f"W291 / W391 (whitespace): {whitespace} files fixed")
    print(f"E226 (arithmetic spacing): {spacing} files fixed")
    print(f"Total: {f_string + imports + whitespace + spacing} files modified")

    # Run black and isort
    print("\n" + "=" * 60)
    print("Running black and isort...")
    print("=" * 60)

    try:
        subprocess.run(["black", ".", "--line - length", "100"], cwd=root, check=False, timeout=120)
        print("✅ black completed")
    except Exception as e:
        print(f"⚠️  black failed: {e}")

    try:
        subprocess.run(["isort", ".", "--profile", "black"], cwd=root, check=False, timeout=120)
        print("✅ isort completed")
    except Exception as e:
        print(f"⚠️  isort failed: {e}")

    print("\n✅ Lint fixes complete!")


if __name__ == "__main__":
    main()
