"""
MT5 Credentials Storage
Stores MT5 credentials per user for persistent login
"""
import logging
import json
import os
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger("evobot.mt5_credentials")

class MT5CredentialsStore:
    def __init__(self):
        self._credentials: Dict[str, Dict[str, str]] = {}
        self._storage_file = Path("data/mt5_credentials.json")
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load credentials from disk on startup"""
        try:
            if self._storage_file.exists():
                with open(self._storage_file, 'r') as f:
                    self._credentials = json.load(f)
                logger.info(f"Loaded MT5 credentials for {len(self._credentials)} users from disk")
        except Exception as e:
            logger.error(f"Failed to load MT5 credentials from disk: {e}")
    
    def _save_to_disk(self):
        """Save credentials to disk for persistence"""
        try:
            self._storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._storage_file, 'w') as f:
                json.dump(self._credentials, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save MT5 credentials to disk: {e}")
    
    def set(self, user_id: str, server: str, login: str, password: str):
        """Store MT5 credentials for a user"""
        self._credentials[user_id] = {
            "server": server,
            "login": login,
            "password": password
        }
        self._save_to_disk()
        logger.info(f"Stored MT5 credentials for user {user_id}")
    
    def get(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get MT5 credentials for a user"""
        creds = self._credentials.get(user_id)
        if creds:
            logger.debug(f"Retrieved MT5 credentials for user {user_id}")
        return creds
    
    def has_credentials(self, user_id: str) -> bool:
        """Check if user has stored credentials"""
        return user_id in self._credentials
    
    def remove(self, user_id: str):
        """Remove MT5 credentials for a user"""
        if user_id in self._credentials:
            del self._credentials[user_id]
            self._save_to_disk()
            logger.info(f"Removed MT5 credentials for user {user_id}")

# Global instance
mt5_store = MT5CredentialsStore()
