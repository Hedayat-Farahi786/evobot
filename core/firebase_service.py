"""
Firebase Realtime Database Service
Syncs trading data to Firebase for real-time dashboard updates
"""
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("evobot.firebase")

class FirebaseService:
    def __init__(self):
        self.db_ref = None
        self.initialized = False
        
    def initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase credentials are configured
            private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
            client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")
            
            if not private_key or not client_email:
                logger.info("Firebase credentials not configured - skipping initialization")
                self.initialized = False
                return
            
            # Firebase config from environment or hardcoded
            firebase_config = {
                "apiKey": "AIzaSyClrXVHM5xP4FqZKsjaqN7VEXAsGwNeax4",
                "authDomain": "evobot-8.firebaseapp.com",
                "databaseURL": "https://evobot-8-default-rtdb.europe-west1.firebasedatabase.app",
                "projectId": "evobot-8",
                "storageBucket": "evobot-8.firebasestorage.app",
                "messagingSenderId": "349123654411",
                "appId": "1:349123654411:web:afc01b90aa06984c74e80e"
            }
            
            # Initialize Firebase Admin (server-side)
            if not firebase_admin._apps:
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": firebase_config["projectId"],
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
                    "private_key": private_key.replace('\\n', '\n'),
                    "client_email": client_email,
                    "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                })
                firebase_admin.initialize_app(cred, {
                    'databaseURL': firebase_config["databaseURL"]
                })
            
            self.db_ref = db.reference('/')
            self.initialized = True
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            self.initialized = False
    
    def update_status(self, data: Dict[str, Any]):
        """Update bot status in Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('status').set({
                **data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase update_status error: {e}")
    
    async def update_status_async(self, data: Dict[str, Any]):
        """Update bot status in Firebase (async wrapper)"""
        self.update_status(data)
    
    def update_account(self, data: Dict[str, Any]):
        """Update account info in Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('account').set({
                **data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase update_account error: {e}")
    
    def update_prices(self, prices: Dict[str, Any]):
        """Update live prices in Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('prices').set({
                **prices,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase update_prices error: {e}")
    
    def add_trade(self, trade_id: str, trade_data: Dict[str, Any]):
        """Add or update trade in Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('trades').child(trade_id).set({
                **trade_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase add_trade error: {e}")
    
    def add_activity(self, activity: Dict[str, Any]):
        """Add activity to Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('activities').push({
                **activity,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase add_activity error: {e}")
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update trading stats in Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('stats').set({
                **stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase update_stats error: {e}")
    
    def update_channels_info(self, channels: list):
        """Update Telegram channels info in Firebase"""
        if not self.initialized:
            return
        try:
            self.db_ref.child('telegram_channels').set({
                'channels': channels,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Firebase update_channels_info error: {e}")

# Global instance
firebase_service = FirebaseService()
