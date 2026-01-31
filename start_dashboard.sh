#!/bin/bash

echo "🚀 Starting EvoBot Dashboard with Firebase..."
echo ""

# Check if firebase-admin is installed
if ! python -c "import firebase_admin" 2>/dev/null; then
    echo "⚠️  firebase-admin not installed. Installing..."
    pip install firebase-admin
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create one from .env.example"
    exit 1
fi

# Start the dashboard
echo "✅ Starting dashboard on http://localhost:8080"
echo ""
cd dashboard && python app.py
