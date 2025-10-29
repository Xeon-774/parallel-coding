#!/usr/bin/env python3
"""
Codex Background Execution Wrapper
Fixes Python 3.13 _pyrepl console handle issues in background processes
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Execute codex with proper environment for background execution"""

    # Python 3.13 fix: Disable new REPL to prevent console handle errors
    env = os.environ.copy()
    env["PYTHON_BASIC_REPL"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    # Get codex command and arguments
    codex_args = sys.argv[1:]  # Forward all arguments

    # Execute codex with fixed environment
    cmd = ["codex"] + codex_args

    try:
        result = subprocess.run(
            cmd,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=subprocess.DEVNULL,  # No interactive input in background
            check=False,
        )
        sys.exit(result.returncode)

    except FileNotFoundError:
        print("ERROR: 'codex' command not found. Please ensure it's installed.", file=sys.stderr)
        print("Install with: npm install -g @openai/codex", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nCodex execution interrupted by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"ERROR: Codex execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
