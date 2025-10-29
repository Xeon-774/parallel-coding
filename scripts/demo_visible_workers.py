#!/usr / bin / env python3
"""
ワーカーAIウィンドウ表示機能のデモ（v4.2）

各ワーカーAIを個別のウィンドウで表示し、
リアルタイムで進捗を可視化します。
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
    print("  ワーカーAIウィンドウ表示デモ（v4.2）")
    print("=" * 80)
    print()

    print("[新機能]")
    print("  ✨ 各ワーカーAIが個別のウィンドウで表示されます")
    print("  ✨ リアルタイムで出力を確認できます")
    print("  ✨ オーケストレーターが適切なタイミングでウィンドウを閉じます")
    print()

    print("[テストリクエスト]")
    user_request = """
3つのシンプルなPythonユーティリティを作成してください：

1. ファイルサイズフォーマッター（bytes → human readable）
2. 現在時刻フォーマッター（様々な形式）
3. カラーコードジェネレーター（ランダムな16進数カラー）

各ユーティリティは独立した関数として実装してください。
"""
    print(user_request)
    print()

    # Windows環境設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"
    os.environ["ORCHESTRATOR_VISIBLE_WORKERS"] = "true"  # ウィンドウ表示を有効化
    os.environ["ORCHESTRATOR_AUTO_CLOSE"] = "true"  # 自動クローズを有効化
    os.environ["ORCHESTRATOR_WINDOW_DELAY"] = "5"  # 5秒後に閉じる

    config = OrchestratorConfig.from_env()

    print("-" * 80)
    print()

    print("[設定]")
    print(f"  実行モード: {config.execution_mode}")
    print(f"  ウィンドウ表示: {config.enable_visible_workers}")
    print(f"  自動クローズ: {config.auto_close_windows}")
    print(f"  クローズ遅延: {config.window_close_delay}秒")
    print()

    print("[注意]")
    print("  複数のウィンドウが開きます。")
    print("  各ウィンドウでワーカーAIの動作がリアルタイムで表示されます。")
    print()

    print("[自動実行モード - 開始します]")
    print()

    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=True,  # AI分析を有効化
        enable_worktree=False,  # Worktreeは不要（単純なタスク）
        enable_realtime_monitoring=True,  # リアルタイム監視を有効化
    )

    print("[実行開始]")
    print()

    try:
        result = orchestrator.execute_with_advanced_analysis(user_request)

        print()
        print("-" * 80)
        print()

        if result:
            print("=" * 80)
            print("  🎉 完了！")
            print("=" * 80)
            print()

            print("[結果統計]")
            print(f"  総文字数: {len(result):,} 文字")
            print()

            print("[結果プレビュー（最初の1000文字）]")
            print("-" * 80)
            print(result[:1000])
            if len(result) > 1000:
                print(f"\n... (残り {len(result) - 1000:,} 文字)")
            print()

        else:
            print("❌ タスク実行に失敗しました")

    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("  デモ完了")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
