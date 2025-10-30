#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
Script to run Codex for design document creation.
Handles TTY requirements and captures output properly.
"""

import subprocess
import sys
from pathlib import Path

# Force UTF - 8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf - 8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf - 8")


def run_codex_with_pseudo_tty(prompt: str, output_file: Path) -> int:
    """Run codex with pseudo - TTY to avoid 'stdout is not a terminal' error"""

    # Codex paths (different for Windows vs WSL)
    CODEX_PATH_WSL = "/mnt / c / Users / chemi / AppData / Roaming / npm / codex"
    CODEX_PATH_WINDOWS = "/c / Users / chemi / AppData / Roaming / npm / codex"

    # Method 1: Try WSL bash with full codex path
    if sys.platform == "win32":
        try:
            # Escape single quotes in prompt for shell
            escaped_prompt = prompt.replace("'", "'\\''")

            result = subprocess.run(
                [
                    "wsl",
                    "-d",
                    "Ubuntu - 24.04",
                    "bash",
                    "-c",
                    f"{CODEX_PATH_WSL} '{escaped_prompt}'",
                ],
                capture_output=True,
                text=True,
                encoding="utf - 8",
                errors="replace",  # Handle encoding errors gracefully
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0 and result.stdout:
                output_file.write_text(result.stdout, encoding="utf - 8")
                print(f"Success! Output written to {output_file}")
                return 0
            else:
                stderr_msg = result.stderr[:200] if result.stderr else "No error output"
                print(f"[INFO] WSL method failed: {stderr_msg}")
        except FileNotFoundError:
            print("[INFO] WSL not available, trying alternative...")
        except subprocess.TimeoutExpired:
            print("Error: Codex execution timed out after 5 minutes")
            return 1
        except Exception as e:
            print(f"[INFO] WSL method error: {e}")

    # Method 2: Try using script command (Unix / WSL)
    try:
        result = subprocess.run(
            ["script", "-q", "-c", f"{CODEX_PATH_WSL} '{prompt}'", "/dev / null"],
            capture_output=True,
            text=True,
            encoding="utf - 8",
            errors="replace",
            timeout=300,
        )

        if result.returncode == 0:
            output_file.write_text(result.stdout, encoding="utf - 8")
            print(f"Success! Output written to {output_file}")
            return 0
        else:
            stderr_msg = result.stderr[:200] if result.stderr else "No error output"
            print(f"[INFO] Script command failed: {stderr_msg}")
    except FileNotFoundError:
        print("[INFO] Script command not available, trying alternative...")
    except subprocess.TimeoutExpired:
        print("Error: Codex execution timed out after 5 minutes")
        return 1

    # Method 3: Try using winpty (Windows) with full path
    try:
        result = subprocess.run(
            ["winpty", CODEX_PATH_WINDOWS, prompt],
            capture_output=True,
            text=True,
            encoding="utf - 8",
            errors="replace",
            timeout=300,
        )

        if result.returncode == 0:
            output_file.write_text(result.stdout, encoding="utf - 8")
            print(f"Success! Output written to {output_file}")
            return 0
        else:
            stderr_msg = result.stderr[:200] if result.stderr else "No error output"
            print(f"[INFO] Winpty command failed: {stderr_msg}")
    except FileNotFoundError:
        print("[INFO] Winpty not available, trying direct method...")

    # Method 4: Try with pty module (Unix only) with full path
    try:
        import os
        import pty

        master, slave = pty.openpty()

        process = subprocess.Popen(
            [CODEX_PATH_WSL, prompt], stdin=slave, stdout=slave, stderr=slave, text=True
        )

        os.close(slave)

        output = ""
        try:
            while True:
                data = os.read(master, 1024).decode("utf - 8", errors="replace")
                if not data:
                    break
                output += data
        except OSError:
            pass

        os.close(master)
        process.wait(timeout=300)

        if output:
            output_file.write_text(output, encoding="utf - 8")
            print(f"Success! Output written to {output_file}")
            return 0

    except (ImportError, OSError) as e:
        print(f"[INFO] PTY method not available: {e}")

    # Method 5: Direct subprocess with full path
    try:
        result = subprocess.run(
            [CODEX_PATH_WINDOWS, prompt],
            input="",  # Empty stdin
            capture_output=True,
            text=True,
            encoding="utf - 8",
            errors="replace",
            timeout=300,
            env={**subprocess.os.environ, "TERM": "dumb"},  # Disable TTY features
        )

        # Check if output contains error
        if "stdout is not a terminal" in result.stdout or result.returncode != 0:
            stdout_msg = result.stdout[:200] if result.stdout else "No output"
            stderr_msg = result.stderr[:200] if result.stderr else "No error output"
            print("[INFO] Direct method failed")
            print(f"stdout: {stdout_msg}")
            print(f"stderr: {stderr_msg}")
            return 1

        output_file.write_text(result.stdout, encoding="utf - 8")
        print(f"Success! Output written to {output_file}")
        return 0

    except Exception as e:
        print(f"[INFO] Direct method failed: {e}")
        return 1

    print("[ERROR] All methods failed. Codex requires interactive terminal.")
    print("[INFO] Please run codex manually in an interactive terminal:")
    print(f'  codex "{prompt[:50]}..."')
    return 1


def main():
    # Read the task from file
    task_file = Path(__file__).parent.parent / "tmp" / "codex_design_task.md"

    if not task_file.exists():
        # Create inline prompt if file doesn't exist
        prompt = """Design a fully autonomous AI development system with Supervisor / Orchestrator / Worker architecture.

Include the following sections:

1. System Architecture
   - Component interactions
   - Data flow
   - API contracts
   - Fault tolerance

2. Implementation Roadmap (10 weeks)
   - Phase breakdown
   - Time estimates
   - Dependencies
   - Quality gates

3. Technical Specifications
   - Technology stack
   - Performance requirements
   - Scalability
   - Security measures

4. Risk Assessment
   - Potential failures
   - Mitigation strategies
   - Recovery procedures

5. Success Metrics
   - KPIs
   - Quality benchmarks
   - Business value

Be comprehensive, innovative, and world - class professional. Output in detailed Markdown format."""
    else:
        prompt = task_file.read_text(encoding="utf - 8")

    # Output file
    output_file = (
        Path(__file__).parent.parent / "docs" / "design" / "codex_autonomous_ai_design_v1.md"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("Running Codex design task...")
    print(f"Output will be saved to: {output_file}")
    print(f"Prompt length: {len(prompt)} characters")
    print("-" * 60)

    return run_codex_with_pseudo_tty(prompt, output_file)


if __name__ == "__main__":
    sys.exit(main())
