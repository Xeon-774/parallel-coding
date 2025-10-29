#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
Environment Setup Script for Claude Orchestrator
Validates and configures required environment variables
"""

import os
import sys
from pathlib import Path
from typing import Tuple

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf - 8")
    sys.stderr.reconfigure(encoding="utf - 8")


def find_git_bash() -> str:
    """Locate Git Bash executable on Windows"""
    common_paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        r"C:\opt\Git.Git\usr\bin\bash.exe",
        r"C:\Windows\System32\bash.exe",
    ]

    for path in common_paths:
        if os.path.exists(path):
            print(f"[OK] Found Git Bash at: {path}")
            return path

    print("[ERROR] Git Bash not found in common locations")
    print("  Please install Git for Windows: https://git - scm.com / download / win")
    return ""


def validate_api_token(token: str) -> bool:
    """
    Validate Claude API token format (DEPRECATED)

    NOTE: API token authentication is deprecated.
    Use WSL Claude CLI login instead:
      1. Install WSL (Ubuntu - 24.04)
      2. Run `claude` command in WSL to login
      3. Orchestrator will use WSL Claude automatically
    """
    # API token validation is no longer required
    return True


def setup_environment() -> Tuple[bool, str]:
    """
    Setup and validate environment
    Returns: (success: bool, message: str)
    """
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_template = project_root / ".env.template"

    print("=" * 60)
    print("Claude Orchestrator - Environment Setup")
    print("=" * 60)
    print()

    # Check if .env exists
    if not env_file.exists():
        if env_template.exists():
            print("Creating .env from template...")

            # Auto - detect Git Bash
            git_bash_path = find_git_bash()

            # Read template
            template_content = env_template.read_text()

            # Replace Git Bash path if found
            if git_bash_path:
                template_content = template_content.replace(
                    "CLAUDE_CODE_GIT_BASH_PATH=C:\\opt\\Git.Git\\usr\\bin\\bash.exe",
                    f"CLAUDE_CODE_GIT_BASH_PATH={git_bash_path}",
                )

            # Write .env
            env_file.write_text(template_content, encoding="utf - 8")
            print(f"[OK] Created {env_file}")
            print()
            print("[WARN] IMPORTANT: Edit .env and add your Claude API token!")
            print("  Get your token from: https://console.anthropic.com/")
            print()
            return False, "Please configure .env file with your API token"
        else:
            return False, ".env.template not found"

    # Load .env
    print("Loading environment variables...")
    env_vars = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env_vars[key] = value
            os.environ[key] = value

    # Validate Git Bash path
    git_bash_path = env_vars.get("CLAUDE_CODE_GIT_BASH_PATH", "")
    if not git_bash_path or not os.path.exists(git_bash_path):
        print(f"[ERROR] Git Bash not found at: {git_bash_path}")
        auto_path = find_git_bash()
        if auto_path:
            print(f"  Update .env with: CLAUDE_CODE_GIT_BASH_PATH={auto_path}")
        return False, "Git Bash path invalid"
    else:
        print(f"[OK] Git Bash found: {git_bash_path}")

    # Claude Authentication (via WSL CLI login)
    print()
    print("=" * 60)
    print("Claude Authentication: WSL Claude CLI")
    print("=" * 60)
    print()
    print("[INFO] API token authentication is deprecated.")
    print("      Please use WSL Claude CLI login instead:")
    print()
    print("  1. Install WSL (Ubuntu - 24.04 or similar)")
    print("  2. Open WSL terminal")
    print("  3. Run: claude")
    print("  4. Follow login prompts")
    print()
    print("  After login, orchestrator will use WSL Claude automatically.")
    print()

    print("=" * 60)
    print("[SUCCESS] Environment setup complete!")
    print("=" * 60)
    print()
    print("Environment variables set:")
    print(f"  CLAUDE_CODE_GIT_BASH_PATH={git_bash_path}")
    print(f"  MAX_WORKERS={env_vars.get('MAX_WORKERS', '8')}")
    print(f"  MAX_DEPTH={env_vars.get('MAX_DEPTH', '3')}")
    print()

    return True, "Environment configured successfully"


if __name__ == "__main__":
    success, message = setup_environment()

    if success:
        print("[OK] You can now run tests: pytest tests/ -v")
        sys.exit(0)
    else:
        print(f"[ERROR] Setup incomplete: {message}")
        sys.exit(1)
