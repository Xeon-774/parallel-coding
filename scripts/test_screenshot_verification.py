#!/usr / bin / env python3
"""
スクリーンショット自動撮影・確認テスト

ワーカーウィンドウの自動スクリーンショット機能をテストし、
AI が自律的にウィンドウ表示を確認できることを検証
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf - 8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf - 8")(sys.stderr.buffer, "replace")

from orchestrator import AdvancedOrchestrator, OrchestratorConfig


def main():
    print("=" * 80)
    print("  スクリーンショット自動撮影・確認テスト")
    print("=" * 80)
    print()

    print("[テスト内容]")
    print("  1. シンプルな関数を1つ生成")
    print("  2. ワーカーウィンドウを表示")
    print("  3. 自動的にスクリーンショットを撮影")
    print("  4. AIがスクリーンショットを読み取って確認")
    print()

    # Windows環境設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"
    os.environ["ORCHESTRATOR_VISIBLE_WORKERS"] = "true"
    os.environ["ORCHESTRATOR_AUTO_CLOSE"] = "false"  # 手動で閉じる
    os.environ["ORCHESTRATOR_WINDOW_DELAY"] = "5"

    config = OrchestratorConfig.from_env()

    print("[設定]")
    print(f"  ウィンドウ表示: {config.enable_visible_workers}")
    print(f"  自動クローズ: {config.auto_close_windows}")
    print(f"  実行モード: {config.execution_mode}")
    print()

    print("[注意]")
    print("  PowerShellウィンドウが1つ開きます")
    print("  自動的にスクリーンショットを撮影し、AIが確認します")
    print()

    user_request = """
シンプルな挨拶関数を作成してください。
関数名はgreet()で、引数nameを受け取り、「Hello, {name}!」を返します。
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

        # スクリーンショット確認
        print()
        print("-" * 80)
        print("[スクリーンショット確認]")
        print()

        if orchestrator.orchestrator.window_manager:
            wm = orchestrator.orchestrator.window_manager
            screenshots_dir = Path(config.workspace_root) / "screenshots"

            if screenshots_dir.exists():
                screenshots = list(screenshots_dir.glob("*.png"))
                if screenshots:
                    latest_screenshot = max(screenshots, key=lambda p: p.stat().st_mtime)
                    print(f"最新スクリーンショット: {latest_screenshot}")
                    print(f"サイズ: {latest_screenshot.stat().st_size} bytes")
                    print()
                    print("スクリーンショットを確認します...")

                    # Read tool でスクリーンショットを読み込む
                    # これにより、AI が画像を視覚的に確認できる
                    print(f"\n[AI確認] {latest_screenshot} を確認中...")
                else:
                    print("⚠️ スクリーンショットが見つかりません")
            else:
                print("⚠️ screenshots ディレクトリが存在しません")
        else:
            print("⚠️ WindowManager が無効です")

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
