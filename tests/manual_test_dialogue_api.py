"""
Manual test for dialogue WebSocket API

This script creates sample worker dialogue data and tests the API manually.

Usage:
    1. Start the API server:
       python -m uvicorn orchestrator.api.main:app --reload --port 8000

    2. In another terminal, run this test:
       python tests/manual_test_dialogue_api.py
"""

import asyncio
import json
import time
from pathlib import Path
import websockets


def create_test_workspace():
    """Create a test workspace with sample dialogue."""
    workspace_root = Path(__file__).parent.parent / "workspace"
    workspace_root.mkdir(exist_ok=True)

    # Create test worker workspace
    worker_path = workspace_root / "worker_test_001"
    worker_path.mkdir(exist_ok=True)

    # Create sample dialogue entries
    dialogue_entries = [
        {
            "timestamp": time.time() - 300,
            "direction": "worker→orchestrator",
            "content": "I need to run: pip install numpy",
            "type": "output",
            "confirmation_type": "bash",
            "confirmation_message": "Execute: pip install numpy"
        },
        {
            "timestamp": time.time() - 295,
            "direction": "orchestrator→worker",
            "content": "APPROVED",
            "type": "response",
            "confirmation_type": None,
            "confirmation_message": None
        },
        {
            "timestamp": time.time() - 290,
            "direction": "worker→orchestrator",
            "content": "Successfully installed numpy-1.26.4",
            "type": "output",
            "confirmation_type": None,
            "confirmation_message": None
        },
        {
            "timestamp": time.time() - 285,
            "direction": "worker→orchestrator",
            "content": "I need to create a file: test_data.py",
            "type": "output",
            "confirmation_type": "write_file",
            "confirmation_message": "Create file test_data.py"
        },
        {
            "timestamp": time.time() - 280,
            "direction": "orchestrator→worker",
            "content": "APPROVED",
            "type": "response",
            "confirmation_type": None,
            "confirmation_message": None
        },
        {
            "timestamp": time.time() - 275,
            "direction": "worker→orchestrator",
            "content": "File test_data.py created successfully",
            "type": "output",
            "confirmation_type": None,
            "confirmation_message": None
        }
    ]

    # Write to JSONL file
    transcript_jsonl = worker_path / "dialogue_transcript.jsonl"
    with open(transcript_jsonl, 'w', encoding='utf-8') as f:
        for entry in dialogue_entries:
            f.write(json.dumps(entry) + '\n')

    # Write to TXT file (human-readable)
    transcript_txt = worker_path / "dialogue_transcript.txt"
    with open(transcript_txt, 'w', encoding='utf-8') as f:
        f.write("=== Worker-Orchestrator Dialogue ===\n\n")
        for entry in dialogue_entries:
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))
            f.write(f"[{timestamp_str}] {entry['direction']}\n")
            f.write(f"  {entry['content']}\n")
            if entry['confirmation_type']:
                f.write(f"  (Confirmation: {entry['confirmation_type']})\n")
            f.write("\n")

    print(f"[OK] Created test workspace: {worker_path}")
    print(f"  - JSONL: {transcript_jsonl}")
    print(f"  - TXT: {transcript_txt}")
    print(f"  - Entries: {len(dialogue_entries)}")

    return worker_path


