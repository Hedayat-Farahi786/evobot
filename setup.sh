#!/bin/bash
# Quick start script for EvoBot

echo "=========================================="
echo "EvoBot Trading System - Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created."
    echo ""
    echo "📝 Please edit .env file with your credentials:"
    echo "   - Telegram API credentials"
    echo "   - MT5 broker credentials"
    echo "   - Trading configuration"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "To start EvoBot:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Run bot: python main.py"
echo ""
echo "To test signal parser:"
echo "  python test_parser.py"
echo ""
