#!/usr/bin/env python3
"""
Claude CLI トークン設定スクリプト

使用方法:
1. https://claude.ai/settings/developer でトークンを生成
2. このスクリプトを実行してトークンを入力

または、環境変数/ファイルを使用:
  export CLAUDE_API_TOKEN="your-token-here"
  # または
  echo "your-token-here" > ~/.claude_token
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator.utils import setup_claude_token, get_token_from_env_or_file


def main():
    print("=" * 70)
    print("Claude CLI 認証トークン設定")
    print("=" * 70)
    print()

    # 既存のトークンをチェック
    existing_token = get_token_from_env_or_file()

    if existing_token:
        print()
        use_existing = input("既存のトークンを使用しますか？ (Y/n): ").strip().lower()
        if use_existing in ('', 'y', 'yes'):
            token = existing_token
        else:
            token = None
    else:
        token = None

    # トークンを入力
    if token is None:
        print()
        print("Claude APIトークンの取得方法:")
        print("  1. https://claude.ai/settings/developer にアクセス")
        print("  2. 'Create Long-Lived Session Token' をクリック")
        print("  3. トークンをコピー")
        print()

        token = input("トークンを貼り付けてください: ").strip()

        if not token:
            print()
            print("❌ トークンが入力されませんでした。")
            return False

    # 実行モードを選択
    print()
    print("実行モード:")
    print("  1. WSL (推奨 - Windows上のLinux環境)")
    print("  2. Windows ネイティブ")
    print()

    mode_choice = input("選択してください (1/2) [1]: ").strip() or "1"

    if mode_choice == "1":
        execution_mode = "wsl"
        dist = input("WSLディストリビューション名 [Ubuntu-24.04]: ").strip() or "Ubuntu-24.04"
    else:
        execution_mode = "windows"
        dist = None

    # トークンを設定
    print()
    print("トークンを設定中...")

    if execution_mode == "wsl":
        success = setup_claude_token(
            execution_mode="wsl",
            wsl_distribution=dist,
            token=token
        )
    else:
        success = setup_claude_token(
            execution_mode="windows",
            token=token
        )

    print()
    print("=" * 70)

    if success:
        print("✅ トークン設定完了！")
        print()
        print("次のステップ:")
        print("  python tests/test_simple_worker_wsl.py")
        print()
    else:
        print("❌ トークン設定に失敗しました。")
        print()

    print("=" * 70)

    return success


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
