"""Trade outcome tracker for signal analytics"""
import logging
from datetime import datetime
from core.signal_storage import signal_storage

logger = logging.getLogger("evobot.signal_tracker")


class SignalOutcomeTracker:
    """Track trade outcomes and update signal records"""
    
    def __init__(self):
        self.trade_to_signal_map = {}  # trade_id -> signal_id
    
    def handle_trade_event(self, event_type: str, trade):
        """Handle trade events and update corresponding signal"""
        # Find signal_id for this trade
        signal_id = None
        for sig_id, trd_id in signal_storage.signal_to_trade_map.items():
            if trd_id == trade.id:
                signal_id = sig_id
                break
        
        if not signal_id:
            return
        
        updates = {}
        
        if event_type == "TP1_HIT":
            updates = {
                "tp1_hit": True,
                "tp1_hit_time": datetime.utcnow().isoformat(),
                "tp1_profit": trade.realized_pnl,
                "status": "tp1_hit"
            }
        
        elif event_type == "TP2_HIT":
            updates = {
                "tp2_hit": True,
                "tp2_hit_time": datetime.utcnow().isoformat(),
                "tp2_profit": trade.realized_pnl,
                "status": "tp2_hit"
            }
        
        elif event_type == "TP3_HIT":
            updates = {
                "tp3_hit": True,
                "tp3_hit_time": datetime.utcnow().isoformat(),
                "tp3_profit": trade.realized_pnl,
                "status": "tp3_hit"
            }
        
        elif event_type == "SL_HIT":
            updates = {
                "sl_hit": True,
                "sl_hit_time": datetime.utcnow().isoformat(),
                "sl_loss": trade.realized_pnl,
                "status": "sl_hit"
            }
        
        elif event_type == "CLOSED":
            duration = None
            if trade.opened_at and trade.closed_at:
                duration = int((trade.closed_at - trade.opened_at).total_seconds() / 60)
            
            # Calculate pips
            pips = 0
            if trade.entry_price and trade.current_price:
                price_diff = abs(trade.current_price - trade.entry_price)
                # Simplified pip calculation
                if "JPY" in trade.symbol:
                    pips = price_diff * 100
                else:
                    pips = price_diff * 10000
            
            # Calculate risk/reward
            rr_ratio = None
            if trade.stop_loss and trade.take_profit_1 and trade.entry_price:
                risk = abs(trade.entry_price - trade.stop_loss)
                reward = abs(trade.take_profit_1 - trade.entry_price)
                if risk > 0:
                    rr_ratio = reward / risk
            
            updates = {
                "closed_time": datetime.utcnow().isoformat(),
                "total_profit": trade.realized_pnl,
                "total_pips": pips,
                "duration_minutes": duration,
                "win": trade.realized_pnl > 0,
                "risk_reward_ratio": rr_ratio,
                "status": "closed"
            }
        
        if updates:
            signal_storage.update_trade_outcome(signal_id, updates)
            logger.info(f"Updated signal {signal_id} with {event_type}")


# Singleton instance
signal_outcome_tracker = SignalOutcomeTracker()
