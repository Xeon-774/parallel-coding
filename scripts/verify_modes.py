"""
実行モードの検証スクリプト

WSLモードとWindowsモードの両方でコマンド生成を確認
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig, find_git_bash


def verify_modes():
    """両方のモードでコマンド生成を検証"""
    print("=" * 80)
    print("MODE VERIFICATION TEST")
    print("=" * 80)
    print()

    # git - bash検出のテスト
    print("0. GIT - BASH DETECTION")
    print("-" * 80)
    git_bash = find_git_bash()
    if git_bash:
        print(f"git - bash found: {git_bash}")
    else:
        print("git - bash NOT found")
    print()

    # テスト用のパス
    test_input_win = r"D:\user\parallel_ai_test_project\workspace\worker_1\task.txt"
    test_output_win = r"D:\user\parallel_ai_test_project\workspace\worker_1\output.txt"

    test_input_wsl = "/mnt / d / user / parallel_ai_test_project / workspace / worker_1 / task.txt"
    test_output_wsl = (
        "/mnt / d / user / parallel_ai_test_project / workspace / worker_1 / output.txt"
    )

    # WSLモードのテスト
    print("1. WSL MODE")
    print("-" * 80)
    config_wsl = OrchestratorConfig(execution_mode="wsl")
    cmd_wsl = config_wsl.get_claude_command(test_input_wsl, test_output_wsl)
    print(f"Execution Mode: {config_wsl.execution_mode}")
    print("Command:")
    print(f"  {cmd_wsl}")
    print()

    # Windowsモードのテスト
    print("2. WINDOWS MODE")
    print("-" * 80)
    config_win = OrchestratorConfig(execution_mode="windows")
    cmd_win = config_win.get_claude_command(test_input_win, test_output_win)
    print(f"Execution Mode: {config_win.execution_mode}")
    print("Command:")
    print(f"  {cmd_win}")
    print()

    # 検証結果
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)

    # WSLモードの検証
    wsl_checks = [
        ("Uses wsl command", "wsl" in cmd_wsl),
        ("Uses WSL distribution", config_wsl.wsl_distribution in cmd_wsl),
        ("Uses NVM path", config_wsl.nvm_path in cmd_wsl),
        (
            "Uses claude flags",
            "--print" in cmd_wsl and "--dangerously - skip - permissions" in cmd_wsl,
        ),
    ]

    print("\nWSL Mode Checks:")
    for check_name, result in wsl_checks:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {check_name}")

    # Windowsモードの検証
    win_checks = [
        ("Uses bash or cmd", ("bash" in cmd_win.lower() or "cmd" in cmd_win)),
        ("Uses Windows paths", test_input_win in cmd_win),
        (
            "Uses claude flags",
            "--print" in cmd_win and "--dangerously - skip - permissions" in cmd_win,
        ),
        ("Does not use wsl command", "wsl -d" not in cmd_win.lower()),
    ]

    # git - bashが利用可能な場合の追加チェック
    if config_win.git_bash_path:
        win_checks.append(("Uses git - bash", config_win.git_bash_path in cmd_win))

    print("\nWindows Mode Checks:")
    for check_name, result in win_checks:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {check_name}")

    # 全体の結果
    all_passed = all(r for _, r in wsl_checks + win_checks)
    print()
    print("=" * 80)
    if all_passed:
        print("[SUCCESS] ALL CHECKS PASSED!")
    else:
        print("[FAILED] SOME CHECKS FAILED!")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    verify_modes()
