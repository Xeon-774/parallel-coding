"""
並列AI Coding機能のデモテスト

2つのWorkerAIを並列実行して、それぞれが独立したタスクを完了することを確認します。
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


def main():
    """並列実行デモ"""

    safe_print("=" * 80)
    safe_print("AI並列コーディング機能デモ")
    safe_print("=" * 80)
    safe_print()

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "parallel_demo")
    config.execution_mode = "wsl"
    config.wsl_distribution = "Ubuntu-24.04"
    config.claude_command = "~/.local/bin/claude"
    config.nvm_path = "/usr/bin"

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(name="parallel_demo", log_dir=workspace, enable_console=True)

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # 自動承認モード
    )

    # タスク定義
    tasks = [
        {
            "name": "Math Calculator",
            "prompt": """
あなたはWorkerAI #1です。

【タスク】
以下の計算を実行して結果を出力してください：
1. 123 + 456 = ?
2. 789 × 12 = ?
3. 1000 ÷ 25 = ?

各計算結果を表示した後、"Math calculations completed!" と出力してください。
""",
        },
        {
            "name": "Text Generator",
            "prompt": """
あなたはWorkerAI #2です。

【タスク】
以下の文章を生成してください：
1. "Hello from Parallel AI Worker #2"
2. "Testing concurrent execution"
3. 1から5までの数字をリストで表示

全て完了したら "Text generation completed!" と出力してください。
""",
        },
    ]

    try:
        safe_print("\n[デモ] WorkerAIを並列起動中...")
        safe_print(f"[デモ] タスク数: {len(tasks)}")
        safe_print(f"[デモ] Workspace: {config.workspace_root}\n")

        start_time = time.time()

        # 全WorkerAIを起動
        for i, task in enumerate(tasks):
            worker_id = f"demo_worker_{i+1}"
            safe_print(f"[起動] Worker {i+1}: {task['name']}")

            session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

            if not session:
                safe_print(f"[ERROR] Worker {i+1} の起動に失敗しました")
                return False

        safe_print("\n[デモ] 全Workerを並列実行中...\n")

        # 並列実行 (wait_allが並列実行を行う)
        results = worker_manager.wait_all(max_workers=2, timeout=300)

        total_time = time.time() - start_time

        # 結果表示
        safe_print("\n" + "=" * 80)
        safe_print("実行結果")
        safe_print("=" * 80)
        safe_print(f"総実行時間: {total_time:.1f}秒")
        safe_print(f"完了したWorker数: {len(results)}")
        safe_print()

        success_count = 0
        for i, result in enumerate(results):
            safe_print(f"\n--- Worker {i+1}: {result.name} ---")
            safe_print(f"成功: {result.success}")
            safe_print(f"実行時間: {result.duration:.1f}秒" if result.duration else "実行時間: N/A")

            if result.success:
                success_count += 1

            if result.output:
                safe_print(f"\n出力（最後の300文字）:")
                safe_print("-" * 70)
                safe_print(result.output[-300:])
                safe_print("-" * 70)

            if result.error_message:
                safe_print(f"\nエラー: {result.error_message}")

        safe_print("\n" + "=" * 80)
        safe_print(f"成功率: {success_count}/{len(results)}")

        if success_count == len(results):
            safe_print("\n✅ 並列実行テスト成功！")
            safe_print("複数のWorkerAIが同時に独立したタスクを完了しました。")
        else:
            safe_print("\n⚠️ 一部のWorkerが失敗しました。")

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
