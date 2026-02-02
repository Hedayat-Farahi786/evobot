#!/bin/bash
# Quick test script for real-time sync

echo "=================================="
echo "EvoBot Real-Time Sync Quick Test"
echo "=================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Run: source venv/bin/activate (Linux/Mac)"
    echo "   Or:  venv\\Scripts\\activate (Windows)"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "=================================="
echo "Test 1: Automated Test Suite"
echo "=================================="
echo ""
echo "Running comprehensive tests..."
echo ""

python test_realtime_sync.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All automated tests passed!"
    echo ""
else
    echo ""
    echo "❌ Some tests failed. Check logs above."
    echo ""
    exit 1
fi

echo "=================================="
echo "Test 2: Visual Dashboard Test"
echo "=================================="
echo ""
echo "Starting dashboard..."
echo ""
echo "📝 Instructions:"
echo "   1. Dashboard will start on http://localhost:8080"
echo "   2. Open http://localhost:8080/test-realtime in your browser"
echo "   3. Click 'Start Bot' from main dashboard"
echo "   4. Watch real-time updates on test page"
echo "   5. Press Ctrl+C here to stop"
echo ""
echo "Starting in 3 seconds..."
sleep 3

python start_dashboard.py
