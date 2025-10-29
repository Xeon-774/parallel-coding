#!/usr/bin/env python3
"""
シンプルなウィンドウテスト

1つのワーカーのみでウィンドウ表示をテスト
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")

from orchestrator import AdvancedOrchestrator, OrchestratorConfig


def main():
    print("=" * 80)
    print("  シンプルウィンドウテスト")
    print("=" * 80)
    print()

    print("[テスト内容]")
    print("  シンプルなHello World関数を1つだけ生成")
    print("  ウィンドウが1つ開くことを確認")
    print()

    # Windows環境設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"
    os.environ["ORCHESTRATOR_VISIBLE_WORKERS"] = "true"
    os.environ["ORCHESTRATOR_AUTO_CLOSE"] = "false"  # 手動で閉じる
    os.environ["ORCHESTRATOR_WINDOW_DELAY"] = "10"

    config = OrchestratorConfig.from_env()

    print("[設定]")
    print(f"  ウィンドウ表示: {config.enable_visible_workers}")
    print(f"  自動クローズ: {config.auto_close_windows}")
    print()

    print("[注意]")
    print("  PowerShellウィンドウが1つ開きます")
    print("  ウィンドウで「Press any key to close」と表示されたらキーを押してください")
    print()

    user_request = """
シンプルなHello World関数を作成してください。
関数名はgreet()で、引数nameを受け取り、挨拶メッセージを返します。
"""

    print(f"[リクエスト]: {user_request.strip()}")
    print()

    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=False,  # AI分析は無効（シンプルに1タスク）
        enable_worktree=False,
        enable_realtime_monitoring=True,
    )

    print("[実行開始]")
    print()

    try:
        result = orchestrator.execute(user_request)

        print()
        print("-" * 80)
        print()

        if result:
            print("✅ 成功！")
            print(f"生成コード: {len(result)} 文字")
            print()
            print(result[:500])
        else:
            print("❌ 失敗")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("  テスト完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
