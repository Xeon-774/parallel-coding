"""
認証ヘルパーの手動テスト - GUI トークン入力

注意: このテストはGUIを使用するため、pytest自動実行から除外されています。
手動で実行する場合: python tests/manual_test_auth_helper.py
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.utils import setup_claude_token


def test_auth_gui():
    """GUIでトークン入力をテスト"""

    print("=" * 70)
    print("Claude CLI 認証トークン設定テスト")
    print("=" * 70)
    print()
    print("WSLモードでトークンを設定します。")
    print("GUIダイアログが表示されます...")
    print()

    # WSLモードでトークン設定（GUI使用）
    success = setup_claude_token(
        execution_mode="wsl", wsl_distribution="Ubuntu-24.04", use_gui=True  # GUIダイアログを表示
    )

    print()
    print("=" * 70)

    if success:
        print("[SUCCESS] トークン設定完了！")
        print()
        print("次のステップ:")
        print("  python tests/test_simple_worker_wsl.py")
        print()
    else:
        print("[CANCELLED] トークン設定がキャンセルされました。")

    print("=" * 70)

    return success


if __name__ == "__main__":
    success = test_auth_gui()
    sys.exit(0 if success else 1)
