#!/bin/bash

# Claude Orchestrator - Portable Installation Script
# This script sets up the orchestrator in any project

set -e  # Exit on error

echo "🚀 Claude Orchestrator - Portable Installation"
echo "=============================================="
echo ""

# Check if running from orchestrator-portable directory
if [ ! -f "install.sh" ]; then
    echo "❌ Error: Please run this script from the orchestrator-portable/ directory"
    exit 1
fi

# Step 1: Check Python version
echo "📋 Step 1: Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "❌ Error: Python 3.9+ required (found $python_version)"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# Step 2: Create virtual environment (optional but recommended)
echo "📋 Step 2: Setting up virtual environment (optional)..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    echo "   Creating virtual environment..."
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi
echo ""

# Step 3: Install dependencies
echo "📋 Step 3: Installing dependencies..."
if [ -f "venv/bin/activate" ]; then
    echo "   Activating virtual environment..."
    source venv/bin/activate
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "   Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.25.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Type checking
mypy==1.7.0

# Configuration
pyyaml==6.0.1

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
EOF
fi

echo "   Installing Python packages..."
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Step 4: Copy orchestrator module if not present
echo "📋 Step 4: Setting up orchestrator module..."
if [ ! -d "../orchestrator" ]; then
    echo "   ❌ Error: orchestrator/ module not found in parent directory"
    echo "   Please ensure orchestrator-portable/ is in the same directory as orchestrator/"
    exit 1
fi

# Create symlink to orchestrator module
if [ ! -L "orchestrator" ] && [ ! -d "orchestrator" ]; then
    ln -s ../orchestrator orchestrator
    echo "   ✅ Orchestrator module linked"
else
    echo "   Orchestrator module already available"
fi
echo ""

# Step 5: Create default configuration
echo "📋 Step 5: Creating configuration..."
if [ ! -f "config.yaml" ]; then
    cp config.template.yaml config.yaml
    echo "   ✅ Created config.yaml (edit for your project)"
else
    echo "   config.yaml already exists (not overwriting)"
fi
echo ""

# Step 6: Create necessary directories
echo "📋 Step 6: Creating workspace directories..."
mkdir -p workspace
mkdir -p logs
echo "   ✅ Directories created"
echo ""

# Step 7: Make scripts executable
echo "📋 Step 7: Setting script permissions..."
chmod +x quick-start.sh
chmod +x check-status.sh
chmod +x api-server.sh
echo "   ✅ Scripts are executable"
echo ""

# Step 8: Verify installation
echo "📋 Step 8: Verifying installation..."
if python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "   ✅ All imports successful"
else
    echo "   ⚠️  Warning: Some imports failed, but continuing..."
fi
echo ""

# Success message
echo "=============================================="
echo "✅ Installation Complete!"
echo "=============================================="
echo ""
echo "📚 Quick Start:"
echo "   1. Review/edit config.yaml for your project"
echo "   2. Run: ./quick-start.sh \"your task description\""
echo "   3. Or start API: ./api-server.sh"
echo ""
echo "📖 Documentation:"
echo "   See README_FOR_AI.md for detailed usage"
echo ""
echo "🎯 Example:"
echo "   ./quick-start.sh \"Build a REST API with auth and CRUD\""
echo ""