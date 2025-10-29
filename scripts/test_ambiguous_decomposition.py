#!/usr / bin / env python3
"""
曖昧なリクエストの自動分解テスト（v4.1）

AI駆動のタスク分解エンジンをテスト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF - 8出力設定
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf - 8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf - 8")(sys.stderr.buffer, "replace")

from orchestrator import AdvancedOrchestrator, OrchestratorConfig


def main():
    """メイン関数"""
    print("=" * 80)
    print("  AI駆動タスク分解テスト (v4.1)")
    print("=" * 80)
    print()

    print("[テスト内容]")
    print("  曖昧な大規模プロジェクトリクエストを、")
    print("  AI（Claude自身）が自律的にタスク分解できるかをテスト")
    print()

    # 曖昧なリクエスト
    request = """
シンプルなブログシステムを作成してください。

以下の機能が必要です：
- 記事の作成、編集、削除
- 記事の一覧表示
- シンプルなデータ保存（JSONファイル）

Pythonで実装してください。
"""

    print("[リクエスト]")
    print(request)
    print()

    # Windows環境設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\\opt\\Git.Git\\usr\\bin\\bash.exe"

    config = OrchestratorConfig.from_env()

    print("[期待される動作（v4.1）]")
    print("  ✅ AI分析: プロジェクトタイプを認識（web_app）")
    print("  ✅ AI分解: 複数のコンポーネントに自動分割")
    print("  ✅ 例: データモデル、記事管理、UI、ストレージ")
    print("  ✅ 並列実行")
    print("  ✅ 自動統合")
    print()

    print("-" * 80)
    print()

    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=True,  # AI分析有効
        enable_worktree=True,  # Worktree有効
        enable_realtime_monitoring=True,  # リアルタイム監視
    )

    try:
        result = orchestrator.execute_with_advanced_analysis(request)

        print()
        print("-" * 80)
        print()

        if result:
            print("✅ テスト成功！")
            print()

            # ワーカー数を確認
            workspace_path = Path(config.workspace_root)
            worker_count = sum(1 for item in workspace_path.glob("worker_*") if item.is_dir())

            print("[検証結果]")
            print(f"  生成されたワーカー数: {worker_count}")
            print()

            if worker_count > 1:
                print("  🎉 成功！AI分析により複数タスクに自動分解されました！")
                print(f"  → {worker_count}個のコンポーネントが並列実行されました")
            elif worker_count == 1:
                print("  ℹ️ AI判断: 単一タスクとして扱われました")
                print("  → プロジェクトが十分シンプルと判断された可能性")
            print()

            print("[結果サマリー（最初の800文字）]")
            print(result[:800])
            if len(result) > 800:
                print(f"\n... (残り {len(result) - 800} 文字)")
            print()

        else:
            print("❌ テスト失敗")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("  テスト完了")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
