"""
OrchestratorAI ⇄ WorkerAI 対話テスト

既存のWorkerManager（v10.0）を使用して、
OrchestratorとWorkerAIの対話が正しく機能するかテストします。

テスト内容:
1. WorkerAI起動
2. WorkerAIからの確認パターン検出
3. 自動承認（AISafetyJudge）
4. タスク継続
5. 結果取得
"""

import os
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.structured_logging import StructuredLogger
from orchestrator.core.worker.worker_manager import WorkerManager


def test_simple_file_creation():
    """
    テスト1: シンプルなファイル作成タスク

    WorkerAIがファイル書き込み確認を送信
    → OrchestratorAIが自動承認
    → WorkerAIが作業継続
    """
    print("=" * 70)
    print("テスト1: シンプルなファイル作成タスク")
    print("=" * 70)

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "test_interaction")
    config.execution_mode = "windows"  # Windowsモード
    config.windows_claude_path = "claude"  # Claude CLI使用
    config.git_bash_path = r"C:\opt\Git.Git\usr\bin\bash.exe"  # git-bash設定

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(name="test_logger", log_dir=workspace, enable_console=True)

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # 自動承認モード
    )

    # タスク定義
    task = {
        "name": "Simple File Creation",
        "prompt": """
あなたはWorkerAIです。以下のタスクを実行してください：

【タスク】
1. テキストファイル "test_output.txt" を作成
2. 内容: "Hello from WorkerAI! Task completed successfully."
3. ファイルが作成されたことを確認
4. 完了を報告

【重要】
- Writeツールを使用してファイルを作成してください
- 確認パターンが発生したら、それに従ってください
- 作業が完了したら "TASK COMPLETED" と出力してください

開始してください。
""",
    }

    try:
        print("\n[Test] WorkerAI起動中...")
        print(f"[Test] Workspace: {config.workspace_root}")

        # WorkerAI起動
        worker_id = "test_worker_1"

        # Step 1: Spawn worker
        session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

        if not session:
            print("[ERROR] Failed to spawn worker")
            return False

        # Step 2: Run interactive session (use session.worker_id)
        result = worker_manager.run_interactive_session(session.worker_id)

        print("\n" + "=" * 70)
        print("テスト結果")
        print("=" * 70)
        print(f"成功: {result.success}")
        print(f"Worker ID: {result.worker_id}")
        if result.duration:
            print(f"実行時間: {result.duration:.1f}秒")

        if result.output:
            print("\n--- 出力内容（最後の500文字） ---")
            print(result.output[-500:])
            print("--- 出力終了 ---")

        if result.error_message:
            print(f"\nエラー: {result.error_message}")

        # 作成されたファイルを確認
        test_file = workspace / "test_output.txt"
        if test_file.exists():
            print(f"\n[OK] ファイル作成成功: {test_file}")
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"内容: {content}")
        else:
            print(f"\n[ERROR] ファイルが作成されませんでした: {test_file}")

        print("\n" + "=" * 70)

        return result.success

    except Exception as e:
        print(f"\n[ERROR] テスト失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_interactive_task():
    """
    テスト2: 対話型タスク（複数の確認パターン）

    WorkerAIが複数の確認を送信
    → OrchestratorAIが各確認に応答
    → WorkerAIが段階的に作業を進める
    """
    print("\n" + "=" * 70)
    print("テスト2: 対話型タスク（複数の確認パターン）")
    print("=" * 70)

    # 設定
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "test_interaction_2")
    config.execution_mode = "windows"
    config.windows_claude_path = "claude"  # Claude CLI使用
    config.git_bash_path = r"C:\opt\Git.Git\usr\bin\bash.exe"  # git-bash設定

    # ワークスペース準備
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # ロガー
    logger = StructuredLogger(name="test_logger", log_dir=workspace, enable_console=True)

    # WorkerManager初期化
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # 自動承認モード
    )

    # タスク定義
    task = {
        "name": "Interactive Task",
        "prompt": """
あなたはWorkerAIです。以下のタスクを段階的に実行してください：

【タスク】
1. ディレクトリ "test_dir" を作成
2. その中にファイル "step1.txt" を作成（内容: "Step 1 completed"）
3. その中にファイル "step2.txt" を作成（内容: "Step 2 completed"）
4. 作成されたファイルをリストアップ
5. 完了を報告

【重要】
- 各ステップでWriteツールを使用してください
- 確認パターンが発生したら、それに従ってください
- 各ステップ完了後、"Step N completed" と出力してください
- 全て完了したら "ALL TASKS COMPLETED" と出力してください

開始してください。
""",
    }

    try:
        print("\n[Test] WorkerAI起動中...")
        print(f"[Test] Workspace: {config.workspace_root}")

        # WorkerAI起動
        worker_id = "test_worker_2"

        # Step 1: Spawn worker
        session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

        if not session:
            print("[ERROR] Failed to spawn worker")
            return False

        # Step 2: Run interactive session (use session.worker_id)
        result = worker_manager.run_interactive_session(session.worker_id)

        print("\n" + "=" * 70)
        print("テスト結果")
        print("=" * 70)
        print(f"成功: {result.success}")
        print(f"Worker ID: {result.worker_id}")
        if result.duration:
            print(f"実行時間: {result.duration:.1f}秒")

        if result.output:
            print("\n--- 出力内容（最後の1000文字） ---")
            print(result.output[-1000:])
            print("--- 出力終了 ---")

        # 作成されたファイルを確認
        test_dir = workspace / "test_dir"
        if test_dir.exists():
            print(f"\n[OK] ディレクトリ作成成功: {test_dir}")

            step1 = test_dir / "step1.txt"
            step2 = test_dir / "step2.txt"

            if step1.exists():
                with open(step1, "r") as f:
                    print(f"  [OK] step1.txt: {f.read()}")
            else:
                print(f"  [ERROR] step1.txt が作成されませんでした")

            if step2.exists():
                with open(step2, "r") as f:
                    print(f"  [OK] step2.txt: {f.read()}")
            else:
                print(f"  [ERROR] step2.txt が作成されませんでした")
        else:
            print(f"\n[ERROR] ディレクトリが作成されませんでした: {test_dir}")

        print("\n" + "=" * 70)

        return result.success

    except Exception as e:
        print(f"\n[ERROR] テスト失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """全テストを実行"""
    print("\n")
    print("=" * 70)
    print("  OrchestratorAI <-> WorkerAI 対話テスト")
    print("=" * 70)
    print("\n")

    results = []

    # テスト1
    test1_result = test_simple_file_creation()
    results.append(("シンプルなファイル作成", test1_result))

    time.sleep(2)  # テスト間の待機

    # テスト2
    test2_result = test_interactive_task()
    results.append(("対話型タスク", test2_result))

    # 結果サマリー
    print("\n")
    print("=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)

    for test_name, success in results:
        status = "[OK] 成功" if success else "[ERROR] 失敗"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] 全テスト成功！OrchestratorAI <-> WorkerAI 対話が正常に機能しています。")
    else:
        print("[WARNING] 一部のテストが失敗しました。詳細を確認してください。")
    print("=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
