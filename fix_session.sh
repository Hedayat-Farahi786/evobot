#!/bin/bash
# Fix Telegram session database lock issue

echo "Fixing Telegram session lock issue..."

# Stop any running dashboard or main.py processes
echo "Stopping running processes..."
pkill -f "start_dashboard.py" 2>/dev/null
pkill -f "main.py" 2>/dev/null
sleep 2

# Remove the session file lock
echo "Removing session file..."
rm -f evobot_session.session evobot_session.session-journal 2>/dev/null

echo "✓ Session lock fixed!"
echo ""
echo "You can now start the bot or dashboard:"
echo "  - For dashboard: python3 start_dashboard.py"
echo "  - For main bot: python3 main.py"
