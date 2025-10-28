#!/usr/bin/env python3
"""
Update import statements after refactoring
"""
import re
from pathlib import Path

# Define the replacements
REPLACEMENTS = [
    # ai_safety_judge.py moved to common/
    (
        r'from orchestrator\.core\.ai_safety_judge import',
        'from orchestrator.core.common.ai_safety_judge import'
    ),
    # metrics_collector.py moved to common/ and renamed to metrics.py
    (
        r'from orchestrator\.core\.metrics_collector import',
        'from orchestrator.core.common.metrics import'
    ),
    # worker_manager.py moved to worker/
    (
        r'from orchestrator\.core\.worker_manager import',
        'from orchestrator.core.worker.worker_manager import'
    ),
]

def update_file(file_path: Path) -> bool:
    """Update imports in a single file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Apply all replacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"[OK] Updated: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Error updating {file_path}: {e}")
        return False

def main():
    root = Path(__file__).parent
    files_updated = 0

    # Find all Python files
    py_files = list(root.rglob("*.py"))

    print(f"Found {len(py_files)} Python files")
    print("Updating import statements...\n")

    for py_file in py_files:
        # Skip this script itself
        if py_file.name == "update_imports.py":
            continue

        if update_file(py_file):
            files_updated += 1

    print(f"\n[DONE] Updated {files_updated} files")

if __name__ == "__main__":
    main()
