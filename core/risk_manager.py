"""
Risk management system for trade filtering and protection.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import aiohttp

from models.trade import Signal, NewsEvent, TradeDirection
from broker import broker_client
from config.settings import config

logger = logging.getLogger("evobot.risk")


class RiskManager:
    """
    Risk management system that checks various conditions
    before allowing trade execution.
    """
    
    def __init__(self):
        self.daily_start_balance: float = 0.0
        self.daily_pnl: float = 0.0
        self.news_events: List[NewsEvent] = []
        self._news_last_fetch: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Initialize risk manager"""
        logger.info("Starting risk manager...")
        
        # Get initial balance
        account = await broker_client.get_account_info()
        if account:
            self.daily_start_balance = account.balance
        
        # Fetch news calendar
        await self._fetch_news_calendar()
        
        logger.info(f"Risk manager started. Daily start balance: {self.daily_start_balance}")
    
    async def stop(self):
        """Stop risk manager"""
        if self._session:
            await self._session.close()
    
    async def can_trade(self, signal: Signal) -> Tuple[bool, str]:
        """
        Check if a trade should be allowed based on risk parameters.
        
        Returns:
            (can_trade, reason)
        """
        # Check trading hours
        if not self._is_trading_hours():
            return False, "Outside trading hours"
        
        # Check daily drawdown
        drawdown_ok, drawdown = await self._check_daily_drawdown()
        if not drawdown_ok:
            return False, f"Daily drawdown limit exceeded: {drawdown:.2f}%"
        
        # Check spread
        spread_ok, spread = await broker_client.check_spread(signal.symbol)
        if not spread_ok:
            return False, f"Spread too high: {spread:.1f} pips"
        
        # Check news events
        if config.risk.avoid_high_impact_news:
            news_ok, news_reason = await self._check_news_events(signal.symbol)
            if not news_ok:
                return False, news_reason
        
        # Check weekend
        if config.risk.close_trades_before_weekend:
            if self._is_near_weekend_close():
                return False, "Near weekend close"
        
        return True, "All risk checks passed"
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        now = datetime.utcnow()
        hour = now.hour
        
        # Check configured trading hours
        if config.risk.trading_start_hour <= hour < config.risk.trading_end_hour:
            return True
        
        # Handle overnight sessions (e.g., 22:00 - 06:00)
        if config.risk.trading_start_hour > config.risk.trading_end_hour:
            if hour >= config.risk.trading_start_hour or hour < config.risk.trading_end_hour:
                return True
        
        return False
    
    async def _check_daily_drawdown(self) -> Tuple[bool, float]:
        """
        Check if daily drawdown is within limits.
        
        Returns:
            (within_limit, drawdown_percent)
        """
        account = await broker_client.get_account_info()
        if not account:
            return True, 0.0
        
        # Reset daily balance at midnight UTC
        if self._should_reset_daily():
            self.daily_start_balance = account.balance
            logger.info(f"Daily balance reset to {account.balance}")
        
        if self.daily_start_balance <= 0:
            return True, 0.0
        
        current_equity = account.equity
        drawdown = ((self.daily_start_balance - current_equity) / self.daily_start_balance) * 100
        
        self.daily_pnl = current_equity - self.daily_start_balance
        
        if drawdown >= config.trading.max_daily_drawdown_percent:
            logger.warning(f"Daily drawdown limit hit: {drawdown:.2f}%")
            return False, drawdown
        
        return True, drawdown
    
    def _should_reset_daily(self) -> bool:
        """Check if daily stats should be reset"""
        # Simple check - reset if it's a new day
        # In production, you'd track the last reset date
        now = datetime.utcnow()
        return now.hour == 0 and now.minute < 5
    
    def _is_near_weekend_close(self) -> bool:
        """Check if we're near weekend market close"""
        now = datetime.utcnow()
        
        # Friday after configured close hour
        if now.weekday() == 4 and now.hour >= config.risk.weekend_close_hour_friday:
            return True
        
        # Saturday or Sunday
        if now.weekday() in [5, 6]:
            return True
        
        return False
    
    async def _check_news_events(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if there are high-impact news events that could affect the trade.
        
        Returns:
            (can_trade, reason)
        """
        # Refresh news if stale
        if self._news_last_fetch is None or \
           datetime.utcnow() - self._news_last_fetch > timedelta(hours=1):
            await self._fetch_news_calendar()
        
        now = datetime.utcnow()
        
        # Get currencies from symbol
        currencies = self._get_currencies_from_symbol(symbol)
        
        for event in self.news_events:
            if not event.is_high_impact():
                continue
            
            if event.currency not in currencies:
                continue
            
            # Check if event is within blackout window
            time_to_event = (event.event_time - now).total_seconds() / 60
            
            if -config.risk.news_blackout_minutes_after <= time_to_event <= config.risk.news_blackout_minutes_before:
                return False, f"High-impact news: {event.title} ({event.currency})"
        
        return True, "No conflicting news"
    
    def _get_currencies_from_symbol(self, symbol: str) -> List[str]:
        """Extract currencies from symbol"""
        # Handle common formats
        symbol = symbol.upper().replace("/", "").replace("_", "")
        
        # Special cases
        if symbol in ["XAUUSD", "GOLD"]:
            return ["XAU", "USD"]
        if symbol in ["XAGUSD", "SILVER"]:
            return ["XAG", "USD"]
        
        # Standard forex pairs
        if len(symbol) >= 6:
            return [symbol[:3], symbol[3:6]]
        
        return []
    
    async def _fetch_news_calendar(self):
        """Fetch economic news calendar from API"""
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            # Using ForexFactory-style API (you can replace with your preferred source)
            # This is a placeholder - implement with actual news API
            
            # Example with investing.com style API:
            # url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            
            # For now, create empty list
            self.news_events = []
            self._news_last_fetch = datetime.utcnow()
            
            logger.debug("News calendar fetched")
            
        except Exception as e:
            logger.error(f"Failed to fetch news calendar: {e}")
    
    def calculate_lot_size(
        self,
        symbol: str,
        stop_loss_pips: float,
        risk_percent: Optional[float] = None
    ) -> float:
        """
        Calculate lot size based on risk percentage and stop loss.
        
        Args:
            symbol: Trading symbol
            stop_loss_pips: Stop loss distance in pips
            risk_percent: Risk percentage (default from config)
            
        Returns:
            Calculated lot size
        """
        risk_percent = risk_percent or config.risk.max_risk_percent_per_trade
        
        if not broker_client.account_info:
            return config.trading.default_lot_size
        
        account_balance = broker_client.account_info.balance
        risk_amount = account_balance * (risk_percent / 100)
        
        # Get pip value for the symbol
        symbol_info = broker_client.symbol_cache.get(symbol)
        if not symbol_info:
            return config.trading.default_lot_size
        
        # Calculate pip value for 1 lot
        pip_value = symbol_info.tick_value
        if symbol_info.digits in [3, 5]:  # 5-digit broker
            pip_value *= 10
        
        if stop_loss_pips <= 0 or pip_value <= 0:
            return config.trading.default_lot_size
        
        # Lot size = Risk Amount / (SL in pips * Pip value per lot)
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round to volume step
        if symbol_info.volume_step > 0:
            lot_size = round(lot_size / symbol_info.volume_step) * symbol_info.volume_step
        
        # Clamp to min/max
        lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
        
        return round(lot_size, 2)
    
    def get_risk_status(self) -> dict:
        """Get current risk status"""
        current_drawdown = 0
        if self.daily_start_balance > 0:
            current_drawdown = abs(min(0, self.daily_pnl)) / self.daily_start_balance * 100
        
        return {
            "daily_start_balance": self.daily_start_balance,
            "daily_pnl": self.daily_pnl,
            "current_drawdown": current_drawdown,
            "daily_drawdown_percent": (
                (self.daily_start_balance - (self.daily_start_balance + self.daily_pnl)) 
                / self.daily_start_balance * 100
                if self.daily_start_balance > 0 else 0
            ),
            "max_daily_drawdown": config.trading.max_daily_drawdown_percent,
            "trading_hours": f"{config.risk.trading_start_hour}:00 - {config.risk.trading_end_hour}:00 UTC",
            "is_trading_hours": self._is_trading_hours(),
            "avoid_news": config.risk.avoid_high_impact_news,
            "upcoming_news_count": len([e for e in self.news_events if e.is_high_impact()])
        }


# Singleton instance
risk_manager = RiskManager()
