"""
Configuration settings for the EvoBot Trading System
Now backed by Firebase for dynamic configuration from dashboard
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# Import Firebase settings (initialized later)
_firebase_settings = None

def get_firebase_settings():
    """Get Firebase settings instance (lazy load to avoid circular imports)"""
    global _firebase_settings
    if _firebase_settings is None:
        try:
            from core.firebase_settings import firebase_settings
            _firebase_settings = firebase_settings
        except ImportError:
            _firebase_settings = None
    return _firebase_settings


class TelegramConfig:
    """Telegram API configuration - backed by Firebase"""
    
    @property
    def api_id(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.telegram_api_id
        return int(os.getenv("TELEGRAM_API_ID", "0"))
    
    @property
    def api_hash(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.telegram_api_hash
        return os.getenv("TELEGRAM_API_HASH", "")
    
    @property
    def phone_number(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.telegram_phone
        return os.getenv("TELEGRAM_PHONE", "")
    
    @property
    def session_name(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("telegram", "session_name", "evobot_session")
        return os.getenv("TELEGRAM_SESSION", "evobot_session")
    
    @property
    def signal_channels(self) -> List[str]:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.signal_channels
        channels = os.getenv("SIGNAL_CHANNELS", "")
        return channels.split(",") if channels else []
    
    @property
    def notification_channel(self) -> Optional[str]:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.notification_channel or None
        return os.getenv("NOTIFICATION_CHANNEL", None)
    
    @property
    def reconnect_delay(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("telegram", "reconnect_delay", 5)
        return 5
    
    @property
    def max_reconnect_attempts(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("telegram", "max_reconnect_attempts", 999)
        return 999


class BrokerConfig:
    """MT5/MetaApi Broker configuration - backed by Firebase"""
    
    @property
    def broker_type(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "broker_type", "metaapi")
        return os.getenv("BROKER_TYPE", "metaapi")
    
    @property
    def server(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "server", "")
        return os.getenv("MT5_SERVER", "")
    
    @property
    def login(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "login", 0)
        return int(os.getenv("MT5_LOGIN", "0"))
    
    @property
    def password(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "password", "")
        return os.getenv("MT5_PASSWORD", "")
    
    @property
    def path(self) -> str:
        return os.getenv("MT5_PATH", "")
    
    @property
    def metaapi_token(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.metaapi_token
        return os.getenv("METAAPI_TOKEN", "")
    
    @property
    def metaapi_account_id(self) -> str:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.metaapi_account_id
        return os.getenv("METAAPI_ACCOUNT_ID", "")
    
    @property
    def timeout(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "timeout", 60000)
        return 60000
    
    @property
    def retry_attempts(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "retry_attempts", 3)
        return 3
    
    @property
    def retry_delay(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("broker", "retry_delay", 1.0)
        return 1.0


class TradingConfig:
    """Trading parameters configuration - backed by Firebase"""
    
    @property
    def symbols(self) -> List[str]:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "symbols", [
                "XAUUSD", "GBPUSD", "USDCAD", "EURUSD", "USDJPY",
                "GBPJPY", "AUDUSD", "NZDUSD", "USDCHF", "EURJPY"
            ])
        return ["XAUUSD", "GBPUSD", "USDCAD", "EURUSD", "USDJPY",
                "GBPJPY", "AUDUSD", "NZDUSD", "USDCHF", "EURJPY"]
    
    @property
    def default_lot_size(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.default_lot_size
        return float(os.getenv("DEFAULT_LOT_SIZE", "0.01"))
    
    @default_lot_size.setter
    def default_lot_size(self, value: float):
        fs = get_firebase_settings()
        if fs and fs._initialized:
            fs.set("trading", "default_lot_size", value)
    
    @property
    def max_spread_pips(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.max_spread_pips
        return float(os.getenv("MAX_SPREAD_PIPS", "10.0"))
    
    @max_spread_pips.setter
    def max_spread_pips(self, value: float):
        fs = get_firebase_settings()
        if fs and fs._initialized:
            fs.set("trading", "max_spread_pips", value)
    
    @property
    def max_daily_drawdown_percent(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.max_daily_drawdown_percent
        return float(os.getenv("MAX_DAILY_DRAWDOWN", "5.0"))
    
    @max_daily_drawdown_percent.setter
    def max_daily_drawdown_percent(self, value: float):
        fs = get_firebase_settings()
        if fs and fs._initialized:
            fs.set("trading", "max_daily_drawdown_percent", value)
    
    @property
    def max_open_trades(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.max_open_trades
        return int(os.getenv("MAX_OPEN_TRADES", "10"))
    
    @max_open_trades.setter
    def max_open_trades(self, value: int):
        fs = get_firebase_settings()
        if fs and fs._initialized:
            fs.set("trading", "max_open_trades", value)
    
    @property
    def symbol_max_spreads(self) -> Dict[str, float]:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.symbol_max_spreads
        return {
            "XAUUSD": 50.0,
            "XAGUSD": 30.0,
            "BTCUSD": 100.0,
            "US30": 50.0,
            "NAS100": 50.0,
        }
    
    @symbol_max_spreads.setter
    def symbol_max_spreads(self, value: Dict[str, float]):
        fs = get_firebase_settings()
        if fs and fs._initialized:
            fs.set("trading", "symbol_max_spreads", value)
    
    @property
    def tp1_close_percent(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "tp1_close_percent", 0.5)
        return 0.5
    
    @property
    def tp2_close_percent(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "tp2_close_percent", 0.3)
        return 0.3
    
    @property
    def tp3_close_percent(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "tp3_close_percent", 0.2)
        return 0.2
    
    @property
    def move_sl_to_breakeven_at_tp1(self) -> bool:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "move_sl_to_breakeven_at_tp1", True)
        return True
    
    @property
    def breakeven_offset_pips(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "breakeven_offset_pips", 1.0)
        return 1.0
    
    @property
    def entry_zone_tolerance(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "entry_zone_tolerance", 5.0)
        return float(os.getenv("ENTRY_ZONE_TOLERANCE", "5.0"))
    
    @property
    def execute_immediately(self) -> bool:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.execute_immediately
        return os.getenv("EXECUTE_IMMEDIATELY", "true").lower() == "true"
    
    @property
    def max_slippage(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "max_slippage", 30)
        return 30
    
    @property
    def use_pending_orders(self) -> bool:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("trading", "use_pending_orders", False)
        return False


class RiskConfig:
    """Risk management configuration - backed by Firebase"""
    
    @property
    def avoid_high_impact_news(self) -> bool:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "avoid_high_impact_news", True)
        return True
    
    @property
    def news_blackout_minutes_before(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "news_blackout_minutes_before", 30)
        return 30
    
    @property
    def news_blackout_minutes_after(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "news_blackout_minutes_after", 15)
        return 15
    
    @property
    def trading_start_hour(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "trading_start_hour", 0)
        return 0
    
    @property
    def trading_end_hour(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "trading_end_hour", 24)
        return 24
    
    @property
    def close_trades_before_weekend(self) -> bool:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "close_trades_before_weekend", False)
        return False
    
    @property
    def weekend_close_hour_friday(self) -> int:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "weekend_close_hour_friday", 21)
        return 21
    
    @property
    def max_risk_percent_per_trade(self) -> float:
        fs = get_firebase_settings()
        if fs and fs._initialized:
            return fs.get("risk", "max_risk_percent_per_trade", 2.0)
        return 2.0


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    trade_log_file: str = "trades.log"
    system_log_file: str = "system.log"
    error_log_file: str = "errors.log"
    max_log_size_mb: int = 10
    backup_count: int = 5


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    secret_key: str = os.getenv("DASHBOARD_SECRET", "change-this-secret-key")


class Config:
    """Main configuration class - backed by Firebase"""
    
    def __init__(self):
        self.telegram = TelegramConfig()
        self.broker = BrokerConfig()
        self.trading = TradingConfig()
        self.risk = RiskConfig()
        self.logging = LoggingConfig()
        self.dashboard = DashboardConfig()
    
    def save(self):
        """Save is now automatic via Firebase"""
        pass
    
    def reload(self):
        """Reload settings from Firebase"""
        fs = get_firebase_settings()
        if fs:
            fs.reload_from_firebase()


# Global config instance
config = Config()
