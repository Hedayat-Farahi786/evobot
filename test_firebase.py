#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Firebase Realtime Database connection
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.firebase_service import firebase_service
from datetime import datetime

def test_firebase():
    print("Testing Firebase Realtime Database connection...\n")
    
    # Initialize Firebase
    print("1. Initializing Firebase...")
    firebase_service.initialize()
    
    if not firebase_service.initialized:
        print("Firebase initialization failed!")
        print("   Check your credentials in .env file")
        return False
    
    print("Firebase initialized successfully!\n")
    
    # Test write operations
    print("2. Testing write operations...")
    
    try:
        # Test status update
        firebase_service.update_status({
            "bot_running": False,
            "mt5_connected": False,
            "telegram_connected": False,
            "test": True
        })
        print("Status update successful")
        
        # Test account update
        firebase_service.update_account({
            "balance": 10000.00,
            "equity": 10000.00,
            "margin": 0.00,
            "profit": 0.00,
            "test": True
        })
        print("Account update successful")
        
        # Test prices update
        firebase_service.update_prices({
            "XAUUSD": {
                "bid": 2050.00,
                "ask": 2050.50,
                "spread_pips": 5.0
            },
            "test": True
        })
        print("Prices update successful")
        
        # Test trade add
        firebase_service.add_trade("test_trade_123", {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry_price": 2050.00,
            "lot_size": 0.01,
            "status": "active",
            "test": True
        })
        print("Trade add successful")
        
        # Test activity add
        firebase_service.add_activity({
            "type": "test",
            "title": "Firebase Connection Test",
            "message": "Testing Firebase integration",
            "test": True
        })
        print("Activity add successful")
        
        # Test stats update
        firebase_service.update_stats({
            "total_trades": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "test": True
        })
        print("Stats update successful")
        
        print("\nAll Firebase operations successful!")
        print("\nCheck your Firebase Console:")
        print("   https://console.firebase.google.com/project/evobot-8/database")
        print("\nYou should see test data in the Realtime Database")
        
        return True
        
    except Exception as e:
        print("\nFirebase operation failed: " + str(e))
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct Firebase credentials")
        print("2. Verify database URL: https://evobot-8-default-rtdb.firebaseio.com")
        print("3. Check Firebase Console for database rules")
        print("4. Ensure service account has proper permissions")
        return False

if __name__ == "__main__":
    success = test_firebase()
    sys.exit(0 if success else 1)
