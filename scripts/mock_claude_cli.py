"""
Mock Claude CLI for Testing

Simulates Claude CLI behavior including confirmation requests.
This allows testing EnhancedInteractiveWorkerManager without actual Claude CLI.

Usage:
    python scripts / mock_claude_cli.py < task.txt
"""

import sys
import time


def simulate_claude_response():
    """Simulate Claude CLI processing a task"""

    # Read task from stdin
    print("Reading task from stdin...", flush=True)
    task = sys.stdin.read()

    print(f"\n[Mock Claude CLI] Received task ({len(task)} chars)", flush=True)
    time.sleep(0.5)

    print("\n[Mock Claude] Analyzing task...", flush=True)
    time.sleep(0.5)

    print("[Mock Claude] I'll help you with this task.\n", flush=True)
    time.sleep(0.5)

    # Simulate file write confirmation
    print("I'm going to create a new file.", flush=True)
    time.sleep(0.3)

    print("Write to file 'output.py'? (y / n): ", end="", flush=True)

    # Wait for response
    response = input()

    if response.lower() == "y":
        print("\n[Mock Claude] Great! Creating file output.py...", flush=True)
        time.sleep(0.5)
        print("[Mock Claude] File created successfully!", flush=True)
    else:
        print("\n[Mock Claude] Okay, I won't create the file.", flush=True)

    time.sleep(0.5)

    # Simulate another confirmation
    print("\n[Mock Claude] Now I'll create the actual content.", flush=True)
    time.sleep(0.3)

    print("Create file 'hello.py' with Hello World code? (y / n): ", end="", flush=True)

    response = input()

    if response.lower() == "y":
        print("\n[Mock Claude] Creating hello.py...", flush=True)
        time.sleep(0.5)
        print("[Mock Claude] Done! The file contains:", flush=True)
        print("```python", flush=True)
        print("print('Hello, World!')", flush=True)
        print("```", flush=True)
    else:
        print("\n[Mock Claude] Understood, skipping file creation.", flush=True)

    time.sleep(0.5)

    # Simulate command execution request
    print("\n[Mock Claude] Let me verify the file was created.", flush=True)
    time.sleep(0.3)

    print("Execute command 'dir' to list files? (y / n): ", end="", flush=True)

    response = input()

    if response.lower() == "y":
        print("\n[Mock Claude] Running dir command...", flush=True)
        time.sleep(0.3)
        print("hello.py", flush=True)
        print("output.py", flush=True)
        print("task.txt", flush=True)
        print("\n[Mock Claude] Files verified!", flush=True)
    else:
        print("\n[Mock Claude] Skipping verification.", flush=True)

    time.sleep(0.5)

    # Complete
    print("\n[Mock Claude] Task completed successfully!", flush=True)
    print("[Mock Claude] Summary: Created Python files and verified.", flush=True)

    return 0


if __name__ == "__main__":
    try:
        exit_code = simulate_claude_response()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[Mock Claude] Interrupted by user", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[Mock Claude] Error: {e}", flush=True, file=sys.stderr)
        sys.exit(1)
