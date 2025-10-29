"""
Quick test for ClaudeAPIProvider

Test Claude API Provider functionality with a simple task.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.core.ai_providers.claude_api_provider import (
    ClaudeAPIConfig,
    ClaudeAPIError,
    ClaudeAPIProvider,
)


async def test_claude_api_provider():
    """Test Claude API Provider with simple task"""

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return False

    print("=" * 70)
    print("Claude API Provider Test")
    print("=" * 70)

    try:
        # Create config
        config = ClaudeAPIConfig(
            api_key=api_key, workspace_root="./test_workspace", timeout_seconds=120, max_tokens=2048
        )

        print("✓ Configuration created")
        print(f"  Model: {config.model}")
        print(f"  Workspace: {config.workspace_root}")
        print(f"  Timeout: {config.timeout_seconds}s\n")

        # Create provider
        provider = ClaudeAPIProvider(config)
        print("✓ Provider initialized\n")

        # Test execution
        print("Executing test task...")
        print("Task: Create a simple Python function")
        print()

        result = await provider.execute_async(
            prompt="Create a Python function named 'add_numbers' that takes two parameters (a, b) and returns their sum. Save it to test_function.py file.",
            system_prompt="You are an expert Python developer. Write clean, documented code.",
        )

        print("=" * 70)
        print("RESULT")
        print("=" * 70)
        print(f"Status: {result.status}")
        print(f"Execution time: {result.execution_time_seconds:.2f}s")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Retries: {result.retry_count}")
        print(f"File operations: {len(result.file_operations)}")

        if result.file_operations:
            print("\nFile Operations:")
            for file_op in result.file_operations:
                print(f"  - {file_op.operation_type.value}: {file_op.file_path}")
                if not file_op.success:
                    print(f"    ERROR: {file_op.error_message}")

        print(f"\nOutput:\n{result.output}\n")

        if result.is_success:
            print("✓ Test PASSED")
            return True
        else:
            print(f"✗ Test FAILED: {result.error}")
            return False

    except ClaudeAPIError as e:
        print(f"✗ Claude API Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_claude_api_provider())
    sys.exit(0 if success else 1)
