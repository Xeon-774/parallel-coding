#!/usr/bin/env python
"""
Claude Orchestrator Dashboard起動スクリプト

簡単にWebダッシュボードを起動できるユーティリティ
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web_ui.app import start_server


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Claude Orchestrator Web Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルトで起動 (http://127.0.0.1:8000)
  python start_dashboard.py

  # カスタムポートで起動
  python start_dashboard.py --port 3000

  # 外部アクセスを許可
  python start_dashboard.py --host 0.0.0.0 --port 8080

  # ワークスペースを指定
  python start_dashboard.py --workspace /path/to/workspace
        """
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="バインドするホスト (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="バインドするポート (default: 8000)"
    )

    parser.add_argument(
        "--workspace",
        default="./workspace",
        help="ワークスペースのパス (default: ./workspace)"
    )

    args = parser.parse_args()

    # 環境変数を設定（オプション）
    import os
    os.environ["ORCHESTRATOR_WORKSPACE"] = args.workspace

    # サーバー起動
    start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
