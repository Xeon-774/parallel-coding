#!/usr / bin / env python3
"""
真の並列実行テスト - 複数ワーカーAIの同時実行

複数のClaude AIインスタンスを同時に起動し、
リアルタイムで並列実行の様子を視覚化
"""

import os
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF - 8出力設定
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf - 8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf - 8")(sys.stderr.buffer, "replace")

from orchestrator import OrchestratorConfig, RefactoredOrchestrator


def test_true_parallel_execution(num_workers: int = 5):
    """
    複数ワーカーの真の並列実行をテスト

    Args:
        num_workers: ワーカー数
    """
    print("=" * 80)
    print("真の並列実行テスト - 複数Claude AIインスタンス")
    print("=" * 80)
    print(f"ワーカー数: {num_workers}")
    print()

    # Windowsモードに設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"

    print(f"実行モード: {os.environ['ORCHESTRATOR_MODE']}")
    print(f"Git Bash: {os.environ['CLAUDE_CODE_GIT_BASH_PATH']}")
    print("リアルタイム監視: 有効")
    print()

    # 各ワーカーに異なるタスクを割り当て
    tasks_list = [
        {
            "id": 1,
            "name": "Fibonacci計算",
            "prompt": """
Pythonで35番目のフィボナッチ数を再帰的に計算してください。
進捗を表示しながら計算し、結果を出力してください。
""",
        },
        {
            "id": 2,
            "name": "素数探索",
            "prompt": """
Pythonで5000から6000までの素数を探索してください。
見つかった素数の数と最初の10個を表示してください。
""",
        },
        {
            "id": 3,
            "name": "ソート実装",
            "prompt": """
Pythonでクイックソートを実装し、ランダムな1000個の数値をソートしてください。
ソート前後の最初の10個を表示してください。
""",
        },
        {
            "id": 4,
            "name": "行列計算",
            "prompt": """
Pythonで50x50のランダム行列を2つ生成し、行列積を計算してください。
結果行列の対角成分の合計を表示してください。
""",
        },
        {
            "id": 5,
            "name": "文字列処理",
            "prompt": """
Pythonでシーザー暗号（shift=3）を実装し、
"Hello World from Worker 5"を暗号化・復号化してください。
結果を表示してください。
""",
        },
    ]

    # 指定されたワーカー数に合わせてタスクを調整
    selected_tasks = tasks_list[:num_workers]

    print("タスク割り当て:")
    for task in selected_tasks:
        print(f"  Worker {task['id']}: {task['name']}")
    print()

    # タスクをカンマ区切り形式に変換
    task_names = [task["name"] for task in selected_tasks]
    combined_request = f"{', '.join(task_names)}の{num_workers}つのプログラムを作って"

    print("=" * 80)
    print("[ORCHESTRATOR] 並列実行開始")
    print("=" * 80)
    print(f"リクエスト: {combined_request}")
    print()
    print("[INFO] 各ワーカーの出力がリアルタイムで表示されます")
    print("[INFO] ワーカーIDで出力元を識別できます")
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(config=config, enable_realtime_monitoring=True)

    start_time = time.time()

    try:
        result = orchestrator.execute(combined_request)
        execution_time = time.time() - start_time

        print()
        print("=" * 80)
        print("実行完了 - 統計情報")
        print("=" * 80)
        print(f"総実行時間: {execution_time:.2f}秒")
        print()

        if result:
            print("[SUCCESS] すべてのワーカーが完了しました")
            print()

            # 各ワーカーの結果を表示
            workspace_path = Path(config.workspace_root)

            print("各ワーカーの結果:")
            print("-" * 80)

            for i, task in enumerate(selected_tasks, 1):
                worker_output = workspace_path / f"worker_{i}" / "output.txt"

                if worker_output.exists():
                    print(f"\n[Worker {i}: {task['name']}]")
                    with open(worker_output, "r", encoding="utf - 8") as f:
                        output = f.read()
                        # 最初の500文字のみ表示
                        if len(output) > 500:
                            print(output[:500] + "\n... (truncated)")
                        else:
                            print(output)
                else:
                    print(f"\n[Worker {i}: {task['name']}]")
                    print("  [ERROR] 出力ファイルが見つかりません")

            print("-" * 80)

            # パフォーマンス統計
            print()
            print("パフォーマンス統計:")
            print(f"  ワーカー数: {num_workers}")
            print(f"  総実行時間: {execution_time:.2f}秒")
            print(f"  平均処理時間 / ワーカー: {execution_time / num_workers:.2f}秒")
            print()
            print("[NOTE] 実際には並列実行されているため、")
            print("       総実行時間 < 平均処理時間 x ワーカー数")
            print("       となるはずです")

        else:
            print("[FAILED] 実行失敗")

    except Exception as e:
        print(f"\n[ERROR] エラー発生: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("テスト完了")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="真の並列実行テスト")
    parser.add_argument(
        "-w", "--workers", type=int, default=5, help="ワーカー数（1 - 5、デフォルト: 5）"
    )

    args = parser.parse_args()

    # ワーカー数を1 - 5に制限
    num_workers = max(1, min(5, args.workers))

    test_true_parallel_execution(num_workers=num_workers)
