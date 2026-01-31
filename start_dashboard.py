#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EvoBot Web Dashboard Launcher
Starts the FastAPI web interface for EvoBot with auto-start bot
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable auto-start - user should click Start Bot in dashboard
os.environ["AUTO_START_BOT"] = "false"

if __name__ == "__main__":
    import uvicorn
    from dashboard.app import app
    
    print("=" * 60)
    print("Starting EvoBot Web Dashboard")
    print("=" * 60)
    print("Dashboard URL: http://localhost:8080")
    print("API Docs: http://localhost:8080/docs")
    print("=" * 60)
    print("\nClick 'Start Bot' in dashboard to begin trading...")
    print("Press CTRL+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="warning",
        access_log=False
    )
