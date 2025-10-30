#!/usr / bin / env python3
"""
Normal API Test Suite for Web UI
Tests正常な動作を確認
"""

import requests

BASE_URL = "http://127.0.0.1:8000"


def test_get_status():
    """Test 1: GET /api / status"""
    print("\n" + "=" * 70)
    print("TEST 1: GET /api / status")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api / status")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  System Status: {data.get('status')}")
            print(f"  Workers Count: {data.get('workers_count')}")
            print(f"  Workspace: {data.get('workspace')}")
            print(f"  Workers: {len(data.get('workers', []))}")
            print("  [OK] Status endpoint working correctly!")
        else:
            print(f"  [FAIL] Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] {e}")


def test_get_worker_output():
    """Test 2: GET /api / worker/{worker_id}/output"""
    print("\n" + "=" * 70)
    print("TEST 2: GET /api / worker / worker_1 / output")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api / worker / worker_1 / output")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Worker ID: {data.get('worker_id')}")
            print(f"  Total Lines: {data.get('total_lines')}")
            print(f"  Output Preview: {data.get('output', '')[:100]}...")
            print("  [OK] Worker output endpoint working correctly!")
        else:
            print(f"  Response: {response.json()}")
            print(f"  [FAIL] Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] {e}")


def test_get_logs():
    """Test 3: GET /api / logs/{log_file}"""
    print("\n" + "=" * 70)
    print("TEST 3: GET /api / logs / orchestrator_20251021.jsonl")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api / logs / orchestrator_20251021.jsonl")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Total Lines: {data.get('total_lines')}")
            print(f"  Returned Lines: {data.get('returned_lines')}")
            print(f"  Logs Count: {len(data.get('logs', []))}")
            print("  [OK] Logs endpoint working correctly!")
        else:
            print(f"  Response: {response.json()}")
            print(f"  [FAIL] Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] {e}")


def test_get_index():
    """Test 4: GET / (Dashboard Index)"""
    print("\n" + "=" * 70)
    print("TEST 4: GET / (Dashboard Index)")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"  Status: {response.status_code}")
        print(f"  Content - Type: {response.headers.get('content - type')}")
        print(f"  Content Length: {len(response.text)} bytes")

        if response.status_code == 200 and "html" in response.headers.get("content - type", ""):
            if "Claude Orchestrator Dashboard" in response.text:
                print("  Dashboard Title: Found")
                print("  Version: v10.0" if "v10.0" in response.text else "  Version: Not found")
                print("  [OK] Dashboard index working correctly!")
            else:
                print("  [FAIL] Dashboard title not found")
        else:
            print("  [FAIL] Unexpected response")
    except Exception as e:
        print(f"  [ERROR] {e}")


if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print("   WEB UI NORMAL API TEST SUITE")
    print("=" * 70)

    test_get_status()
    test_get_worker_output()
    test_get_logs()
    test_get_index()

    print("\n" + "=" * 70)
    print("NORMAL API TESTS COMPLETE")
    print("=" * 70 + "\n")
