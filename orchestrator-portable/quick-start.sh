#!/bin/bash

# Claude Orchestrator - Quick Start Script
# Launches orchestrator with a simple task description

set -e

# Check if task description provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Please provide a task description"
    echo ""
    echo "Usage: ./quick-start.sh \"task description\""
    echo ""
    echo "Examples:"
    echo "  ./quick-start.sh \"Build a REST API with authentication\""
    echo "  ./quick-start.sh \"Create a React frontend with 5 components\""
    echo "  ./quick-start.sh \"Implement microservices architecture\""
    exit 1
fi

TASK="$1"
MAX_WORKERS="${2:-5}"  # Default 5 workers
TIMEOUT="${3:-300}"    # Default 5 minutes

echo "🚀 Claude Orchestrator - Quick Start"
echo "===================================="
echo ""
echo "📋 Task: $TASK"
echo "👥 Max Workers: $MAX_WORKERS"
echo "⏱️  Timeout: ${TIMEOUT}s"
echo ""

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo "⚠️  Warning: config.yaml not found, using defaults"
    echo "   Run ./install.sh to create config.yaml"
    echo ""
fi

# Check if orchestrator API is running
API_RUNNING=false
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    API_RUNNING=true
    echo "✅ Orchestrator API is running"
else
    echo "🔧 Starting Orchestrator API..."
    # Start API server in background
    python3 -m uvicorn orchestrator.api.app:app --host 0.0.0.0 --port 8000 > logs/api_server.log 2>&1 &
    API_PID=$!
    echo "   API server started (PID: $API_PID)"

    # Wait for API to be ready
    echo "   Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "   ✅ API is ready!"
            API_RUNNING=true
            break
        fi
        sleep 1
    done

    if [ "$API_RUNNING" = false ]; then
        echo "   ❌ Failed to start API server"
        echo "   Check logs/api_server.log for details"
        exit 1
    fi
fi

echo ""
echo "📤 Submitting task to orchestrator..."

# Submit task via API
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/orchestrate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${ORCHESTRATOR_API_KEY:-dev-key-12345}" \
    -d "{
        \"request\": \"$TASK\",
        \"config\": {
            \"max_workers\": $MAX_WORKERS,
            \"default_timeout\": $TIMEOUT,
            \"enable_recursion\": true,
            \"max_recursion_depth\": 2
        }
    }")

# Extract job ID
JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "")

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to submit task"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "✅ Task submitted successfully!"
echo "   Job ID: $JOB_ID"
echo ""

# Monitor progress
echo "📊 Monitoring progress..."
echo "   (Press Ctrl+C to stop monitoring, job will continue)"
echo ""

DOTS=0
while true; do
    # Get status
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/status)
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
    PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['progress']['completed']}/{data['progress']['total']}\")" 2>/dev/null || echo "?/?")

    # Print status
    printf "\r   Status: %-12s Progress: %-8s" "$STATUS" "$PROGRESS"

    # Check if complete
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] || [ "$STATUS" = "partial" ]; then
        echo ""
        break
    fi

    sleep 2
done

echo ""
echo "=============================================="

if [ "$STATUS" = "completed" ]; then
    echo "✅ Task Completed Successfully!"
    echo "=============================================="
    echo ""

    # Get results
    RESULTS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results)

    # Display summary
    echo "📊 Summary:"
    echo "$RESULTS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Total Tasks: {len(data.get('results', {}).get('tasks', []))}\")
success = sum(1 for t in data.get('results', {}).get('tasks', []) if t['status'] == 'success')
print(f\"   Successful: {success}\")
print(f\"   Workspace: {data.get('results', {}).get('workspace', 'N/A')}\")
" 2>/dev/null || echo "   (Unable to parse results)"

    echo ""
    echo "📄 Final Report:"
    WORKSPACE=$(echo "$RESULTS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('results', {}).get('workspace', ''))" 2>/dev/null || echo "")

    if [ -n "$WORKSPACE" ] && [ -f "$WORKSPACE/FINAL_RESULT.md" ]; then
        echo "   Location: $WORKSPACE/FINAL_RESULT.md"
        echo ""
        echo "   Preview:"
        head -20 "$WORKSPACE/FINAL_RESULT.md" | sed 's/^/   /'
        echo "   ..."
    else
        echo "   (Report not available)"
    fi

elif [ "$STATUS" = "failed" ]; then
    echo "❌ Task Failed"
    echo "=============================================="
    echo ""
    echo "📄 Error Details:"
    ERROR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))" 2>/dev/null || echo "Unknown error")
    echo "   $ERROR"
    echo ""
    echo "📋 Check logs for more details:"
    echo "   - API logs: logs/api_server.log"
    echo "   - Worker logs: workspace/job_$JOB_ID/logs/"

elif [ "$STATUS" = "partial" ]; then
    echo "⚠️  Task Partially Completed"
    echo "=============================================="
    echo ""
    echo "Some workers succeeded, some failed."
    echo "Check workspace/job_$JOB_ID/FINAL_RESULT.md for details"
fi

echo ""
echo "🔍 Full results available at:"
echo "   http://localhost:8000/api/v1/jobs/$JOB_ID/results"
echo ""
echo "💡 To check status later:"
echo "   ./check-status.sh $JOB_ID"
echo ""