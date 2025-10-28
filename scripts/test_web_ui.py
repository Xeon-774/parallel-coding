#!/usr/bin/env python
"""
Web UIテストスクリプト

Webダッシュボードが正しく起動し、基本的なAPIが機能することを確認します。
"""

import sys
import time
import requests
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_web_ui():
    """Web UIの動作テスト"""

    print("=" * 60)
    print("  Claude Orchestrator Web UI Test")
    print("=" * 60)
    print()

    base_url = "http://127.0.0.1:8000"

    print(f"Testing Web UI at: {base_url}")
    print()

    # テスト1: サーバーが起動しているか確認
    print("[1/4] Testing server availability...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Server is not running")
        print()
        print("Please start the dashboard first:")
        print("  python start_dashboard.py")
        print()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # テスト2: /api/statusエンドポイント
    print("[2/4] Testing /api/status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working")
            print(f"   - System status: {data.get('status')}")
            print(f"   - Workers count: {data.get('workers_count')}")
            print(f"   - Workspace: {data.get('workspace')}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # テスト3: 静的ファイル
    print("[3/4] Testing static files...")
    try:
        response = requests.get(f"{base_url}/static/style.css", timeout=5)
        if response.status_code == 200:
            print("✅ Static files are served correctly")
        else:
            print(f"❌ Static files failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # テスト4: JavaScriptファイル
    print("[4/4] Testing JavaScript files...")
    try:
        response = requests.get(f"{base_url}/static/app.js", timeout=5)
        if response.status_code == 200:
            print("✅ JavaScript files are served correctly")
        else:
            print(f"❌ JavaScript files failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    print()
    print("=" * 60)
    print("  All tests passed! ✅")
    print("=" * 60)
    print()
    print(f"Dashboard URL: {base_url}")
    print()
    print("Next steps:")
    print("  1. Open your browser and go to the URL above")
    print("  2. In another terminal, run:")
    print('     python orchestrator/main.py "Create a simple app"')
    print("  3. Watch the dashboard update in real-time!")
    print()

    return True


def main():
    """メイン関数"""
    try:
        success = test_web_ui()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
