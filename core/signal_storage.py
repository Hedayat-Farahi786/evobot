"""Signal message storage service"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from models.signal_message import SignalMessage

logger = logging.getLogger("evobot.signal_storage")


class SignalMessageStorage:
    """Store and retrieve signal messages with execution tracking"""
    
    def __init__(self):
        self.messages: List[SignalMessage] = []
        self.firebase_db = None
        self.signal_to_trade_map: Dict[str, str] = {}  # signal_id -> trade_id
        
    def set_firebase(self, db_root):
        """Set Firebase database reference"""
        try:
            # Create a child reference for signal_messages
            self.firebase_db = db_root.child('signal_messages') if db_root else None
            if self.firebase_db:
                logger.info("Firebase reference set for signal storage at /signal_messages")
        except Exception as e:
            logger.error(f"Failed to set Firebase reference: {e}")
            self.firebase_db = None
        
    def add_message(self, message: SignalMessage):
        """Add a new signal message"""
        self.messages.insert(0, message)
        
        if len(self.messages) > 500:
            self.messages = self.messages[:500]
        
        if self.firebase_db:
            try:
                self.firebase_db.child(message.id).set(message.to_dict())
                logger.info(f"Signal message {message.id} saved to Firebase")
            except Exception as e:
                logger.error(f"Failed to save message to Firebase: {e}")
    
    def update_message(self, signal_id: str, updates: Dict):
        """Update an existing signal message"""
        for msg in self.messages:
            if msg.id == signal_id:
                for key, value in updates.items():
                    if hasattr(msg, key):
                        setattr(msg, key, value)
                
                # Always save complete updated object to Firebase
                if self.firebase_db:
                    try:
                        self.firebase_db.child(signal_id).set(msg.to_dict())
                        logger.info(f"Updated signal {signal_id} in Firebase")
                    except Exception as e:
                        logger.error(f"Failed to update message in Firebase: {e}")
                break
    
    def link_trade(self, signal_id: str, trade_id: str):
        """Link a signal to its executed trade"""
        self.signal_to_trade_map[signal_id] = trade_id
        self.update_message(signal_id, {
            "trade_id": trade_id,
            "executed": True,
            "execution_time": datetime.utcnow().isoformat(),
            "status": "active"
        })
    
    def update_trade_outcome(self, signal_id: str, outcome: Dict):
        """Update signal with trade outcome (TP/SL hits)"""
        self.update_message(signal_id, outcome)
    
    def get_messages(self, limit: int = 100) -> List[SignalMessage]:
        """Get recent messages"""
        return self.messages[:limit]
    
    def get_messages_by_channel(self, channel_id: str, limit: int = 100) -> List[SignalMessage]:
        """Get messages from specific channel"""
        filtered = [m for m in self.messages if m.channel_id == channel_id]
        return filtered[:limit]
    
    def get_channel_analytics(self, channel_id: str) -> Dict:
        """Get analytics for a specific channel"""
        all_channel_signals = [m for m in self.messages if m.channel_id == channel_id]
        channel_signals = [m for m in all_channel_signals if m.executed]
        
        if not all_channel_signals:
            return {
                "total_signals": 0,
                "executed_signals": 0,
                "win_rate": 0,
                "total_profit": 0,
                "avg_profit": 0
            }
        
        closed_signals = [s for s in channel_signals if s.status in ['tp3_hit', 'tp2_hit', 'tp1_hit', 'sl_hit', 'closed']]
        wins = [s for s in closed_signals if s.win or (s.total_profit and s.total_profit > 0)]
        
        tp1_hits = sum(1 for s in channel_signals if s.tp1_hit)
        tp2_hits = sum(1 for s in channel_signals if s.tp2_hit)
        tp3_hits = sum(1 for s in channel_signals if s.tp3_hit)
        sl_hits = sum(1 for s in channel_signals if s.sl_hit)
        
        total_profit = sum(s.total_profit for s in closed_signals if s.total_profit)
        
        return {
            "total_signals": len(all_channel_signals),
            "executed_signals": len(channel_signals),
            "closed_signals": len(closed_signals),
            "win_rate": (len(wins) / len(closed_signals) * 100) if closed_signals else 0,
            "total_profit": total_profit,
            "avg_profit": total_profit / len(closed_signals) if closed_signals else 0,
            "tp1_hit_count": tp1_hits,
            "tp2_hit_count": tp2_hits,
            "tp3_hit_count": tp3_hits,
            "sl_hit_count": sl_hits,
            "tp1_rate": (tp1_hits / len(channel_signals) * 100) if channel_signals else 0,
            "tp2_rate": (tp2_hits / len(channel_signals) * 100) if channel_signals else 0,
            "tp3_rate": (tp3_hits / len(channel_signals) * 100) if channel_signals else 0
        }


# Singleton instance
signal_storage = SignalMessageStorage()
