#!/bin/bash

# Claude Orchestrator - Status Check Script
# Check the status of a running or completed job

if [ $# -eq 0 ]; then
    echo "Usage: ./check-status.sh <job-id>"
    exit 1
fi

JOB_ID="$1"
API_URL="${2:-http://localhost:8000}"

echo "🔍 Checking status for Job: $JOB_ID"
echo "===================================="
echo ""

# Check if API is running
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ Error: Orchestrator API is not running"
    echo "   Start it with: ./api-server.sh"
    exit 1
fi

# Get job status
STATUS_RESPONSE=$(curl -s "$API_URL/api/v1/jobs/$JOB_ID/status")

if [ -z "$STATUS_RESPONSE" ]; then
    echo "❌ Error: Failed to get job status"
    exit 1
fi

# Parse and display status
python3 << 'EOF'
import sys
import json

try:
    data = json.loads('''$STATUS_RESPONSE''')

    print(f"📊 Status: {data['status']}")
    print(f"📝 Job ID: {data['job_id']}")
    print("")

    progress = data.get('progress', {})
    print(f"Progress: {progress.get('completed', 0)}/{progress.get('total', 0)} tasks")
    print(f"Success Rate: {progress.get('success_rate', 0):.1%}")
    print("")

    if data['status'] == 'running':
        print("⏳ Job is currently running...")
        print("")
        print("Active Workers:")
        for task in data.get('tasks', []):
            if task['status'] == 'running':
                print(f"   - {task['worker_id']}: {task.get('description', 'N/A')}")

    elif data['status'] == 'completed':
        print("✅ Job completed successfully!")
        print("")
        print(f"📄 Results available at:")
        print(f"   {data.get('workspace', 'N/A')}/FINAL_RESULT.md")

    elif data['status'] == 'failed':
        print("❌ Job failed")
        print("")
        error = data.get('error', 'Unknown error')
        print(f"Error: {error}")

    elif data['status'] == 'partial':
        print("⚠️  Job partially completed")
        print("")
        print("Some workers succeeded, others failed")

except json.JSONDecodeError:
    print("❌ Error: Invalid response from API")
    sys.exit(1)
except KeyError as e:
    print(f"❌ Error: Missing field in response: {e}")
    sys.exit(1)
EOF