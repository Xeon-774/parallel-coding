"""
高負荷並列実行テスト - 16 Workers

各Workerが計算集約的タスクを実行し、真の並列実行を検証します。
"""

import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure UTF-8 encoding BEFORE any output
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print

configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.structured_logging import StructuredLogger
from orchestrator.core.worker.worker_manager import WorkerManager


def generate_tasks(num_workers: int):
    """高負荷タスクを生成"""

    task_templates = [
        {
            "type": "fibonacci",
            "name": "Fibonacci Calculator",
            "prompt": """
あなたはWorkerAI #{worker_id}です。

【高負荷タスク: フィボナッチ数列】
以下のフィボナッチ数を計算してください：
- F(10) = ?
- F(15) = ?
- F(20) = ?

各結果を表示した後、"Fibonacci calculations completed!" と出力してください。
""",
        },
        {
            "type": "prime",
            "name": "Prime Number Finder",
            "prompt": """
あなたはWorkerAI #{worker_id}です。

【高負荷タスク: 素数探索】
以下の範囲で素数を見つけてください：
- 1から50までの素数をリストアップ
- 素数の個数をカウント
- 最大の素数を表示

完了したら "Prime search completed!" と出力してください。
""",
        },
        {
            "type": "text_processing",
            "name": "Text Processor",
            "prompt": """
あなたはWorkerAI #{worker_id}です。

【高負荷タスク: テキスト処理】
以下の処理を実行してください：
1. "Hello World" を10回繰り返して連結
2. その文字列の長さを計算
3. 文字 'o' の出現回数をカウント

結果を表示した後、"Text processing completed!" と出力してください。
""",
        },
        {
            "type": "list_operations",
            "name": "List Operations",
            "prompt": """
あなたはWorkerAI #{worker_id}です。

【高負荷タスク: リスト操作】
以下を実行してください：
1. 1から20までの数字のリストを作成
2. 各数字を2倍にした新しいリストを作成
3. その中から偶数のみをフィルタ
4. 合計を計算

結果を表示した後、"List operations completed!" と出力してください。
""",
        },
    ]

    tasks = []
    for i in range(num_workers):
        # タスクテンプレートを循環的に選択
        template = task_templates[i % len(task_templates)]

        task = {
            "name": f"{template['name']} #{i+1}",
            "prompt": template["prompt"].replace("{worker_id}", str(i + 1)),
        }
        tasks.append(task)

    return tasks


