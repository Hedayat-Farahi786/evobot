#!/bin/bash

# EvoBot Dashboard - One-Click Setup & Start
# This script installs dependencies and starts the dashboard

set -e

echo "=========================================="
echo "🤖 EvoBot Dashboard Setup"
echo "=========================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your credentials:"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've configured .env file..."
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "=========================================="
echo "🚀 Starting EvoBot Dashboard"
echo "=========================================="
echo ""
echo "📡 Dashboard will be available at:"
echo "   http://localhost:8080"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8080/docs"
echo ""
echo "Press CTRL+C to stop the dashboard"
echo ""
echo "=========================================="
echo ""

# Start the dashboard
python3 start_dashboard.py
