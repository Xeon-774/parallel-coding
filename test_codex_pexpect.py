#!/usr / bin / env python
"""
Test Codex CLI with pexpect for full I / O control

This test verifies if we can:
1. Spawn codex exec process
2. Capture all output (including thinking / confirmation prompts)
3. Send responses automatically
4. Verify file creation

Excellence AI Standard: 100% Applied
"""

import sys
import time
from pathlib import Path

# Cross - platform pexpect import
if sys.platform == "win32":
    import wexpect as pexpect
else:
    import pexpect as pexpect


def test_codex_with_pexpect():
    """Test Codex CLI execution with full I / O control"""
    print("=" * 70)
    print("🧪 Testing Codex CLI with pexpect / wexpect")
    print("=" * 70)
    print()

    # Setup
    workspace = Path("test_codex_pexpect_workspace")
    workspace.mkdir(exist_ok=True)

    task_file = workspace / "task.txt"
    task_content = """Create a simple Python hello world function.
Save it to hello.py in the current directory.
The function should be named 'hello' and return 'Hello, World!'"""

    task_file.write_text(task_content, encoding="utf - 8")

    print(f"📁 Workspace: {workspace.absolute()}")
    print(f"📝 Task file: {task_file}")
    print()

    # Build command
    cmd = "codex exec --dangerously - bypass - approvals - and - sandbox"
    print(f"🚀 Command: {cmd}")
    print("📤 Sending task via stdin")
    print()

    try:
        # Spawn process
        print("⏳ Spawning codex process...")
        child = pexpect.spawn(cmd, cwd=str(workspace.absolute()), encoding="utf - 8", timeout=60)

        # Send task via stdin
        print("📨 Sending task content...")
        child.sendline(task_content)
        child.sendline("")  # EOF marker

        print()
        print("=" * 70)
        print("📡 CODEX OUTPUT:")
        print("=" * 70)

        output_buffer = []
        iteration = 0
        max_iterations = 100

        while iteration < max_iterations:
            iteration += 1

            try:
                # Wait for any output with short timeout
                index = child.expect([pexpect.TIMEOUT, pexpect.EOF, r".*\n"], timeout=2)  # Any line

                if index == 0:  # TIMEOUT
                    print(f"[Iteration {iteration}] Timeout (no output)")
                    # Check if process is still alive
                    if not child.isalive():
                        print("Process terminated")
                        break
                    continue

                elif index == 1:  # EOF
                    print("[EOF] Process completed")
                    break

                elif index == 2:  # Line output
                    before = child.before if child.before else ""
                    after = child.after if child.after else ""
                    line = before + after

                    output_buffer.append(line)
                    print(line, end="", flush=True)

                    # Check for confirmation patterns
                    if "?" in line or "approve" in line.lower() or "confirm" in line.lower():
                        print("\n[CONFIRMATION DETECTED] Sending 'yes'")
                        child.sendline("yes")

            except pexpect.TIMEOUT:
                print(f"[Iteration {iteration}] Timeout exception")
                if not child.isalive():
                    break
                continue
            except pexpect.EOF:
                print("[EOF] Process completed")
                break

        # Capture remaining output
        try:
            remaining = child.read()
            if remaining:
                output_buffer.append(remaining)
                print(remaining, flush=True)
        except:
            pass

        # Close process
        child.close()
        exit_code = child.exitstatus

        print()
        print("=" * 70)
        print("📊 RESULTS:")
        print("=" * 70)
        print(f"Exit code: {exit_code}")
        print(f"Total output lines: {len(output_buffer)}")
        print()

        # Check for created file
        hello_file = workspace / "hello.py"
        if hello_file.exists():
            print("✅ SUCCESS: hello.py was created!")
            print()
            print("📄 File content:")
            print("-" * 70)
            print(hello_file.read_text(encoding="utf - 8"))
            print("-" * 70)
            return True
        else:
            print("❌ FAILED: hello.py was NOT created")
            print()
            print("📁 Files in workspace:")
            for f in workspace.iterdir():
                print(f"  - {f.name}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_codex_with_pexpect()
    sys.exit(0 if success else 1)