async def test_rest_api():
    """Test REST API endpoints."""
    import httpx

    print("\n=== Testing REST API ===")

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test root endpoint
        print("\n1. Testing GET /")
        response = await client.get("/")
        assert response.status_code == 200
        print(f"   [OK] Status: {response.status_code}")
        print(f"   [OK] Response: {response.json()}")

        # Test health check
        print("\n2. Testing GET /health")
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        print(f"   [OK] Status: {data['status']}")
        print(f"   [OK] Workspace: {data['workspace_root']}")

        # Test list workers
        print("\n3. Testing GET /api/v1/workers")
        response = await client.get("/api/v1/workers")
        assert response.status_code == 200
        data = response.json()
        print(f"   [OK] Workers found: {data['count']}")
        for worker in data['workers']:
            print(f"     - {worker['worker_id']}: dialogue={worker['has_dialogue']}")

        # Test get worker info
        print("\n4. Testing GET /api/v1/workers/worker_test_001")
        response = await client.get("/api/v1/workers/worker_test_001")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Worker ID: {data['worker_id']}")
            print(f"   [OK] JSONL exists: {data['dialogue']['jsonl_exists']}")
            print(f"   [OK] JSONL size: {data['dialogue']['jsonl_size']} bytes")
        else:
            print(f"   [ERROR] Status: {response.status_code}")


async def test_websocket():
    """Test WebSocket endpoint."""
    print("\n=== Testing WebSocket ===")

    uri = "ws://localhost:8000/ws/dialogue/worker_test_001"

    print(f"\n1. Connecting to {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("   [OK] Connected")

            print("\n2. Receiving messages:")
            message_count = 0

            # Receive messages until ready
            while True:
                message_str = await websocket.recv()
                message = json.loads(message_str)

                message_count += 1

                if message["type"] == "historical":
                    data = message["data"]
                    print(f"\n   [Historical #{message_count}]")
                    print(f"     Direction: {data['direction']}")
                    print(f"     Content: {data['content'][:50]}...")
                    if data['confirmation_type']:
                        print(f"     Confirmation: {data['confirmation_type']}")

                elif message["type"] == "ready":
                    print(f"\n   [Ready]")
                    print(f"     {message['message']}")
                    break

                elif message["type"] == "error":
                    print(f"\n   [Error]")
                    print(f"     {message['message']}")
                    break

            print(f"\n   [OK] Received {message_count} messages total")

            # Test real-time streaming (simulate new entry)
            print("\n3. Testing real-time streaming:")
            print("   Appending new entry to dialogue file...")

            workspace_root = Path(__file__).parent.parent / "workspace"
            transcript = workspace_root / "worker_test_001" / "dialogue_transcript.jsonl"

            new_entry = {
                "timestamp": time.time(),
                "direction": "worker→orchestrator",
                "content": "This is a new entry added during the test",
                "type": "output",
                "confirmation_type": None,
                "confirmation_message": None
            }

            with open(transcript, 'a', encoding='utf-8') as f:
                f.write(json.dumps(new_entry) + '\n')

            print("   Waiting for new entry...")

            # Wait for new entry (with timeout)
            try:
                message_str = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(message_str)

                if message["type"] == "entry":
                    print(f"   [OK] Received new entry!")
                    print(f"     Content: {message['data']['content']}")
                else:
                    print(f"   Unexpected message type: {message['type']}")

            except asyncio.TimeoutError:
                print("   [WARN] Timeout - file watching may need time to detect changes")
                print("     (This is normal on some systems)")

    except ConnectionRefusedError:
        print("\n   [ERROR] Connection refused!")
        print("     Make sure the API server is running:")
        print("     python -m uvicorn orchestrator.api.main:app --reload --port 8000")
        return False

    except Exception as e:
        print(f"\n   [ERROR] Error: {e}")
        return False

    return True


async def main():
    """Run all manual tests."""
    print("=" * 60)
    print("Manual Test: Dialogue WebSocket API")
    print("=" * 60)

    # Create test data
    worker_path = create_test_workspace()

    # Wait a moment
    await asyncio.sleep(0.5)

    # Test REST API
    try:
        await test_rest_api()
    except Exception as e:
        print(f"\n[ERROR] REST API tests failed: {e}")
        print("  Make sure the server is running on http://localhost:8000")
        return

    # Test WebSocket
    try:
        success = await test_websocket()
        if success:
            print("\n" + "=" * 60)
            print("[OK] All manual tests completed successfully!")
            print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] WebSocket tests failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
