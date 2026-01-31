"""
Data models for the trading system
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class TradeDirection(Enum):
    """Trade direction enum"""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(Enum):
    """Trade status enum"""
    WAITING = "waiting"          # Waiting for price to enter zone
    PENDING = "pending"          # Pending order placed
    ACTIVE = "active"            # Trade is active
    TP1_HIT = "tp1_hit"          # TP1 reached, partial close done
    TP2_HIT = "tp2_hit"          # TP2 reached, partial close done
    TP3_HIT = "tp3_hit"          # TP3 reached, fully closed
    SL_HIT = "sl_hit"            # Stop loss hit
    BREAKEVEN = "breakeven"      # SL moved to breakeven
    CLOSED = "closed"            # Manually closed
    CANCELLED = "cancelled"      # Signal cancelled
    FAILED = "failed"            # Execution failed
    REJECTED = "rejected"        # Rejected by risk manager


class SignalType(Enum):
    """Signal type enum"""
    NEW_TRADE = "new_trade"
    UPDATE_SL = "update_sl"
    UPDATE_TP = "update_tp"
    CLOSE_TRADE = "close_trade"
    PARTIAL_CLOSE = "partial_close"
    BREAKEVEN = "breakeven"
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    TP3_HIT = "tp3_hit"
    SL_HIT = "sl_hit"
    CANCEL = "cancel"
    UNKNOWN = "unknown"  # Non-signal messages (announcements, chat, etc.)


@dataclass
class Signal:
    """Parsed signal from Telegram"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_type: SignalType = SignalType.NEW_TRADE
    symbol: str = ""
    direction: Optional[TradeDirection] = None
    entry_min: Optional[float] = None
    entry_max: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    lot_size: Optional[float] = None
    raw_message: str = ""
    channel_id: str = ""
    message_id: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    parsed_successfully: bool = False
    parse_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "signal_type": self.signal_type.value,
            "symbol": self.symbol,
            "direction": self.direction.value if self.direction else None,
            "entry_min": self.entry_min,
            "entry_max": self.entry_max,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "take_profit_3": self.take_profit_3,
            "lot_size": self.lot_size,
            "raw_message": self.raw_message,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "parsed_successfully": self.parsed_successfully,
            "parse_errors": self.parse_errors
        }


@dataclass
class Trade:
    """Trade object with full state management"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_id: str = ""
    
    # Trade details
    symbol: str = ""
    direction: Optional[TradeDirection] = None
    entry_min: Optional[float] = None
    entry_max: Optional[float] = None
    entry_price: Optional[float] = None  # Actual entry price
    stop_loss: Optional[float] = None
    original_stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    
    # Lot management
    initial_lot_size: float = 0.0
    current_lot_size: float = 0.0
    tp1_lot_size: float = 0.0  # Lot to close at TP1
    tp2_lot_size: float = 0.0  # Lot to close at TP2
    tp3_lot_size: float = 0.0  # Lot to close at TP3
    
    # Broker order IDs
    order_ticket: Optional[int] = None
    position_ticket: Optional[int] = None
    position_tickets: List[dict] = field(default_factory=list)  # [{"ticket": int, "tp": int, "lot": float, "tp_price": float, "closed": bool}]
    
    # Status tracking
    status: TradeStatus = TradeStatus.WAITING
    breakeven_applied: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    opened_at: Optional[datetime] = None
    tp1_hit_at: Optional[datetime] = None
    tp2_hit_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # P&L tracking
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    current_price: Optional[float] = None  # Live market price
    commission: float = 0.0
    swap: float = 0.0
    
    # Metadata
    channel_id: str = ""
    message_ids: List[int] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    # Rejection/failure details
    rejection_reason: str = ""
    market_price_at_signal: Optional[float] = None
    spread_at_signal: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "direction": self.direction.value if self.direction else None,
            "entry_min": self.entry_min,
            "entry_max": self.entry_max,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "original_stop_loss": self.original_stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "take_profit_3": self.take_profit_3,
            "take_profit": self.take_profit_1,  # Alias for dashboard
            "initial_lot_size": self.initial_lot_size,
            "current_lot_size": self.current_lot_size,
            "lot_size": self.current_lot_size,  # Alias for dashboard
            "order_ticket": self.order_ticket,
            "position_ticket": self.position_ticket,
            "position_tickets": self.position_tickets,
            "status": self.status.value,
            "breakeven_applied": self.breakeven_applied,
            "created_at": self.created_at.isoformat(),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "profit": self.unrealized_pnl,  # Alias for dashboard
            "channel_id": self.channel_id,
            "notes": self.notes,
            "rejection_reason": self.rejection_reason,
            "market_price_at_signal": self.market_price_at_signal,
            "spread_at_signal": self.spread_at_signal
        }
    
    @classmethod
    def from_signal(cls, signal: Signal, lot_size: float) -> "Trade":
        """Create a trade from a signal"""
        trade = cls(
            signal_id=signal.id,
            symbol=signal.symbol,
            direction=signal.direction,
            entry_min=signal.entry_min,
            entry_max=signal.entry_max,
            stop_loss=signal.stop_loss,
            original_stop_loss=signal.stop_loss,
            take_profit_1=signal.take_profit_1,
            take_profit_2=signal.take_profit_2,
            take_profit_3=signal.take_profit_3,
            initial_lot_size=lot_size,
            current_lot_size=lot_size,
            channel_id=signal.channel_id,
            message_ids=[signal.message_id]
        )
        return trade


@dataclass
class AccountInfo:
    """Broker account information"""
    balance: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    free_margin: float = 0.0
    margin_level: float = 0.0
    profit: float = 0.0
    currency: str = "USD"
    leverage: int = 100
    server: str = ""
    login: int = 0
    name: str = ""
    
    # Daily tracking
    daily_start_balance: float = 0.0
    daily_pnl: float = 0.0
    daily_drawdown_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance": self.balance,
            "equity": self.equity,
            "margin": self.margin,
            "free_margin": self.free_margin,
            "margin_level": self.margin_level,
            "profit": self.profit,
            "currency": self.currency,
            "leverage": self.leverage,
            "server": self.server,
            "login": self.login,
            "name": self.name,
            "daily_pnl": self.daily_pnl,
            "daily_drawdown_percent": self.daily_drawdown_percent
        }


@dataclass
class SymbolInfo:
    """Symbol/instrument information"""
    name: str = ""
    description: str = ""
    point: float = 0.0
    digits: int = 0
    spread: int = 0
    spread_float: float = 0.0
    tick_size: float = 0.0
    tick_value: float = 0.0
    volume_min: float = 0.0
    volume_max: float = 0.0
    volume_step: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    
    def spread_in_pips(self) -> float:
        """Calculate spread in pips"""
        if self.digits in [3, 5]:  # JPY pairs or 5-digit brokers
            return self.spread_float / 10
        return self.spread_float


@dataclass
class NewsEvent:
    """Economic news event"""
    id: str = ""
    title: str = ""
    country: str = ""
    currency: str = ""
    impact: str = ""  # low, medium, high
    forecast: str = ""
    previous: str = ""
    actual: str = ""
    event_time: datetime = field(default_factory=datetime.utcnow)
    
    def is_high_impact(self) -> bool:
        return self.impact.lower() == "high"
