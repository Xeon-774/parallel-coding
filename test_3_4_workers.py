"""
3-4 WorkerAI並列実行テスト

より実践的なタスクで並列実行のスケーラビリティを検証します。
- Worker 1: ファイル分析
- Worker 2: コード生成
- Worker 3: データ処理
- Worker 4: ドキュメント生成（オプション）
"""

import sys
from pathlib import Path
import time

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure UTF-8 encoding BEFORE any output
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print
configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker.worker_manager import WorkerManager
from orchestrator.core.structured_logging import StructuredLogger


def get_task_definitions(num_workers=3):
    """
    タスク定義を取得

    Args:
        num_workers: 実行するWorker数（3または4）

    Returns:
        タスク定義のリスト
    """
    tasks = [
        {
            "name": "File Analyzer",
            "prompt": """
あなたはWorkerAI #1です。

【タスク】
以下のテキストファイルの内容を分析してください：

ファイル名: sample_data.txt
内容:
---
Project: AI_Investor
Status: Active
Features:
- Parallel AI Coding
- Economic Indicators Scraper
- News Monitoring
- Multi-tier Cache Strategy
---

以下を出力してください：
1. プロジェクト名
2. ステータス
3. 機能の数
4. 全機能のリスト

完了したら "File analysis completed!" と出力してください。
"""
        },
        {
            "name": "Code Generator",
            "prompt": """
あなたはWorkerAI #2です。

【タスク】
以下の仕様に基づいてPython関数を生成してください：

関数名: calculate_roi
引数: revenue (float), cost (float)
戻り値: ROI (Return on Investment) をパーセンテージで返す
計算式: ((revenue - cost) / cost) * 100

関数のコードを生成し、3つのテストケースを実行してください：
1. revenue=1000, cost=500 → 期待値: 100.0
2. revenue=1500, cost=1000 → 期待値: 50.0
3. revenue=800, cost=1000 → 期待値: -20.0

完了したら "Code generation completed!" と出力してください。
"""
        },
        {
            "name": "Data Processor",
            "prompt": """
あなたはWorkerAI #3です。

【タスク】
以下のJSON形式のデータを処理してください：

```json
{
  "users": [
    {"id": 1, "name": "Alice", "age": 25, "purchases": 5},
    {"id": 2, "name": "Bob", "age": 30, "purchases": 12},
    {"id": 3, "name": "Charlie", "age": 35, "purchases": 8},
    {"id": 4, "name": "Diana", "age": 28, "purchases": 15},
    {"id": 5, "name": "Eve", "age": 22, "purchases": 3}
  ]
}
```

以下の統計を計算してください：
1. 合計ユーザー数
2. 平均年齢（小数点第1位まで）
3. 合計購入数
4. 最も購入数が多いユーザー名

完了したら "Data processing completed!" と出力してください。
"""
        }
    ]

    # 4 Worker版の場合、ドキュメント生成タスクを追加
    if num_workers == 4:
        tasks.append({
            "name": "Doc Generator",
            "prompt": """
あなたはWorkerAI #4です。

【タスク】
以下の内容を含むMarkdown形式のREADMEを生成してください：

プロジェクト名: Parallel AI Coding System
バージョン: v10.0
目的: 複数のAIエージェントが並列でコーディングタスクを実行

以下のセクションを含めてください：
1. # Overview - プロジェクトの概要（2-3文）
2. ## Features - 主要機能を箇条書き（3つ）
3. ## Quick Start - 簡単な使い方の例

完了したら "Documentation completed!" と出力してください。
"""
        })

    return tasks


