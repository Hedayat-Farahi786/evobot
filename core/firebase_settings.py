"""
Firebase-backed Configuration Settings
All settings are stored in Firebase and editable from the dashboard
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("evobot.firebase_settings")

# Default values (used only on first run or if Firebase is unavailable)
DEFAULT_SETTINGS = {
    "telegram": {
        "api_id": "",
        "api_hash": "",
        "phone_number": "",
        "session_name": "evobot_session",
        "signal_channels": [],
        "notification_channel": "",
        "reconnect_delay": 5,
        "max_reconnect_attempts": 999
    },
    "broker": {
        "broker_type": "metaapi",
        "metaapi_token": "",
        "metaapi_account_id": "",
        "server": "",
        "login": 0,
        "password": "",
        "timeout": 60000,
        "retry_attempts": 3,
        "retry_delay": 1.0
    },
    "trading": {
        "symbols": ["XAUUSD", "GBPUSD", "EURUSD", "USDJPY", "GBPJPY"],
        "default_lot_size": 0.01,
        "max_spread_pips": 10.0,
        "max_daily_drawdown_percent": 5.0,
        "max_open_trades": 10,
        "symbol_max_spreads": {
            "XAUUSD": 50.0,
            "XAGUSD": 30.0,
            "BTCUSD": 100.0,
            "US30": 50.0,
            "NAS100": 50.0
        },
        "tp1_close_percent": 0.5,
        "tp2_close_percent": 0.3,
        "tp3_close_percent": 0.2,
        "move_sl_to_breakeven_at_tp1": True,
        "breakeven_offset_pips": 1.0,
        "entry_zone_tolerance": 5.0,
        "execute_immediately": True,
        "max_slippage": 30,
        "use_pending_orders": False
    },
    "risk": {
        "avoid_high_impact_news": True,
        "news_blackout_minutes_before": 30,
        "news_blackout_minutes_after": 15,
        "trading_start_hour": 0,
        "trading_end_hour": 24,
        "close_trades_before_weekend": False,
        "weekend_close_hour_friday": 21,
        "max_risk_percent_per_trade": 2.0
    }
}


class FirebaseSettings:
    """
    Firebase-backed settings manager.
    All settings are stored in Firebase and can be edited from the dashboard.
    Falls back to .env values on first run, then syncs to Firebase.
    """
    
    def __init__(self):
        self._settings: Dict[str, Any] = {}
        self._db_ref = None
        self._initialized = False
        self._local_cache_file = "data/settings_cache.json"
        
    def initialize(self, db_ref):
        """Initialize with Firebase database reference"""
        self._db_ref = db_ref
        self._load_settings()
        self._initialized = True
        logger.info("Firebase settings initialized")
        
    def _load_settings(self):
        """Load settings from Firebase only"""
        try:
            if self._db_ref:
                firebase_settings = self._db_ref.child('settings').get()
                if firebase_settings:
                    self._settings = firebase_settings
                    logger.info("Settings loaded from Firebase")
                    return
                else:
                    # First time - initialize from env and save to Firebase
                    logger.info("No settings in Firebase - initializing from environment")
                    self._settings = self._get_defaults_with_env()
                    self._save_to_firebase()
                    return
            
            logger.warning("Firebase not available - using empty settings")
            self._settings = json.loads(json.dumps(DEFAULT_SETTINGS))
                    
        except Exception as e:
            logger.error(f"Error loading settings from Firebase: {e}")
            self._settings = json.loads(json.dumps(DEFAULT_SETTINGS))
        
    def _get_defaults_with_env(self) -> Dict[str, Any]:
        """Get default settings, overriding with environment variables"""
        settings = json.loads(json.dumps(DEFAULT_SETTINGS))  # Deep copy
        
        # Override with environment variables if they exist
        env_mappings = {
            ("telegram", "api_id"): ("TELEGRAM_API_ID", int),
            ("telegram", "api_hash"): ("TELEGRAM_API_HASH", str),
            ("telegram", "phone_number"): ("TELEGRAM_PHONE", str),
            ("telegram", "signal_channels"): ("SIGNAL_CHANNELS", lambda x: [c.strip() for c in x.split(",")] if x else []),
            ("telegram", "notification_channel"): ("NOTIFICATION_CHANNEL", str),
            ("broker", "metaapi_token"): ("METAAPI_TOKEN", str),
            ("broker", "metaapi_account_id"): ("METAAPI_ACCOUNT_ID", str),
            ("broker", "server"): ("MT5_SERVER", str),
            ("broker", "login"): ("MT5_LOGIN", int),
            ("broker", "password"): ("MT5_PASSWORD", str),
            ("trading", "default_lot_size"): ("DEFAULT_LOT_SIZE", float),
            ("trading", "max_spread_pips"): ("MAX_SPREAD_PIPS", float),
            ("trading", "max_daily_drawdown_percent"): ("MAX_DAILY_DRAWDOWN", float),
            ("trading", "max_open_trades"): ("MAX_OPEN_TRADES", int),
            ("trading", "entry_zone_tolerance"): ("ENTRY_ZONE_TOLERANCE", float),
            ("trading", "execute_immediately"): ("EXECUTE_IMMEDIATELY", lambda x: x.lower() == "true"),
        }
        
        for (section, key), (env_var, converter) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                try:
                    settings[section][key] = converter(env_value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid env value for {env_var}: {e}")
        
        return settings
    
    def _save_to_firebase(self):
        """Save current settings to Firebase"""
        if not self._db_ref:
            logger.warning("Cannot save settings - Firebase not initialized")
            return
        try:
            self._db_ref.child('settings').set({
                **self._settings,
                '_updated_at': datetime.utcnow().isoformat()
            })
            logger.info("Settings saved to Firebase")
        except Exception as e:
            logger.error(f"Error saving settings to Firebase: {e}")
    

    
    def get(self, section: str, key: str, default=None):
        """Get a setting value"""
        try:
            return self._settings.get(section, {}).get(key, default)
        except:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set a setting value and save to Firebase"""
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][key] = value
        self._save_to_firebase()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all settings in a section"""
        return self._settings.get(section, {})
    
    def set_section(self, section: str, values: Dict[str, Any]):
        """Set all values in a section"""
        self._settings[section] = values
        self._save_to_firebase()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._settings.copy()
    
    def update_all(self, settings: Dict[str, Any]):
        """Update all settings at once"""
        # Deep merge to preserve structure
        for section, values in settings.items():
            if section.startswith('_'):
                continue  # Skip metadata fields
            if section in self._settings and isinstance(values, dict):
                self._settings[section].update(values)
            else:
                self._settings[section] = values
        self._save_to_firebase()
    
    def reload_from_firebase(self):
        """Force reload settings from Firebase"""
        if not self._db_ref:
            logger.warning("Cannot reload - Firebase not initialized")
            return
        try:
            firebase_settings = self._db_ref.child('settings').get()
            if firebase_settings:
                self._settings = firebase_settings
                logger.info("Settings reloaded from Firebase")
        except Exception as e:
            logger.error(f"Error reloading from Firebase: {e}")
    
    # Convenience properties for common settings
    @property
    def telegram_api_id(self) -> int:
        return self.get("telegram", "api_id", 0)
    
    @property
    def telegram_api_hash(self) -> str:
        return self.get("telegram", "api_hash", "")
    
    @property
    def telegram_phone(self) -> str:
        return self.get("telegram", "phone_number", "")
    
    @property
    def signal_channels(self) -> List[str]:
        channels = self.get("telegram", "signal_channels", [])
        return [c for c in channels if c]  # Filter empty strings
    
    @property
    def notification_channel(self) -> str:
        return self.get("telegram", "notification_channel", "")
    
    @property
    def metaapi_token(self) -> str:
        return self.get("broker", "metaapi_token", "")
    
    @property
    def metaapi_account_id(self) -> str:
        return self.get("broker", "metaapi_account_id", "")
    
    @property
    def default_lot_size(self) -> float:
        return self.get("trading", "default_lot_size", 0.01)
    
    @property
    def max_spread_pips(self) -> float:
        return self.get("trading", "max_spread_pips", 10.0)
    
    @property
    def max_open_trades(self) -> int:
        return self.get("trading", "max_open_trades", 10)
    
    @property
    def max_daily_drawdown_percent(self) -> float:
        return self.get("trading", "max_daily_drawdown_percent", 5.0)
    
    @property
    def symbol_max_spreads(self) -> Dict[str, float]:
        return self.get("trading", "symbol_max_spreads", {})
    
    @property
    def execute_immediately(self) -> bool:
        return self.get("trading", "execute_immediately", True)


# Global instance
firebase_settings = FirebaseSettings()
