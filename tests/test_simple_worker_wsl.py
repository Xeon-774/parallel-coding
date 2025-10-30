"""
シンプルなWorkerAIテスト (WSLモード)

既存のWorkerManagerを使ってWorkerAIが起動・実行できることを確認
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure UTF - 8 encoding BEFORE any output
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print

configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.structured_logging import StructuredLogger
from orchestrator.core.worker.worker_manager import WorkerManager


def test_worker():
    """WorkerAI起動・実行テスト (WSL)"""

    print("=" * 70)
    print("WorkerAI起動テスト (WSL Mode)")
    print("=" * 70)

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "test_simple_wsl")
    config.execution_mode = "wsl"  # WSLモード
    config.wsl_distribution = "Ubuntu - 24.04"  # WSLディストリビューション名
    config.claude_command = "~/.local / bin / claude"  # Claude CLI パス
    config.nvm_path = "/usr / bin"  # PATH設定（~/.local / binはシェルで展開される）

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(name="simple_test_wsl", log_dir=workspace, enable_console=True)

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # 自動承認モード
    )

    # タスク定義
    task = {
        "name": "Simple Test WSL",
        "prompt": """
あなたはWorkerAIのテストです。

以下を実行してください:
1. "Hello from WorkerAI (WSL)!" と出力
2. 簡単な計算: 123 + 456 = ?
3. "Test completed!" と出力

開始してください。
""",
    }

    try:
        print("\n[Test] WorkerAI起動中...")
        print("[Test] Mode: WSL")
        print(f"[Test] Distribution: {config.wsl_distribution}")
        print(f"[Test] Workspace: {config.workspace_root}\n")

        # WorkerAI起動
        worker_id = "simple_test_worker_wsl"

        session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

        if not session:
            print("[ERROR] Failed to spawn worker")
            return False

        # 実行 (spawn_workerが返すsession.worker_idを使用)
        result = worker_manager.run_interactive_session(session.worker_id)

        # 結果表示
        print("\n" + "=" * 70)
        print("テスト結果")
        print("=" * 70)
        print(f"成功: {result.success}")
        print(f"Worker ID: {result.worker_id}")

        if result.duration:
            print(f"実行時間: {result.duration:.1f}秒")

        if result.output:
            # 出力をファイルに保存 (UTF - 8 with BOM)
            output_file = workspace / "worker_output.txt"
            with open(output_file, "w", encoding="utf - 8 - sig") as f:
                f.write(result.output)
            safe_print(f"\n出力を保存しました: {output_file}")
            safe_print(f"出力長: {len(result.output)} 文字")

            # 出力の最後の部分を表示（UTF - 8対応）
            try:
                output_preview = result.output[-500:]
                safe_print("\n出力プレビュー（最後の500文字）:")
                safe_print("-" * 70)
                safe_print(output_preview)
                safe_print("-" * 70)
            except Exception as e:
                safe_print(f"[WARNING] 出力表示エラー: {e}")

        if result.error_message:
            print(f"\nエラー: {result.error_message}")

        print("\n" + "=" * 70)

        if result.success:
            print("[SUCCESS] WorkerAI起動・実行成功！")
            print("OrchestratorAI <-> WorkerAI 対話が正常に機能しています。")
        else:
            print("[WARNING] WorkerAI実行が成功しませんでした。")
            print("詳細を確認してください。")

        print("=" * 70)

        return result.success

    except Exception as e:
        print(f"\n[ERROR] テスト失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_worker()
    sys.exit(0 if success else 1)
