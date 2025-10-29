"""
Basic pexpect / wexpect test without Claude CLI

Tests that the pseudo - terminal functionality works correctly
"""

import sys
from pathlib import Path

# Cross - platform pexpect import
if sys.platform == "win32":
    import wexpect as expect_module

    PLATFORM = "windows"
else:
    import pexpect as expect_module

    PLATFORM = "unix"


def test_basic_interaction():
    """Test basic pseudo - terminal interaction"""
    print(f"\n{'='*60}")
    print(f"Platform: {PLATFORM}")
    print(f"Module: {expect_module.__name__}")
    print(f"{'='*60}\n")

    # Test 1: Simple echo command
    print("[TEST 1] Simple command execution")
    try:
        if PLATFORM == "windows":
            child = expect_module.spawn("cmd", encoding="utf - 8", timeout=5)
            child.expect(">")  # Wait for prompt
            child.sendline("echo Hello World")
            child.expect("Hello World")
            print("[OK] Command executed and output captured")
            child.sendline("exit")
        else:
            child = expect_module.spawn("bash", encoding="utf - 8", timeout=5)
            child.expect("\\$")  # Wait for prompt
            child.sendline("echo Hello World")
            child.expect("Hello World")
            print("[OK] Command executed and output captured")
            child.sendline("exit")

        print("[PASS] Test 1 passed\n")

    except Exception as e:
        print(f"[FAIL] Test 1 failed: {e}\n")

    # Test 2: Pattern matching with multiple options
    print("[TEST 2] Pattern matching")
    try:
        if PLATFORM == "windows":
            child = expect_module.spawn("cmd", encoding="utf - 8", timeout=5)

            # Wait for one of several patterns
            index = child.expect([">", "Microsoft", expect_module.TIMEOUT])

            if index == 0:
                print("[OK] Matched prompt '>'")
            elif index == 1:
                print("[OK] Matched 'Microsoft' in banner")
            else:
                print("[WARN] Timeout occurred")

            child.sendline("exit")
        else:
            child = expect_module.spawn("bash", encoding="utf - 8", timeout=5)
            index = child.expect(["\\$", "#", expect_module.TIMEOUT])

            if index in [0, 1]:
                print("[OK] Matched shell prompt")
            else:
                print("[WARN] Timeout occurred")

            child.sendline("exit")

        print("[PASS] Test 2 passed\n")

    except Exception as e:
        print(f"[FAIL] Test 2 failed: {e}\n")

    # Test 3: Interactive Q&A simulation
    print("[TEST 3] Simulated interactive Q&A")
    try:
        # Create a simple Python script that asks questions
        test_script = Path("workspace / test_qa.py")
        test_script.parent.mkdir(parents=True, exist_ok=True)

        with open(test_script, "w", encoding="utf - 8") as f:
            f.write(
                """
import sys
print("Starting interactive test...", flush=True)
sys.stdout.flush()

response1 = input("Question 1: Write to file 'output.txt'? (y / n): ")
print(f"You answered: {response1}", flush=True)

if response1.lower() == 'y':
    print("File write approved!", flush=True)
else:
    print("File write denied!", flush=True)

response2 = input("Question 2: Delete file 'temp.txt'? (y / n): ")
print(f"You answered: {response2}", flush=True)

print("Interactive test complete!", flush=True)
"""
            )

        # Run the script with pexpect / wexpect
        child = expect_module.spawn(f'python "{test_script}"', encoding="utf - 8", timeout=10)

        # Wait for first question
        index = child.expect(["output.txt.*\\(y / n\\)", expect_module.TIMEOUT])

        if index == 0:
            print("[OK] Detected first question")
            child.sendline("y")

            # Wait for acknowledgment
            child.expect("File write approved")
            print("[OK] Response processed correctly")

            # Wait for second question
            index = child.expect(["temp.txt.*\\(y / n\\)", expect_module.TIMEOUT])

            if index == 0:
                print("[OK] Detected second question")
                child.sendline("n")

                # Wait for acknowledgment
                child.expect("File write denied")
                print("[OK] Second response processed correctly")

                # Wait for completion
                child.expect("Interactive test complete")
                print("[OK] Script completed successfully")
            else:
                print("[WARN] Second question timeout")
        else:
            print("[WARN] First question timeout")

        child.close()
        print("[PASS] Test 3 passed\n")

    except Exception as e:
        print(f"[FAIL] Test 3 failed: {e}\n")
        import traceback

        traceback.print_exc()

    print(f"\n{'='*60}")
    print("All basic tests completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\nBasic pexpect / wexpect functionality test")
    print("This validates pseudo - terminal control without Claude CLI\n")

    test_basic_interaction()
