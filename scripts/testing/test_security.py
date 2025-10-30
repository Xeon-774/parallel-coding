#!/usr / bin / env python3
"""
Security Test Suite for Web UI
Tests Path Traversal vulnerability fixes
"""

import requests

BASE_URL = "http://127.0.0.1:8000"


def test_path_traversal_logs():
    """Test 1: Path Traversal Attack on /api / logs endpoint"""
    print("\n" + "=" * 70)
    print("TEST 1: Path Traversal Attack - /api / logs/{log_file}")
    print("=" * 70)

    malicious_paths = [
        "../../../etc / passwd",
        r"..\..\..\windows\system32\config\sam",
        "../../pyproject.toml",
        "../orchestrator / __init__.py",
    ]

    for path in malicious_paths:
        print(f"\n[ATTACK] Trying: {path}")
        try:
            response = requests.get(f"{BASE_URL}/api / logs/{path}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 400:
                print("  [OK] BLOCKED - Security working correctly!")
            else:
                print(f"  [FAIL] VULNERABILITY - Got status {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] {e}")


def test_path_traversal_screenshots():
    """Test 2: Path Traversal Attack on /api / screenshots endpoint"""
    print("\n" + "=" * 70)
    print("TEST 2: Path Traversal Attack - /api / screenshots/{screenshot_file}")
    print("=" * 70)

    malicious_paths = [
        "../../../etc / passwd",
        r"..\..\..\windows\system32\drivers\etc\hosts",
        "../../web_ui / app.py",
        "../logs / orchestrator_20251021.jsonl",
    ]

    for path in malicious_paths:
        print(f"\n[ATTACK] Trying: {path}")
        try:
            response = requests.get(f"{BASE_URL}/api / screenshots/{path}")
            print(f"  Status: {response.status_code}")

            if response.status_code == 400:
                print(f"  Response: {response.json()}")
                print("  ✅ BLOCKED - Security working correctly!")
            else:
                print(f"  ❌ VULNERABILITY - Got status {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_path_traversal_worker():
    """Test 3: Path Traversal Attack on /api / worker endpoint"""
    print("\n" + "=" * 70)
    print("TEST 3: Path Traversal Attack - /api / worker/{worker_id}/output")
    print("=" * 70)

    malicious_ids = [
        "../../etc / passwd",
        r"..\..\windows\system32",
        "../orchestrator",
        "not_worker_1",  # Doesn't start with "worker_"
        "worker_../../../etc",
    ]

    for worker_id in malicious_ids:
        print(f"\n[ATTACK] Trying: {worker_id}")
        try:
            response = requests.get(f"{BASE_URL}/api / worker/{worker_id}/output")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 400:
                print("  [OK] BLOCKED - Security working correctly!")
            else:
                print(f"  [FAIL] VULNERABILITY - Got status {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] {e}")


if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print("   WEB UI SECURITY TEST SUITE - PATH TRAVERSAL PROTECTION")
    print("=" * 70)

    test_path_traversal_logs()
    test_path_traversal_screenshots()
    test_path_traversal_worker()

    print("\n" + "=" * 70)
    print("SECURITY TESTS COMPLETE")
    print("=" * 70 + "\n")
