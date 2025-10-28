#!/bin/bash

# Claude Orchestrator - API Server Launcher
# Starts the REST API server

echo "🚀 Starting Claude Orchestrator API Server"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo "⚠️  Warning: config.yaml not found"
    echo "   Creating from template..."
    cp config.template.yaml config.yaml
    echo "   ✅ config.yaml created (please review and edit)"
    echo ""
fi

# Load configuration
HOST=$(grep -A 1 "^api:" config.yaml | grep "host:" | awk '{print $2}' | tr -d '"' || echo "0.0.0.0")
PORT=$(grep -A 2 "^api:" config.yaml | grep "port:" | awk '{print $2}' | tr -d '"' || echo "8000")

echo "📋 Configuration:"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Warning: Port $PORT is already in use"
    echo ""
    echo "Options:"
    echo "  1. Stop the existing process: kill \$(lsof -t -i:$PORT)"
    echo "  2. Use a different port in config.yaml"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🌐 Starting server..."
echo "   Access at: http://$HOST:$PORT"
echo "   API docs: http://$HOST:$PORT/docs"
echo "   Health check: http://$HOST:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the server
python3 -m uvicorn orchestrator.api.app:app \
    --host "$HOST" \
    --port "$PORT" \
    --log-level info \
    --access-log \
    2>&1 | tee logs/api_server.log