def main(num_workers=3):
    """
    並列実行テスト

    Args:
        num_workers: 実行するWorker数（3または4）
    """

    safe_print("=" * 80)
    safe_print(f"{num_workers} WorkerAI並列実行テスト")
    safe_print("=" * 80)
    safe_print()

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / f"test_{num_workers}_workers")
    config.execution_mode = "wsl"
    config.wsl_distribution = "Ubuntu-24.04"
    config.claude_command = "~/.local/bin/claude"
    config.nvm_path = "/usr/bin"

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(
        name=f"test_{num_workers}_workers",
        log_dir=workspace,
        enable_console=True
    )

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config,
        logger=logger,
        user_approval_callback=None  # 自動承認モード
    )

    # タスク定義取得
    tasks = get_task_definitions(num_workers)

    try:
        safe_print(f"\n[テスト] {num_workers}個のWorkerAIを並列起動中...")
        safe_print(f"[テスト] Workspace: {config.workspace_root}\n")

        start_time = time.time()

        # 全WorkerAIを起動
        for i, task in enumerate(tasks):
            worker_id = f"worker_{i+1}"
            safe_print(f"[起動] Worker {i+1}: {task['name']}")

            session = worker_manager.spawn_worker(
                worker_id=worker_id,
                task=task
            )

            if not session:
                safe_print(f"[ERROR] Worker {i+1} の起動に失敗しました")
                return False

        safe_print(f"\n[テスト] {num_workers}個のWorkerを並列実行中...\n")

        # 並列実行
        results = worker_manager.wait_all(max_workers=num_workers, timeout=300)

        total_time = time.time() - start_time

        # 結果表示
        safe_print("\n" + "=" * 80)
        safe_print("実行結果")
        safe_print("=" * 80)
        safe_print(f"総実行時間: {total_time:.1f}秒")
        safe_print(f"完了したWorker数: {len(results)}/{num_workers}")
        safe_print()

        success_count = 0
        individual_times = []

        for i, result in enumerate(results):
            safe_print(f"\n--- Worker {i+1}: {result.name} ---")
            safe_print(f"成功: {'✅' if result.success else '❌'} {result.success}")

            if result.duration:
                safe_print(f"実行時間: {result.duration:.1f}秒")
                individual_times.append(result.duration)
            else:
                safe_print("実行時間: N/A")

            if result.success:
                success_count += 1

            if result.output:
                safe_print(f"\n出力（最後の400文字）:")
                safe_print("-" * 70)
                safe_print(result.output[-400:])
                safe_print("-" * 70)

            if result.error_message:
                safe_print(f"\nエラー: {result.error_message}")

        # パフォーマンス分析
        safe_print("\n" + "=" * 80)
        safe_print("パフォーマンス分析")
        safe_print("=" * 80)
        safe_print(f"成功率: {success_count}/{num_workers} ({success_count/num_workers*100:.1f}%)")

        if individual_times:
            avg_time = sum(individual_times) / len(individual_times)
            max_time = max(individual_times)
            sequential_time = sum(individual_times)

            safe_print(f"\n個別実行時間:")
            for i, t in enumerate(individual_times):
                safe_print(f"  Worker {i+1}: {t:.1f}秒")

            safe_print(f"\n平均実行時間: {avg_time:.1f}秒")
            safe_print(f"最大実行時間: {max_time:.1f}秒")
            safe_print(f"\n逐次実行予測時間: {sequential_time:.1f}秒")
            safe_print(f"並列実行実時間: {total_time:.1f}秒")
            safe_print(f"時間短縮: {sequential_time - total_time:.1f}秒 ({(1 - total_time/sequential_time)*100:.1f}%削減)")
            safe_print(f"並列効率: {sequential_time/total_time:.2f}x （理想値: {num_workers:.0f}x）")

        safe_print("\n" + "=" * 80)

        if success_count == num_workers:
            safe_print(f"\n✅ {num_workers} Worker並列実行テスト成功！")
            safe_print(f"{num_workers}個のWorkerAIが同時に独立したタスクを完了しました。")
        else:
            safe_print(f"\n⚠️ 一部のWorkerが失敗しました ({success_count}/{num_workers})。")

        safe_print("=" * 80 + "\n")

        return success_count == num_workers

    except Exception as e:
        safe_print(f"\n[ERROR] テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='3-4 WorkerAI並列実行テスト')
    parser.add_argument('--workers', type=int, choices=[3, 4], default=3,
                        help='実行するWorker数（3または4、デフォルト: 3）')

    args = parser.parse_args()

    success = main(num_workers=args.workers)
    sys.exit(0 if success else 1)