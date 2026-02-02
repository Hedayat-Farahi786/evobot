"""Signal message model for storing parsed trading signals with execution tracking"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


@dataclass
class SignalMessage:
    """Parsed trading signal from Telegram with execution tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str = ""
    channel_name: str = ""
    message_id: int = 0
    text: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sender_name: Optional[str] = None
    
    # Signal details
    symbol: str = ""
    direction: Optional[str] = None
    signal_type: str = ""
    entry_min: Optional[float] = None
    entry_max: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    
    # Execution tracking
    trade_id: Optional[str] = None
    executed: bool = False
    execution_time: Optional[datetime] = None
    actual_entry_price: Optional[float] = None
    lot_size: Optional[float] = None
    
    # Outcome tracking
    status: str = "pending"  # pending, active, tp1_hit, tp2_hit, tp3_hit, sl_hit, closed, cancelled
    tp1_hit: bool = False
    tp1_hit_time: Optional[datetime] = None
    tp1_profit: Optional[float] = None
    tp2_hit: bool = False
    tp2_hit_time: Optional[datetime] = None
    tp2_profit: Optional[float] = None
    tp3_hit: bool = False
    tp3_hit_time: Optional[datetime] = None
    tp3_profit: Optional[float] = None
    sl_hit: bool = False
    sl_hit_time: Optional[datetime] = None
    sl_loss: Optional[float] = None
    
    # Final results
    closed_time: Optional[datetime] = None
    total_profit: Optional[float] = None
    total_pips: Optional[float] = None
    duration_minutes: Optional[int] = None
    
    # Analytics
    win: Optional[bool] = None  # True if profit > 0, False if loss
    risk_reward_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "message_id": self.message_id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "sender_name": self.sender_name,
            "symbol": self.symbol,
            "direction": self.direction,
            "signal_type": self.signal_type,
            "entry_min": self.entry_min,
            "entry_max": self.entry_max,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "take_profit_3": self.take_profit_3,
            "trade_id": self.trade_id,
            "executed": self.executed,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "actual_entry_price": self.actual_entry_price,
            "lot_size": self.lot_size,
            "status": self.status,
            "tp1_hit": self.tp1_hit,
            "tp1_hit_time": self.tp1_hit_time.isoformat() if self.tp1_hit_time else None,
            "tp1_profit": self.tp1_profit,
            "tp2_hit": self.tp2_hit,
            "tp2_hit_time": self.tp2_hit_time.isoformat() if self.tp2_hit_time else None,
            "tp2_profit": self.tp2_profit,
            "tp3_hit": self.tp3_hit,
            "tp3_hit_time": self.tp3_hit_time.isoformat() if self.tp3_hit_time else None,
            "tp3_profit": self.tp3_profit,
            "sl_hit": self.sl_hit,
            "sl_hit_time": self.sl_hit_time.isoformat() if self.sl_hit_time else None,
            "sl_loss": self.sl_loss,
            "closed_time": self.closed_time.isoformat() if self.closed_time else None,
            "total_profit": self.total_profit,
            "total_pips": self.total_pips,
            "duration_minutes": self.duration_minutes,
            "win": self.win,
            "risk_reward_ratio": self.risk_reward_ratio
        }
