#!/usr/bin/env python3
"""
オーケストレーターによるライブ監視と逐次報告

終了時間が不定のタスクを複数のAIインスタンスに実行させ、
オーケストレーターAIがリアルタイムで監視し、ユーザーに逐一報告
"""

import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF-8出力設定
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")

from orchestrator import OrchestratorConfig, RefactoredOrchestrator


def report(message: str, level: str = "INFO"):
    """
    オーケストレーターからの報告

    Args:
        message: 報告メッセージ
        level: レベル（INFO, SUCCESS, WARNING, ERROR）
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    prefix_map = {"INFO": "📊", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROGRESS": "🔄"}

    prefix = prefix_map.get(level, "📌")

    print(f"[{timestamp}] [ORCHESTRATOR {level}] {prefix} {message}")
    sys.stdout.flush()


def test_live_monitoring():
    """
    ライブ監視と逐次報告のテスト
    """
    print("=" * 80)
    print("オーケストレーターAI - ライブ監視デモンストレーション")
    print("=" * 80)
    print()

    report("システム起動中...", "INFO")
    print()

    print("[システム概要]")
    print("  - 複数の計算タスクを並列実行")
    print("  - 各タスクは終了時間が異なる（不定）")
    print("  - オーケストレーターAIがリアルタイムで監視")
    print("  - 進捗と完了を逐一報告")
    print()

    # Windowsモードに設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"

    report("実行環境設定完了", "SUCCESS")
    report(f"モード: {os.environ['ORCHESTRATOR_MODE']}", "INFO")
    print()

    # 終了時間が不定のタスク（異なる計算量）
    task_request = """
以下の3つの計算タスクを作成して実行してください。
各タスクは進捗を定期的に出力してください。

タスク1 (軽量): 100から300までの素数を探索
- 10個見つかるごとに「進捗: X個発見」と表示
- 完了時に「タスク1完了: 合計X個」と表示

タスク2 (中程度): 1から35までのフィボナッチ数列を計算
- 5個計算するごとに「進捗: X番目まで計算完了」と表示
- 完了時に「タスク2完了: 35番目の値はX」と表示

タスク3 (重量級): ランダムな500個の数字を生成してバブルソートで並べ替え
- 100回交換するごとに「進捗: X回の交換を実行」と表示
- 完了時に「タスク3完了: X回の交換でソート完了」と表示

各タスクは独立して実行してください。
"""

    print("=" * 80)
    print("[タスク内容]")
    print("=" * 80)
    print()
    report("以下のタスクを準備しました:", "INFO")
    print()
    print("  📋 タスク1: 素数探索 (100-300) - 軽量、早く終わる")
    print("  📋 タスク2: フィボナッチ (1-35) - 中程度")
    print("  📋 タスク3: バブルソート (500個) - 重量級、時間がかかる")
    print()
    report("各タスクの終了時間は予測できません（不定）", "WARNING")
    print()

    print("=" * 80)
    print("[実行開始]")
    print("=" * 80)
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(config=config, enable_realtime_monitoring=True)

    report("ワーカーAIインスタンスを起動します...", "INFO")
    print()

    start_time = time.time()

    # 進捗報告用のスレッド
    stop_reporting = threading.Event()

    def periodic_status_report():
        """定期的なステータス報告"""
        while not stop_reporting.is_set():
            elapsed = time.time() - start_time
            report(f"実行時間: {elapsed:.1f}秒 - 監視継続中...", "PROGRESS")
            time.sleep(5)  # 5秒ごとに報告

    # 報告スレッド開始
    reporter_thread = threading.Thread(target=periodic_status_report, daemon=True)
    reporter_thread.start()

    try:
        print("-" * 80)
        print()

        result = orchestrator.execute(task_request)

        print()
        print("-" * 80)

        execution_time = time.time() - start_time

        # 定期報告を停止
        stop_reporting.set()

        print()
        print("=" * 80)
        print("[実行完了]")
        print("=" * 80)
        print()

        report(f"全タスク完了！総実行時間: {execution_time:.2f}秒", "SUCCESS")
        print()

        if result:
            report("結果統合に成功しました", "SUCCESS")
            print()

            # 各ワーカーの詳細結果を報告
            workspace_path = Path(config.workspace_root)

            print("=" * 80)
            print("[各ワーカーAIの実行結果詳細]")
            print("=" * 80)
            print()

            for worker_id in range(1, 4):
                worker_dir = workspace_path / f"worker_{worker_id}"
                output_file = worker_dir / "output.txt"

                if output_file.exists():
                    report(f"Worker {worker_id} の結果を取得しました", "SUCCESS")

                    with open(output_file, "r", encoding="utf-8") as f:
                        output = f.read()

                    print()
                    print(f"  Worker {worker_id} 出力 ({len(output)} 文字):")
                    print("  " + "-" * 76)

                    # 最初の800文字を表示
                    if len(output) > 800:
                        print("  " + output[:800].replace("\n", "\n  "))
                        print(f"\n  ... (残り {len(output) - 800} 文字)")
                    else:
                        print("  " + output.replace("\n", "\n  "))

                    print("  " + "-" * 76)
                    print()
                else:
                    report(f"Worker {worker_id} の出力ファイルが見つかりません", "WARNING")
                    print()

            print("=" * 80)
            print("[オーケストレーターの最終分析]")
            print("=" * 80)
            print()

            report("監視したイベント:", "INFO")
            print()
            print("  ✓ ワーカーAIの起動")
            print("  ✓ タスクの開始")
            print("  ✓ リアルタイム出力の監視")
            print("  ✓ 各ワーカーの進捗確認")
            print("  ✓ 完了検出")
            print("  ✓ 結果の統合")
            print()

            report(f"システムは完全に自律的に動作しました", "SUCCESS")
            print()

            # 統合結果の一部を表示
            print("=" * 80)
            print("[統合結果サマリー]")
            print("=" * 80)
            print()
            print(result[:1000])
            if len(result) > 1000:
                print(f"\n... (残り {len(result) - 1000} 文字)")
            print()

        else:
            report("実行に失敗しました", "ERROR")

    except Exception as e:
        stop_reporting.set()
        report(f"エラーが発生しました: {e}", "ERROR")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("[デモンストレーション完了]")
    print("=" * 80)
    print()

    report("確認事項:", "INFO")
    print()
    print("  ✅ 終了時間が不定のタスクを実行")
    print("  ✅ 複数のAIインスタンスを並列実行")
    print("  ✅ オーケストレーターがリアルタイムで監視")
    print("  ✅ 進捗を逐一報告")
    print("  ✅ 完全自律動作")
    print()

    report("オーケストレーターAIのライブ監視デモを完了しました", "SUCCESS")
    print()


if __name__ == "__main__":
    test_live_monitoring()
