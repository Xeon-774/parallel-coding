"""
Quick test to verify parallel AI orchestrator setup
"""

import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.config import OrchestratorConfig


def test_config():
    """Test configuration"""
    config = OrchestratorConfig()

    print("=" * 60)
    print("PARALLEL AI ORCHESTRATOR - Configuration Test")
    print("=" * 60)
    print(f"\n✓ Execution Mode: {config.execution_mode}")
    print(f"✓ WSL Distribution: {config.wsl_distribution}")
    print(f"✓ Claude Path: {config.nvm_path}/{config.claude_command}")
    print(f"✓ Workspace Root: {config.workspace_root}")
    print(f"✓ Max Workers: {config.max_workers}")

    # Test command generation
    test_input = "/mnt/d/test/input.txt"
    test_output = "/mnt/d/test/output.txt"
    cmd = config.get_claude_command_wsl(test_input, test_output)

    print(f"\n✓ Generated Command:")
    print(f"  {cmd}")

    print("\n" + "=" * 60)
    print("✅ Configuration test PASSED!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
