"""
シンプルなWorkerAIテスト

既存のWorkerManagerを使ってWorkerAIが起動・実行できることを確認
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker.worker_manager import WorkerManager
from orchestrator.core.structured_logging import StructuredLogger


def test_worker():
    """WorkerAI起動・実行テスト"""

    print("=" * 70)
    print("WorkerAI起動テスト")
    print("=" * 70)

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "test_simple")
    config.execution_mode = "windows"
    config.windows_claude_path = "claude"  # Claude CLI使用
    config.git_bash_path = r"C:\opt\Git.Git\usr\bin\bash.exe"  # git-bash設定

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(
        name="simple_test",
        log_dir=workspace,
        enable_console=True
    )

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config,
        logger=logger,
        user_approval_callback=None  # 自動承認モード
    )

    # タスク定義
    task = {
        "name": "Simple Test",
        "prompt": """
あなたはWorkerAIのテストです。

以下を実行してください:
1. "Hello from WorkerAI!" と出力
2. 簡単な計算: 123 + 456 = ?
3. "Test completed!" と出力

開始してください。
"""
    }

    try:
        print("\n[Test] WorkerAI起動中...")
        print(f"[Test] Workspace: {config.workspace_root}\n")

        # WorkerAI起動
        worker_id = "simple_test_worker"

        session = worker_manager.spawn_worker(
            worker_id=worker_id,
            task=task
        )

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

        if result.output:
            print(f"\n出力（最後の500文字）:")
            print("-" * 70)
            print(result.output[-500:])
            print("-" * 70)

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


if __name__ == '__main__':
    success = test_worker()
    sys.exit(0 if success else 1)
