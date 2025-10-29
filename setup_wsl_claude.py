#!/usr/bin/env python3
"""
WSL Claude CLI 完全自動セットアップ

このスクリプトを実行するだけで、以下を自動的に行います:
1. WSL (Ubuntu-24.04) に Claude CLI をインストール
2. トークン入力（GUIダイアログで入力）
3. 認証確認
4. 動作テスト

使用方法:
    python setup_wsl_claude.py

または、別のWSLディストリビューションを指定:
    python setup_wsl_claude.py Ubuntu-22.04
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator.utils.wsl_setup import WSLClaudeSetup


def main():
    print()
    print("=" * 70)
    print(" " * 15 + "WSL Claude CLI 自動セットアップ")
    print("=" * 70)
    print()

    # WSLディストリビューション名
    if len(sys.argv) > 1:
        distribution = sys.argv[1]
    else:
        distribution = "Ubuntu-24.04"

    print(f"WSL Distribution: {distribution}")
    print()

    # セットアップ実行
    setup = WSLClaudeSetup(wsl_distribution=distribution)

    try:
        success = setup.run_full_setup()

        if success:
            print()
            print("次のコマンドでテストを実行:")
            print()
            print("  python tests/test_simple_worker_wsl.py")
            print()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n中断されました。")
        return 1
    except Exception as e:
        print(f"\n[X] エラー: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