def main():
    """16 Workers 高負荷並列実行テスト"""

    safe_print("=" * 80)
    safe_print("高負荷並列実行テスト - 16 Workers")
    safe_print("=" * 80)
    safe_print()

    num_workers = 16

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "heavy_parallel_test")
    config.execution_mode = "wsl"
    config.wsl_distribution = "Ubuntu-24.04"
    config.claude_command = "~/.local/bin/claude"
    config.nvm_path = "/usr/bin"

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(name="heavy_parallel_test", log_dir=workspace, enable_console=True)

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # 自動承認モード
    )

    # タスク生成
    tasks = generate_tasks(num_workers)

    safe_print(f"\n[テスト] {num_workers}個のWorkerAIを並列起動中...")
    safe_print(f"[テスト] タスクタイプ: Fibonacci, Prime, TextProcessing, ListOps")
    safe_print(f"[テスト] Workspace: {config.workspace_root}\n")

    try:
        start_time = time.time()

        # 全WorkerAIを起動
        safe_print(f"[起動フェーズ] {num_workers}個のWorkerを起動中...")
        spawn_start = time.time()

        for i, task in enumerate(tasks):
            worker_id = f"heavy_worker_{i+1}"

            session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

            if not session:
                safe_print(f"[ERROR] Worker {i+1} の起動に失敗しました")
                return False

            if (i + 1) % 4 == 0:
                safe_print(f"  [{i+1}/{num_workers}] Workers 起動完了")

        spawn_time = time.time() - spawn_start
        safe_print(f"\n[起動完了] 全{num_workers}個のWorkerを起動 (所要時間: {spawn_time:.1f}秒)\n")

        # 並列実行
        safe_print(f"[実行フェーズ] {num_workers}個のWorkerを並列実行中...")
        safe_print(
            f"[注意] 各Workerが高負荷タスクを実行します。完了まで数分かかる場合があります。\n"
        )

        execution_start = time.time()
        results = worker_manager.wait_all(max_workers=16, timeout=600)
        execution_time = time.time() - execution_start

        total_time = time.time() - start_time

        # 結果分析
        safe_print("\n" + "=" * 80)
        safe_print("実行結果分析")
        safe_print("=" * 80)

        success_count = sum(1 for r in results if r.success)
        total_duration = sum(r.duration for r in results if r.duration)
        avg_duration = total_duration / len(results) if results else 0

        safe_print(f"総Worker数: {num_workers}")
        safe_print(f"成功したWorker: {success_count}/{len(results)}")
        safe_print(f"失敗したWorker: {len(results) - success_count}/{len(results)}")
        safe_print()
        safe_print(f"起動時間: {spawn_time:.1f}秒")
        safe_print(f"実行時間: {execution_time:.1f}秒")
        safe_print(f"合計時間: {total_time:.1f}秒")
        safe_print()
        safe_print(f"全Worker実行時間の合計: {total_duration:.1f}秒")
        safe_print(f"平均Worker実行時間: {avg_duration:.1f}秒")
        safe_print()

        # 並列効率の計算
        theoretical_sequential_time = total_duration
        actual_parallel_time = execution_time
        speedup = (
            theoretical_sequential_time / actual_parallel_time if actual_parallel_time > 0 else 0
        )
        efficiency = (speedup / num_workers) * 100 if num_workers > 0 else 0

        safe_print(f"理論的逐次実行時間: {theoretical_sequential_time:.1f}秒")
        safe_print(f"実際の並列実行時間: {actual_parallel_time:.1f}秒")
        safe_print(f"スピードアップ: {speedup:.2f}x")
        safe_print(f"並列効率: {efficiency:.1f}%")
        safe_print()

        # 詳細結果
        safe_print("=" * 80)
        safe_print("各Workerの詳細結果")
        safe_print("=" * 80)

        # タスクタイプ別に集計
        task_types = {}
        for i, result in enumerate(results):
            task_type = tasks[i]["name"].split("#")[0].strip()
            if task_type not in task_types:
                task_types[task_type] = {"success": 0, "fail": 0, "durations": []}

            if result.success:
                task_types[task_type]["success"] += 1
            else:
                task_types[task_type]["fail"] += 1

            if result.duration:
                task_types[task_type]["durations"].append(result.duration)

        for task_type, stats in task_types.items():
            avg_dur = sum(stats["durations"]) / len(stats["durations"]) if stats["durations"] else 0
            safe_print(f"\n[{task_type}]")
            safe_print(f"  成功: {stats['success']}, 失敗: {stats['fail']}")
            safe_print(f"  平均実行時間: {avg_dur:.1f}秒")

        # 最速・最遅Worker
        if results:
            sorted_results = sorted(results, key=lambda r: r.duration if r.duration else 0)
            fastest = sorted_results[0]
            slowest = sorted_results[-1]

            safe_print(f"\n最速Worker: {fastest.name} ({fastest.duration:.1f}秒)")
            safe_print(f"最遅Worker: {slowest.name} ({slowest.duration:.1f}秒)")

        safe_print("\n" + "=" * 80)

        if success_count == len(results):
            safe_print("\n✅ 全Workerが成功！高負荷並列実行テスト完全成功！")
            safe_print(f"16個のWorkerが同時に独立して高負荷タスクを実行しました。")
            safe_print(f"並列実行により約{speedup:.1f}倍の速度向上を達成しました。")
        elif success_count > len(results) * 0.8:
            safe_print(f"\n⚠️ 大半のWorkerが成功 ({success_count}/{len(results)})")
            safe_print("一部のWorkerで問題が発生しましたが、並列実行は機能しています。")
        else:
            safe_print(f"\n❌ 多くのWorkerが失敗しました ({success_count}/{len(results)})")
            safe_print("詳細を確認して問題を特定してください。")

        safe_print("=" * 80 + "\n")

        return success_count == len(results)

    except Exception as e:
        safe_print(f"\n[ERROR] テスト失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
