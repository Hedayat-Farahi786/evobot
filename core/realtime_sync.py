"""
Real-time synchronization service for seamless data flow
Coordinates MT5 -> Firebase -> WebSocket -> Dashboard
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("evobot.realtime_sync")


@dataclass
class RealtimeSnapshot:
    """Complete snapshot of current state"""
    account: Optional[Dict] = None
    positions: list = None
    stats: Optional[Dict] = None
    status: Optional[Dict] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.positions is None:
            self.positions = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class RealtimeSyncService:
    """Manages real-time data synchronization across all systems"""
    
    def __init__(self):
        self.firebase_service = None
        self.broker_client = None
        self.trade_manager = None
        self.websocket_broadcast = None
        self.bot_state = None
        
        self._sync_task = None
        self._running = False
        self._last_snapshot = RealtimeSnapshot()
        self._update_interval = 1.0  # 1 second updates
        self._heartbeat_counter = 0
        self._force_sync_every = 10  # Force full sync every 10 seconds
        
    def initialize(self, firebase_service, broker_client, trade_manager, websocket_broadcast, bot_state):
        """Initialize with required services"""
        self.firebase_service = firebase_service
        self.broker_client = broker_client
        self.trade_manager = trade_manager
        self.websocket_broadcast = websocket_broadcast
        self.bot_state = bot_state
        logger.info("Real-time sync service initialized")
    
    async def start(self):
        """Start real-time synchronization"""
        if self._running:
            return
        
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Real-time sync started - 1s update interval")
    
    async def stop(self):
        """Stop real-time synchronization"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Real-time sync stopped")
    
    async def _sync_loop(self):
        """Main synchronization loop"""
        while self._running:
            try:
                if self.bot_state and self.bot_state.is_running and self.bot_state.is_connected_mt5:
                    snapshot = await self._capture_snapshot()
                    
                    # Increment heartbeat counter
                    self._heartbeat_counter += 1
                    
                    # Force sync every N iterations or if changes detected
                    force_sync = (self._heartbeat_counter >= self._force_sync_every)
                    has_changes = self._has_changes(snapshot)
                    
                    if has_changes or force_sync:
                        await self._sync_snapshot(snapshot)
                        self._last_snapshot = snapshot
                        
                        if force_sync:
                            self._heartbeat_counter = 0
                            logger.debug("Heartbeat: Full sync completed")
                
                await asyncio.sleep(self._update_interval)
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(2)
    
    async def _capture_snapshot(self) -> RealtimeSnapshot:
        """Capture current state from MT5"""
        snapshot = RealtimeSnapshot()
        
        try:
            # Get account info
            if self.broker_client:
                account_info = await self.broker_client.get_account_info(force_refresh=True)
                if account_info:
                    snapshot.account = account_info.to_dict()
            
            # Get positions
            if self.broker_client:
                positions = await self.broker_client.get_positions(force_refresh=True)
                if positions:
                    snapshot.positions = [
                        {
                            "id": str(p.get("ticket", "")),
                            "position_ticket": p.get("ticket"),
                            "symbol": p.get("symbol", ""),
                            "direction": p.get("type", ""),
                            "lot_size": p.get("volume", 0),
                            "entry_price": p.get("open_price", 0),
                            "current_price": p.get("current_price", 0),
                            "stop_loss": p.get("sl", 0),
                            "take_profit": p.get("tp", 0),
                            "profit": float(p.get("profit", 0)) + float(p.get("swap", 0)) + float(p.get("commission", 0)),
                            "swap": p.get("swap", 0),
                            "commission": p.get("commission", 0),
                            "time": p.get("time").isoformat() if p.get("time") else None,
                        }
                        for p in positions
                    ]
            
            # Get trade stats
            if self.trade_manager:
                snapshot.stats = self.trade_manager.get_trade_stats()
            
            # Get bot status
            if self.bot_state:
                snapshot.status = {
                    "bot_running": self.bot_state.is_running,
                    "mt5_connected": self.bot_state.is_connected_mt5,
                    "telegram_connected": self.bot_state.is_connected_telegram,
                    "uptime_seconds": (datetime.utcnow() - self.bot_state.start_time).total_seconds() if self.bot_state.start_time else 0
                }
        
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
        
        return snapshot
    
    def _has_changes(self, new_snapshot: RealtimeSnapshot) -> bool:
        """Check if snapshot has meaningful changes"""
        # Always sync if no previous snapshot
        if not self._last_snapshot.account:
            return True
        
        # Check account changes (balance, equity, profit) - more sensitive threshold
        if new_snapshot.account and self._last_snapshot.account:
            for key in ['balance', 'equity', 'profit', 'margin', 'free_margin']:
                old_val = self._last_snapshot.account.get(key, 0)
                new_val = new_snapshot.account.get(key, 0)
                # Use smaller threshold for profit (0.001) to catch small P&L changes
                threshold = 0.001 if key == 'profit' else 0.01
                if abs(float(new_val) - float(old_val)) > threshold:
                    return True
        
        # Check position count changes
        if len(new_snapshot.positions) != len(self._last_snapshot.positions):
            return True
        
        # Check individual position changes (tickets, profit, prices)
        if new_snapshot.positions and self._last_snapshot.positions:
            # Create lookup by ticket for comparison
            old_positions = {p.get('position_ticket'): p for p in self._last_snapshot.positions}
            for new_pos in new_snapshot.positions:
                ticket = new_pos.get('position_ticket')
                old_pos = old_positions.get(ticket)
                
                if not old_pos:
                    return True  # New position
                
                # Check profit change (sensitive)
                if abs(new_pos.get('profit', 0) - old_pos.get('profit', 0)) > 0.001:
                    return True
                
                # Check price change
                if abs(new_pos.get('current_price', 0) - old_pos.get('current_price', 0)) > 0.00001:
                    return True
        
        # Check status changes
        if new_snapshot.status and self._last_snapshot.status:
            for key in ['bot_running', 'mt5_connected', 'telegram_connected']:
                if new_snapshot.status.get(key) != self._last_snapshot.status.get(key):
                    return True
        
        return False
    
    async def _sync_snapshot(self, snapshot: RealtimeSnapshot):
        """Sync snapshot to Firebase and WebSocket"""
        try:
            # 1. Broadcast to WebSocket clients FIRST (instant updates)
            if self.websocket_broadcast:
                if snapshot.account:
                    await self.websocket_broadcast({
                        "type": "account_update",
                        "data": snapshot.account
                    })
                
                if snapshot.positions is not None:
                    await self.websocket_broadcast({
                        "type": "positions_update",
                        "data": {
                            "positions": snapshot.positions,
                            "count": len(snapshot.positions)
                        }
                    })
                
                if snapshot.stats:
                    await self.websocket_broadcast({
                        "type": "stats_update",
                        "data": snapshot.stats
                    })
                
                if snapshot.status:
                    await self.websocket_broadcast({
                        "type": "status",
                        "data": snapshot.status
                    })
            
            # 2. Update Firebase (persistent storage) - non-blocking
            if self.firebase_service and self.firebase_service.initialized:
                if snapshot.account:
                    self.firebase_service.update_account(snapshot.account)
                
                if snapshot.positions is not None:
                    self.firebase_service.update_positions(snapshot.positions)
                
                if snapshot.stats:
                    self.firebase_service.update_stats(snapshot.stats)
                
                if snapshot.status:
                    self.firebase_service.update_status(snapshot.status)
        
        except Exception as e:
            logger.error(f"Error syncing snapshot: {e}")
    
    async def force_sync(self):
        """Force immediate synchronization"""
        try:
            if self.bot_state and self.bot_state.is_running:
                snapshot = await self._capture_snapshot()
                await self._sync_snapshot(snapshot)
                self._last_snapshot = snapshot
                logger.debug("Force sync completed")
        except Exception as e:
            logger.error(f"Force sync error: {e}")
    
    async def sync_trade_event(self, event: str, trade, data: dict = None):
        """Sync specific trade event immediately"""
        try:
            if self.websocket_broadcast:
                await self.websocket_broadcast({
                    "type": "trade_event",
                    "event": event,
                    "data": {
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "status": trade.status.value if hasattr(trade.status, 'value') else str(trade.status),
                        "event_data": data or {}
                    }
                })
            
            # Also trigger full sync to update all data
            await self.force_sync()
        except Exception as e:
            logger.error(f"Trade event sync error: {e}")


# Global singleton
realtime_sync = RealtimeSyncService()
