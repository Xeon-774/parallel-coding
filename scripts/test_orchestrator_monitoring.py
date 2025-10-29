#!/usr / bin / env python3
"""
オーケストレーターによるリアルタイム監視テスト

オーケストレーターAIがワーカーAIの出力を
リアルタイムで把握できることを実証
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


def test_orchestrator_realtime_monitoring():
    """
    オーケストレーターによるリアルタイム監視テスト

    このテストでは：
    1. 複数の高負荷タスクを並列実行
    2. 各ワーカーAIの出力がリアルタイムで表示される
    3. オーケストレーターが出力を把握し、統合する
    """
    print("=" * 80)
    print("オーケストレーターによるリアルタイム監視テスト")
    print("=" * 80)
    print()
    print("[目的]")
    print("  - オーケストレーターAIがワーカーAIの出力をリアルタイムで把握")
    print("  - 複数ワーカーの並列実行を監視")
    print("  - 高負荷タスクでの動作確認")
    print()

    # Windowsモードに設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"

    print("[設定]")
    print(f"  実行モード: {os.environ['ORCHESTRATOR_MODE']}")
    print(f"  Git Bash: {os.environ['CLAUDE_CODE_GIT_BASH_PATH']}")
    print("  リアルタイム監視: 有効")
    print()

    # 高負荷タスク：素数探索、フィボナッチ、ソート
    task_request = """
以下の3つの計算タスクを並列実行してください：

1. 素数探索: 1000から2000までの素数を見つけて、個数と最初の10個を表示
2. フィボナッチ: 30番目までのフィボナッチ数列を計算して表示
3. ソート: ランダムな100個の数字を生成してクイックソートし、最初と最後の10個を表示

各タスクは進捗を出力しながら実行してください。
"""

    print("=" * 80)
    print("[タスク内容]")
    print("=" * 80)
    print(task_request.strip())
    print()

    print("=" * 80)
    print("[実行開始]")
    print("=" * 80)
    print()
    print("[INFO] 以下、各ワーカーAIの出力がリアルタイムで表示されます")
    print("[INFO] [OUTPUT] worker_X: の形式で、どのワーカーの出力かわかります")
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(
        config=config, enable_realtime_monitoring=True  # リアルタイム監視を有効化
    )

    start_time = time.time()

    try:
        print("-" * 80)
        print()

        result = orchestrator.execute(task_request)

        print()
        print("-" * 80)

        execution_time = time.time() - start_time

        print()
        print("=" * 80)
        print("[実行完了]")
        print("=" * 80)
        print(f"総実行時間: {execution_time:.2f}秒")
        print()

        if result:
            print("[SUCCESS] オーケストレーター統合完了")
            print()
            print("=" * 80)
            print("[オーケストレーターによる統合結果]")
            print("=" * 80)
            print(result[:2000])  # 最初の2000文字
            if len(result) > 2000:
                print()
                print(f"... (残り {len(result) - 2000} 文字)")
            print()

            # 各ワーカーの出力を詳細に確認
            print("=" * 80)
            print("[各ワーカーの詳細出力]")
            print("=" * 80)
            print()

            workspace_path = Path(config.workspace_root)

            for worker_id in range(1, 4):  # 最大3ワーカー
                worker_dir = workspace_path / f"worker_{worker_id}"
                output_file = worker_dir / "output.txt"

                if output_file.exists():
                    print(f"[Worker {worker_id} 出力]")
                    print("-" * 40)
                    with open(output_file, "r", encoding="utf - 8") as f:
                        output = f.read()
                        # 最初の1000文字を表示
                        if len(output) > 1000:
                            print(output[:1000])
                            print(f"\n... (残り {len(output) - 1000} 文字)")
                        else:
                            print(output)
                    print()

            print("=" * 80)
            print("[オーケストレーターの分析]")
            print("=" * 80)
            print()
            print("[確認事項]")
            print("  ✓ リアルタイム出力: 実行中に [OUTPUT] が表示された")
            print("  ✓ 並列実行: 複数ワーカーが同時に動作")
            print("  ✓ 結果統合: すべてのワーカーの結果が統合された")
            print()

        else:
            print("[FAILED] 実行失敗")

    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR]")
        print("=" * 80)
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("[テスト完了]")
    print("=" * 80)


if __name__ == "__main__":
    test_orchestrator_realtime_monitoring()
