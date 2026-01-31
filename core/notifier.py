"""
Notification system for trade events.
Sends notifications to Telegram and other channels.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from models.trade import Trade, TradeStatus, TradeDirection
from config.settings import config

logger = logging.getLogger("evobot.notifier")


class Notifier:
    """
    Handles notifications for trade events.
    Sends updates to Telegram notification channel.
    """
    
    def __init__(self):
        self._telegram_client = None
        self._enabled = bool(config.telegram.notification_channel)
    
    def set_telegram_client(self, client):
        """Set the Telegram client for sending notifications"""
        self._telegram_client = client
    
    async def notify_trade_opened(self, trade: Trade, ticket: int):
        """Notify when a trade is opened"""
        if not self._enabled:
            return
        
        emoji = "🟢" if trade.direction == TradeDirection.BUY else "🔴"
        direction = trade.direction.value if trade.direction else "N/A"
        
        message = f"""
{emoji} <b>Trade Opened</b>

<b>Symbol:</b> {trade.symbol}
<b>Direction:</b> {direction}
<b>Entry:</b> {trade.entry_price:.5f}
<b>Lot Size:</b> {trade.initial_lot_size}
<b>Ticket:</b> #{ticket}

<b>Stop Loss:</b> {trade.stop_loss:.5f if trade.stop_loss else 'N/A'}
<b>TP1:</b> {trade.take_profit_1:.5f if trade.take_profit_1 else 'N/A'}
<b>TP2:</b> {trade.take_profit_2:.5f if trade.take_profit_2 else 'N/A'}
<b>TP3:</b> {trade.take_profit_3:.5f if trade.take_profit_3 else 'N/A'}

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_tp_hit(self, trade: Trade, tp_level: int, partial_close: float):
        """Notify when a TP is hit"""
        if not self._enabled:
            return
        
        emoji = "🎯" if tp_level < 3 else "🏆"
        
        message = f"""
{emoji} <b>TP{tp_level} Hit!</b>

<b>Symbol:</b> {trade.symbol}
<b>Direction:</b> {trade.direction.value if trade.direction else 'N/A'}
<b>Partial Close:</b> {partial_close} lots
<b>Remaining:</b> {trade.current_lot_size} lots

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_breakeven(self, trade: Trade, new_sl: float):
        """Notify when trade moved to breakeven"""
        if not self._enabled:
            return
        
        message = f"""
🔒 <b>Moved to Breakeven</b>

<b>Symbol:</b> {trade.symbol}
<b>Direction:</b> {trade.direction.value if trade.direction else 'N/A'}
<b>Entry:</b> {trade.entry_price:.5f if trade.entry_price else 'N/A'}
<b>New SL:</b> {new_sl:.5f}

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_sl_hit(self, trade: Trade):
        """Notify when SL is hit"""
        if not self._enabled:
            return
        
        message = f"""
❌ <b>Stop Loss Hit</b>

<b>Symbol:</b> {trade.symbol}
<b>Direction:</b> {trade.direction.value if trade.direction else 'N/A'}
<b>Entry:</b> {trade.entry_price:.5f if trade.entry_price else 'N/A'}
<b>SL:</b> {trade.stop_loss:.5f if trade.stop_loss else 'N/A'}
<b>P&L:</b> {trade.realized_pnl:.2f}

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_trade_closed(self, trade: Trade, reason: str = "Manual"):
        """Notify when trade is closed"""
        if not self._enabled:
            return
        
        emoji = "✅" if trade.realized_pnl >= 0 else "❌"
        
        message = f"""
{emoji} <b>Trade Closed</b>

<b>Symbol:</b> {trade.symbol}
<b>Direction:</b> {trade.direction.value if trade.direction else 'N/A'}
<b>Reason:</b> {reason}
<b>P&L:</b> {trade.realized_pnl:.2f}

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_signal_received(self, symbol: str, direction: str, entry: str):
        """Notify when a new signal is received"""
        if not self._enabled:
            return
        
        emoji = "📈" if direction.upper() == "BUY" else "📉"
        
        message = f"""
{emoji} <b>New Signal Received</b>

<b>Symbol:</b> {symbol}
<b>Direction:</b> {direction}
<b>Entry:</b> {entry}

Processing...
"""
        await self._send_notification(message)
    
    async def notify_risk_alert(self, alert_type: str, message_text: str):
        """Notify risk-related alerts"""
        if not self._enabled:
            return
        
        message = f"""
⚠️ <b>Risk Alert: {alert_type}</b>

{message_text}

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_system_status(self, status: str, details: str = ""):
        """Notify system status changes"""
        if not self._enabled:
            return
        
        emoji = "✅" if "started" in status.lower() or "connected" in status.lower() else "⚠️"
        
        message = f"""
{emoji} <b>System Status: {status}</b>

{details}

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self._send_notification(message)
    
    async def notify_daily_summary(self, stats: dict):
        """Send daily trading summary"""
        if not self._enabled:
            return
        
        win_rate = stats.get('win_rate', 0)
        emoji = "🏆" if win_rate >= 60 else "📊"
        
        message = f"""
{emoji} <b>Daily Trading Summary</b>

<b>Total Trades:</b> {stats.get('total_trades', 0)}
<b>Winning:</b> {stats.get('winning_trades', 0)}
<b>Losing:</b> {stats.get('losing_trades', 0)}
<b>Win Rate:</b> {win_rate:.1f}%
<b>Total P&L:</b> ${stats.get('total_pnl', 0):.2f}

<b>Active Trades:</b> {stats.get('active_trades', 0)}

🕐 {datetime.utcnow().strftime('%Y-%m-%d')}
"""
        await self._send_notification(message)
    
    async def _send_notification(self, message: str):
        """Send notification to Telegram"""
        if not self._telegram_client or not config.telegram.notification_channel:
            return
        
        try:
            await self._telegram_client.send_notification(message.strip())
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def handle_trade_event(self, event: str, trade: Trade, data: dict = None):
        """Handle trade events from trade manager"""
        data = data or {}
        
        if event == "OPENED":
            await self.notify_trade_opened(trade, data.get("ticket", 0))
        elif event == "TP1_HIT":
            await self.notify_tp_hit(trade, 1, data.get("partial_close", 0))
        elif event == "TP2_HIT":
            await self.notify_tp_hit(trade, 2, data.get("partial_close", 0))
        elif event == "TP3_HIT":
            await self.notify_tp_hit(trade, 3, data.get("partial_close", 0))
        elif event == "BREAKEVEN":
            await self.notify_breakeven(trade, data.get("new_sl", 0))
        elif event == "SL_HIT":
            await self.notify_sl_hit(trade)
        elif event == "CLOSED":
            await self.notify_trade_closed(trade)


# Singleton instance
notifier = Notifier()
