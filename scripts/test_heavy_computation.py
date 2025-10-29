#!/usr/bin/env python3
"""
Windows環境での高負荷計算テスト

計算集約的なタスクでリアルタイム監視を確認
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator import OrchestratorConfig, RefactoredOrchestrator


def test_heavy_computation():
    """計算集約的なタスクをテスト"""

    print("=" * 80)
    print("Windows環境テスト - 高負荷計算")
    print("=" * 80)
    print()

    # Windowsモードに設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"

    print(f"モード: {os.environ['ORCHESTRATOR_MODE']}")
    print(f"Git Bash: {os.environ['CLAUDE_CODE_GIT_BASH_PATH']}")
    print()

    # 計算集約的なタスク
    task = """
Pythonで以下の計算タスクを実行してください：

1. **素数探索**: 10000から11000までの範囲の素数をすべて見つける
2. **フィボナッチ数**: 40番目のフィボナッチ数を再帰的に計算
3. **円周率近似**: モンテカルロ法で円周率を推定（100万回試行）

各タスクの実行結果と計算時間を表示してください。

**重要**:
- すべてのコードを実際に実行してください
- 進捗状況を適宜出力してください
- 最終結果を明確に表示してください
"""

    print("タスク内容:")
    print("  1. 素数探索 (10000-11000)")
    print("  2. フィボナッチ数 (40番目)")
    print("  3. 円周率近似 (モンテカルロ法、100万回試行)")
    print()
    print("[ORCHESTRATOR] 実行開始...")
    print("[INFO] リアルタイム監視: 有効")
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(
        config=config, enable_realtime_monitoring=True  # リアルタイム監視を有効化
    )

    import time

    start_time = time.time()

    try:
        result = orchestrator.execute(task)
        execution_time = time.time() - start_time

        print()
        print("=" * 80)
        print("実行結果")
        print("=" * 80)
        print(f"総実行時間: {execution_time:.2f}秒")
        print()

        if result:
            print("[SUCCESS] 計算完了")
            print()
            print("統合結果:")
            print("-" * 80)
            print(result)
            print("-" * 80)
        else:
            print("[FAILED] 計算失敗")

        # ワーカー出力も表示
        workspace_path = Path(config.workspace_root)
        worker_output = workspace_path / "worker_1" / "output.txt"

        if worker_output.exists():
            print()
            print("=" * 80)
            print("ワーカー詳細出力")
            print("=" * 80)
            with open(worker_output, "r", encoding="utf-8") as f:
                print(f.read())

    except Exception as e:
        print(f"\n[ERROR] エラー発生: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("テスト完了")
    print("=" * 80)


if __name__ == "__main__":
    test_heavy_computation()
