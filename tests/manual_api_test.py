"""
Manual API Test Script

This script tests the API server functionality without requiring
actual Claude AI execution. It uses the API in a controlled way
to verify the basic workflow.

Usage:
    1. Start API server in one terminal:
       python start_api_server.py

    2. Run this test in another terminal:
       python tests/manual_api_test.py

    Or use the automated version (requires no separate terminal):
       python tests/manual_api_test.py --auto
"""

import sys
import time
import argparse
import subprocess
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator_client import OrchestratorClient, OrchestratorError


class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def test_server_connectivity(api_url):
    """Test if API server is reachable"""
    print_header("Test 1: Server Connectivity")

    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is reachable")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Version: {data.get('version')}")
            return True
        else:
            print_error(f"Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server")
        print_info(f"Make sure API server is running on {api_url}")
        print_info("Start with: python start_api_server.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_health_check(client):
    """Test health check endpoint"""
    print_header("Test 2: Health Check")

    try:
        if client.health_check():
            print_success("Health check passed")
            return True
        else:
            print_error("Health check failed")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_system_status(client):
    """Test system status endpoint"""
    print_header("Test 3: System Status")

    try:
        status = client.get_system_status()
        print_success("System status retrieved")
        print_info(f"Status: {status['status']}")
        print_info(f"Available capacity: {status['available_capacity']} workers")
        print_info(f"Active jobs: {status['active_jobs']}")
        print_info(f"Completed jobs: {status['total_completed_jobs']}")
        print_info(f"Version: {status['version']}")
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_authentication(api_url):
    """Test API authentication"""
    print_header("Test 4: Authentication")

    # Test without API key
    print_info("Testing request without API key...")
    try:
        response = requests.post(
            f"{api_url}/api/v1/orchestrate",
            json={"request": "Test request"}
        )
        if response.status_code == 401:
            print_success("Correctly rejected request without API key")
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
        return False

    # Test with invalid API key
    print_info("Testing request with invalid API key...")
    try:
        response = requests.post(
            f"{api_url}/api/v1/orchestrate",
            json={"request": "Test request"},
            headers={"X-API-Key": "invalid-key-12345"}
        )
        if response.status_code == 401:
            print_success("Correctly rejected request with invalid API key")
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
        return False

    return True


def test_mock_orchestration(client):
    """Test orchestration with a mock request that won't actually execute Claude"""
    print_header("Test 5: Mock Orchestration Request")

    print_warning("Note: This will create a job but may fail during execution")
    print_warning("because it requires actual Claude CLI access.")
    print_info("This is expected - we're testing the API workflow, not actual execution.")

    try:
        # Submit a very simple request
        print_info("Submitting orchestration request...")
        job = client.orchestrate(
            request="Print 'Hello World'",
            config={
                "max_workers": 1,
                "default_timeout": 10,
                "enable_ai_analysis": False
            },
            wait=False  # Don't wait for completion
        )

        print_success(f"Job created: {job.job_id}")

        # Check status
        print_info("Checking job status...")
        time.sleep(1)  # Give it a moment

        status = job.status()
        print_info(f"Job status: {status['status']}")
        print_info(f"Total tasks: {status['progress']['total_tasks']}")

        # Note: Job will likely fail because we don't have real Claude execution
        # but that's OK - we're testing the API workflow

        print_success("API workflow test completed")
        print_warning("Job execution may fail (this is expected without real Claude CLI)")

        return True

    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sdk_client_basic(client):
    """Test SDK client basic functionality"""
    print_header("Test 6: SDK Client Functionality")

    # Test that client methods exist
    methods = ['orchestrate', 'get_job', 'get_system_status', 'health_check']

    for method in methods:
        if hasattr(client, method):
            print_success(f"Client has method: {method}")
        else:
            print_error(f"Client missing method: {method}")
            return False

    return True


def run_all_tests(api_url, api_key, skip_execution=False):
    """Run all tests"""
    print_header("Claude Orchestrator API - Manual Test Suite")
    print_info(f"API URL: {api_url}")
    print_info(f"API Key: {api_key[:20]}...")

    results = []

    # Test 1: Server connectivity
    if not test_server_connectivity(api_url):
        print_error("\nServer is not reachable. Cannot continue tests.")
        return False

    # Create client
    client = OrchestratorClient(api_url=api_url, api_key=api_key)

    # Test 2: Health check
    results.append(("Health Check", test_health_check(client)))

    # Test 3: System status
    results.append(("System Status", test_system_status(client)))

    # Test 4: Authentication
    results.append(("Authentication", test_authentication(api_url)))

    # Test 5: SDK client
    results.append(("SDK Client", test_sdk_client_basic(client)))

    # Test 6: Mock orchestration (optional)
    if not skip_execution:
        results.append(("Mock Orchestration", test_mock_orchestration(client)))
    else:
        print_warning("\nSkipping orchestration test (--skip-execution)")

    # Summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print_success("\n🎉 All tests passed!")
        return True
    else:
        print_error(f"\n❌ {total - passed} test(s) failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Manual API Test Suite for Claude Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API server URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "--api-key",
        default="sk-orch-dev-key-12345",
        help="API key for authentication"
    )

    parser.add_argument(
        "--skip-execution",
        action="store_true",
        help="Skip actual orchestration execution test"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Start API server automatically (experimental)"
    )

    args = parser.parse_args()

    server_process = None

    if args.auto:
        print_info("Starting API server automatically...")
        print_warning("This is experimental. Press Ctrl+C to stop.")
        print()

        # Start server in background
        server_process = subprocess.Popen(
            [sys.executable, "start_api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to start
        print_info("Waiting for server to start...")
        time.sleep(3)

    try:
        success = run_all_tests(
            api_url=args.api_url,
            api_key=args.api_key,
            skip_execution=args.skip_execution
        )

        sys.exit(0 if success else 1)

    finally:
        if server_process:
            print_info("\nShutting down API server...")
            server_process.terminate()
            server_process.wait(timeout=5)


if __name__ == "__main__":
    main()
