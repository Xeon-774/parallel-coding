#!/usr/bin/env python3
"""
Windows環境での簡単なテスト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator import RefactoredOrchestrator, OrchestratorConfig


def test_windows_mode():
    """Windows環境で簡単な計算テスト"""

    print("=" * 80)
    print("Windows環境テスト - 簡単な計算")
    print("=" * 80)
    print()

    # Windowsモードに設定
    os.environ['ORCHESTRATOR_MODE'] = 'windows'
    os.environ['CLAUDE_CODE_GIT_BASH_PATH'] = r'C:\opt\Git.Git\usr\bin\bash.exe'

    print(f"モード: {os.environ['ORCHESTRATOR_MODE']}")
    print(f"Git Bash: {os.environ['CLAUDE_CODE_GIT_BASH_PATH']}")
    print()

    # 簡単なタスク
    task = """
Pythonで簡単な計算をしてください：

1 + 1 の結果を計算して出力してください。
コードを書いて実行し、結果を表示してください。
"""

    print("タスク:", task.strip())
    print()
    print("[ORCHESTRATOR] 実行開始...")
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(
        config=config,
        enable_realtime_monitoring=True
    )

    try:
        result = orchestrator.execute(task)

        print()
        print("=" * 80)
        print("実行結果")
        print("=" * 80)

        if result:
            print("[SUCCESS] 成功")
            print()
            print("統合結果:")
            print(result)
        else:
            print("[FAILED] 失敗")

    except Exception as e:
        print(f"\n[ERROR] エラー発生: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)


if __name__ == '__main__':
    test_windows_mode()
