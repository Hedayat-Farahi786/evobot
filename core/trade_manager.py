"""
Trade state manager for handling trade lifecycle, partial closes, and breakeven logic.
"""
import asyncio
import logging
from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import json
import os

from models.trade import (
    Trade, Signal, TradeDirection, TradeStatus, SignalType
)
from broker import broker_client
from config.settings import config
from utils.logging_utils import log_trade_event

logger = logging.getLogger("evobot.trade_manager")


class TradeManager:
    """
    Manages trade state, execution, and lifecycle.
    Handles TP hits, breakeven moves, and partial closes.
    """
    
    def __init__(self):
        self.trades: Dict[str, Trade] = {}  # trade_id -> Trade
        self.signal_to_trade: Dict[str, str] = {}  # signal_id -> trade_id
        self.symbol_trades: Dict[str, List[str]] = {}  # symbol -> [trade_ids]
        self._lock = asyncio.Lock()
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._trade_listeners: List[Callable] = []
        self._persistence_file = "data/trades.json"
        
    async def start(self):
        """Start the trade manager"""
        logger.info("Starting trade manager...")
        self._running = True
        
        # Load persisted trades
        await self._load_trades()
        
        # Start position monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_positions())
        
        logger.info(f"Trade manager started. Loaded {len(self.trades)} trades.")
    
    async def stop(self):
        """Stop the trade manager"""
        logger.info("Stopping trade manager...")
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Persist trades
        await self._save_trades()
        
        logger.info("Trade manager stopped")
    
    def add_trade_listener(self, listener: Callable):
        """Add a listener for trade events"""
        self._trade_listeners.append(listener)
    
    async def _notify_listeners(self, event: str, trade: Trade, data: dict = None):
        """Notify all listeners of trade event"""
        for listener in self._trade_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event, trade, data)
                else:
                    listener(event, trade, data)
            except Exception as e:
                logger.error(f"Trade listener error: {e}")
    
    async def process_signal(self, signal: Signal) -> Optional[Trade]:
        """
        Process a trading signal.
        Creates new trades or updates existing ones.
        """
        async with self._lock:
            try:
                # Only process NEW_TRADE signals - we auto-detect TP/SL from broker
                if signal.signal_type == SignalType.NEW_TRADE:
                    return await self._handle_new_trade(signal)
                    
                # Ignore TP/SL hit messages from Telegram - we detect these automatically from broker
                elif signal.signal_type in [SignalType.TP1_HIT, SignalType.TP2_HIT, SignalType.TP3_HIT, SignalType.SL_HIT]:
                    logger.debug(f"Ignoring {signal.signal_type.value} from Telegram (auto-detected from broker)")
                    return None
                    
                # Handle manual breakeven command from channel
                elif signal.signal_type == SignalType.BREAKEVEN:
                    return await self._handle_breakeven_signal(signal)
                    
                # Handle close/cancel signals
                elif signal.signal_type == SignalType.CLOSE_TRADE:
                    return await self._handle_close(signal)
                    
                # Handle SL/TP updates (edited signals)
                elif signal.signal_type == SignalType.UPDATE_SL:
                    return await self._handle_sl_update(signal)
                elif signal.signal_type == SignalType.UPDATE_TP:
                    return await self._handle_tp_update(signal)
                    
                # Ignore unknown signals
                elif signal.signal_type == SignalType.UNKNOWN:
                    return None
                    
            except Exception as e:
                logger.error(f"Error processing signal: {e}", exc_info=True)
        
        return None
    
    async def _handle_new_trade(self, signal: Signal) -> Optional[Trade]:
        """Handle new trade signal"""
        # Check if we already have a trade for this signal
        if signal.id in self.signal_to_trade:
            logger.warning(f"Trade already exists for signal {signal.id}")
            return self.trades.get(self.signal_to_trade[signal.id])
        
        # Check max open trades
        active_trades = [t for t in self.trades.values() 
                        if t.status in [TradeStatus.ACTIVE, TradeStatus.WAITING, TradeStatus.TP1_HIT, TradeStatus.TP2_HIT]]
        if len(active_trades) >= config.trading.max_open_trades:
            logger.warning(f"Max open trades ({config.trading.max_open_trades}) reached")
            return None
        
        # Check spread
        spread_ok, spread = await broker_client.check_spread(signal.symbol)
        if not spread_ok:
            logger.warning(f"Spread too high for {signal.symbol}: {spread} pips")
            return None
        
        # Calculate lot sizes for partial closes
        lot_size = signal.lot_size or config.trading.default_lot_size
        
        # Create trade object
        trade = Trade.from_signal(signal, lot_size)
        trade.tp1_lot_size = round(lot_size * config.trading.tp1_close_percent, 2)
        trade.tp2_lot_size = round(lot_size * config.trading.tp2_close_percent, 2)
        trade.tp3_lot_size = round(lot_size * config.trading.tp3_close_percent, 2)
        
        # Check if price is in entry zone
        bid, ask = await broker_client.get_current_price(signal.symbol)
        if bid is None:
            logger.error(f"Cannot get price for {signal.symbol}")
            return None
        
        current_price = ask if signal.direction == TradeDirection.BUY else bid
        
        # Determine if we should enter now or wait
        # If execute_immediately is True, always enter at market price
        should_enter = config.trading.execute_immediately or self._is_price_in_zone(
            current_price, 
            signal.entry_min, 
            signal.entry_max,
            signal.direction
        )
        
        if should_enter or signal.entry_min is None:
            # Execute market orders - one for each TP level with SAME lot size
            # All orders have same SL, different TPs
            orders_placed = []
            tp_levels = [
                (1, signal.take_profit_1),
                (2, signal.take_profit_2),
                (3, signal.take_profit_3)
            ]
            
            for tp_num, tp_price in tp_levels:
                if tp_price is None:
                    logger.warning(f"TP{tp_num} is None - skipping order")
                    continue
                    
                # Create order with same lot size, same SL, specific TP
                trade_order = Trade.from_signal(signal, lot_size)
                trade_order.take_profit_1 = tp_price  # Set this TP as target
                trade_order.take_profit_2 = None
                trade_order.take_profit_3 = None
                trade_order.stop_loss = signal.stop_loss  # Same SL for all
                
                logger.info(f"Attempting to place TP{tp_num} order: TP={tp_price}, SL={signal.stop_loss}")
                success, ticket, msg = await broker_client.place_market_order(trade_order, lot_size)
                if success:
                    order_info = {
                        "tp": tp_num, 
                        "ticket": ticket, 
                        "lot": lot_size, 
                        "tp_price": tp_price,
                        "entry_price": current_price,  # Store actual fill price for this position
                        "closed": False
                    }
                    orders_placed.append(order_info)
                    if tp_num == 1:
                        trade.order_ticket = ticket
                        trade.position_ticket = ticket
                    logger.info(f"✅ TP{tp_num} order PLACED: ticket={ticket}, lots={lot_size}, TP={tp_price}, SL={signal.stop_loss}")
                else:
                    logger.error(f"❌ Failed to place TP{tp_num} order: {msg} (TP={tp_price}, SL={signal.stop_loss})")
                
                # Small delay between orders to avoid rate limiting
                if tp_num < 3 and success:
                    await asyncio.sleep(0.5)
            
            if orders_placed:
                trade.status = TradeStatus.ACTIVE
                trade.opened_at = datetime.utcnow()
                trade.entry_price = current_price
                trade.initial_lot_size = lot_size * len(orders_placed)
                trade.current_lot_size = lot_size * len(orders_placed)
                trade.position_tickets = orders_placed  # Store all position tickets
                trade.notes.append(f"Placed {len(orders_placed)} orders @ {lot_size} lots each, SL: {signal.stop_loss}")
                
                logger.info("=" * 80)
                logger.info(f"🎯 === NEW SIGNAL GROUP: Trade {trade.id[:8]}... ===")
                logger.info(f"Symbol: {trade.symbol}, Direction: {trade.direction.value}")
                logger.info(f"Total Orders Placed: {len(orders_placed)}/3")
                order_summary = ", ".join([f"TP{o['tp']}={o['ticket']}" for o in orders_placed])
                logger.info(f"Orders: [{order_summary}]")
                logger.info(f"Each order: {lot_size} lots, SL={signal.stop_loss}")
                logger.info(f"Entry prices: {current_price}")
                logger.info(f"When any TP hits, only THIS group moves to breakeven")
                logger.info("=" * 80)
                
                log_trade_event("TRADE_OPENED", trade.id, trade.symbol, {
                    "orders": orders_placed,
                    "entry_price": current_price,
                    "lot_per_order": lot_size,
                    "total_orders": len(orders_placed)
                })
                
                await self._notify_listeners("OPENED", trade, {"orders": orders_placed})
            else:
                trade.status = TradeStatus.FAILED
                trade.notes.append("Failed to place any orders")
                logger.error("Failed to place any orders")
        else:
            # Set trade to waiting status
            trade.status = TradeStatus.WAITING
            logger.info(f"Trade waiting for price to enter zone: {signal.entry_min}-{signal.entry_max}")
        
        # Store trade
        self.trades[trade.id] = trade
        self.signal_to_trade[signal.id] = trade.id
        
        if signal.symbol not in self.symbol_trades:
            self.symbol_trades[signal.symbol] = []
        self.symbol_trades[signal.symbol].append(trade.id)
        
        await self._save_trades()
        
        return trade
    
    async def _handle_tp_hit(self, signal: Signal, tp_level: int) -> Optional[Trade]:
        """Handle TP hit signal from Telegram"""
        trade = self._find_active_trade(signal.symbol)
        if not trade:
            logger.warning(f"No active trade found for {signal.symbol} TP{tp_level} hit")
            return None
        
        await self._process_tp_hit(trade, tp_level)
        return trade
    
    async def _process_tp_hit(self, trade: Trade, tp_level: int):
        """Process TP hit - partial close and breakeven"""
        if trade.status == TradeStatus.CLOSED:
            return
        
        if tp_level == 1 and trade.status != TradeStatus.TP1_HIT:
            # Close partial at TP1
            if trade.position_ticket and trade.tp1_lot_size > 0:
                success, msg = await broker_client.close_position(
                    trade.position_ticket, 
                    trade.tp1_lot_size
                )
                if success:
                    trade.current_lot_size -= trade.tp1_lot_size
                    logger.info(f"TP1 partial close: {trade.tp1_lot_size} lots")
            
            # Move SL to breakeven
            if config.trading.move_sl_to_breakeven_at_tp1:
                await self._move_to_breakeven(trade)
            
            trade.status = TradeStatus.TP1_HIT
            trade.tp1_hit_at = datetime.utcnow()
            
            log_trade_event("TP1_HIT", trade.id, trade.symbol, {
                "partial_close": trade.tp1_lot_size,
                "remaining_lots": trade.current_lot_size
            })
            
            await self._notify_listeners("TP1_HIT", trade, {"partial_close": trade.tp1_lot_size})
            
        elif tp_level == 2 and trade.status != TradeStatus.TP2_HIT:
            # Close partial at TP2
            if trade.position_ticket and trade.tp2_lot_size > 0:
                success, msg = await broker_client.close_position(
                    trade.position_ticket,
                    trade.tp2_lot_size
                )
                if success:
                    trade.current_lot_size -= trade.tp2_lot_size
                    logger.info(f"TP2 partial close: {trade.tp2_lot_size} lots")
            
            trade.status = TradeStatus.TP2_HIT
            trade.tp2_hit_at = datetime.utcnow()
            
            log_trade_event("TP2_HIT", trade.id, trade.symbol, {
                "partial_close": trade.tp2_lot_size,
                "remaining_lots": trade.current_lot_size
            })
            
            await self._notify_listeners("TP2_HIT", trade, {"partial_close": trade.tp2_lot_size})
            
        elif tp_level == 3:
            # Close remaining at TP3
            if trade.position_ticket:
                success, msg = await broker_client.close_position(trade.position_ticket)
                if success:
                    trade.current_lot_size = 0
                    logger.info(f"TP3 full close")
            
            trade.status = TradeStatus.TP3_HIT
            trade.closed_at = datetime.utcnow()
            
            log_trade_event("TP3_HIT", trade.id, trade.symbol, {"fully_closed": True})
            await self._notify_listeners("TP3_HIT", trade, {"fully_closed": True})
        
        await self._save_trades()
    
    async def _handle_sl_hit(self, signal: Signal) -> Optional[Trade]:
        """Handle SL hit signal"""
        trade = self._find_active_trade(signal.symbol)
        if not trade:
            return None
        
        trade.status = TradeStatus.SL_HIT
        trade.closed_at = datetime.utcnow()
        trade.current_lot_size = 0
        
        log_trade_event("SL_HIT", trade.id, trade.symbol)
        await self._notify_listeners("SL_HIT", trade)
        await self._save_trades()
        
        return trade
    
    async def _handle_breakeven_signal(self, signal: Signal) -> Optional[Trade]:
        """Handle breakeven signal from Telegram"""
        trade = self._find_active_trade(signal.symbol)
        if not trade:
            return None
        
        await self._move_to_breakeven(trade)
        return trade
    
    async def _move_to_breakeven(self, trade: Trade):
        """Move stop loss to breakeven - delegates to multi-position handler"""
        await self._move_all_to_breakeven(trade)
    
    async def _handle_close(self, signal: Signal) -> Optional[Trade]:
        """Handle close/cancel signal"""
        trade = self._find_active_trade(signal.symbol)
        if not trade:
            return None
        
        # Close all remaining lots
        if trade.position_ticket and trade.current_lot_size > 0:
            success, msg = await broker_client.close_position(trade.position_ticket)
            if success:
                trade.current_lot_size = 0
        
        trade.status = TradeStatus.CLOSED
        trade.closed_at = datetime.utcnow()
        
        log_trade_event("CLOSED", trade.id, trade.symbol)
        await self._notify_listeners("CLOSED", trade)
        await self._save_trades()
        
        return trade
    
    async def _handle_sl_update(self, signal: Signal) -> Optional[Trade]:
        """Handle SL update signal"""
        trade = self._find_active_trade(signal.symbol)
        if not trade or not signal.stop_loss:
            return None
        
        if trade.position_ticket:
            success, msg = await broker_client.modify_position(
                trade.position_ticket,
                sl=signal.stop_loss
            )
            
            if success:
                trade.stop_loss = signal.stop_loss
                log_trade_event("SL_UPDATED", trade.id, trade.symbol, {"new_sl": signal.stop_loss})
                await self._notify_listeners("SL_UPDATED", trade, {"new_sl": signal.stop_loss})
        
        await self._save_trades()
        return trade
    
    async def _handle_tp_update(self, signal: Signal) -> Optional[Trade]:
        """Handle TP update signal"""
        trade = self._find_active_trade(signal.symbol)
        if not trade:
            return None
        
        updated = False
        
        if signal.take_profit_1:
            trade.take_profit_1 = signal.take_profit_1
            updated = True
        if signal.take_profit_2:
            trade.take_profit_2 = signal.take_profit_2
            updated = True
        if signal.take_profit_3:
            trade.take_profit_3 = signal.take_profit_3
            updated = True
        
        # Update TP on broker (using TP1 as the active TP)
        if updated and trade.position_ticket:
            await broker_client.modify_position(
                trade.position_ticket,
                tp=trade.take_profit_1
            )
            
            log_trade_event("TP_UPDATED", trade.id, trade.symbol, {
                "tp1": trade.take_profit_1,
                "tp2": trade.take_profit_2,
                "tp3": trade.take_profit_3
            })
        
        await self._save_trades()
        return trade
    
    def _find_active_trade(self, symbol: str) -> Optional[Trade]:
        """Find most recent active trade for symbol"""
        if symbol not in self.symbol_trades:
            return None
        
        for trade_id in reversed(self.symbol_trades[symbol]):
            trade = self.trades.get(trade_id)
            if trade and trade.status in [
                TradeStatus.ACTIVE, TradeStatus.WAITING,
                TradeStatus.TP1_HIT, TradeStatus.TP2_HIT, TradeStatus.BREAKEVEN
            ]:
                return trade
        
        return None
    
    def _is_price_in_zone(
        self, 
        price: float, 
        entry_min: Optional[float], 
        entry_max: Optional[float],
        direction: TradeDirection
    ) -> bool:
        """Check if price is within entry zone with buffer to never miss signals"""
        if entry_min is None or entry_max is None:
            return True  # Market order
        
        # Aggressive buffer: 5 pips default + 50% extra buffer for fast-moving pairs
        base_tolerance_pips = config.trading.entry_zone_tolerance
        
        # Add extra buffer for fast-moving symbols (Gold, indices)
        fast_symbols = ['XAUUSD', 'XAGUSD', 'BTCUSD', 'US30', 'NAS100', 'USTEC']
        if any(sym in str(entry_min) or sym in str(entry_max) for sym in fast_symbols):
            # For gold/indices, use 2x buffer
            tolerance_pips = base_tolerance_pips * 2
        else:
            # For forex, use 1.5x buffer
            tolerance_pips = base_tolerance_pips * 1.5
        
        # Convert pips to price (0.0001 for forex, 0.01 for gold)
        pip_value = 0.01 if price > 100 else 0.0001
        tolerance = tolerance_pips * pip_value
        
        # Expand entry zone in BOTH directions to catch fast price movements
        expanded_min = entry_min - tolerance
        expanded_max = entry_max + tolerance
        
        # For BUY: allow entry if price is anywhere near the zone (even slightly above)
        # For SELL: allow entry if price is anywhere near the zone (even slightly below)
        # This ensures we NEVER miss a signal due to fast price movement
        in_zone = expanded_min <= price <= expanded_max
        
        if not in_zone:
            logger.debug(f"Price {price} outside expanded zone [{expanded_min:.5f} - {expanded_max:.5f}] (tolerance: {tolerance_pips} pips)")
        
        return in_zone
    
    async def _monitor_positions(self):
        """Background task to monitor positions and check TPs"""
        logger.info("Position monitoring started")
        
        while self._running:
            try:
                await self._check_waiting_trades()
                await self._check_tp_levels()
                await self._update_pnl()
                
            except Exception as e:
                logger.error(f"Position monitor error: {e}", exc_info=True)
            
            # Monitor at configured interval for real-time updates
            await asyncio.sleep(config.trading.position_monitoring_interval)
    
    async def _check_waiting_trades(self):
        """Check if waiting trades should be executed"""
        for trade in list(self.trades.values()):
            if trade.status != TradeStatus.WAITING:
                continue
            
            bid, ask = await broker_client.get_current_price(trade.symbol)
            if bid is None:
                continue
            
            price = ask if trade.direction == TradeDirection.BUY else bid
            
            if self._is_price_in_zone(price, trade.entry_min, trade.entry_max, trade.direction):
                # Execute the trade
                success, ticket, msg = await broker_client.place_market_order(
                    trade, 
                    trade.initial_lot_size
                )
                
                if success:
                    trade.order_ticket = ticket
                    trade.position_ticket = ticket
                    trade.status = TradeStatus.ACTIVE
                    trade.opened_at = datetime.utcnow()
                    trade.entry_price = price
                    
                    log_trade_event("TRADE_OPENED", trade.id, trade.symbol, {
                        "ticket": ticket,
                        "entry_price": price
                    })
                    
                    await self._notify_listeners("OPENED", trade, {"ticket": ticket})
                    await self._save_trades()
    
    async def _check_tp_levels(self):
        """Check if any TPs have been hit by checking if positions are still open"""
        try:
            # Get all open positions from broker
            open_positions = await broker_client.get_positions()
            open_ticket_ids = set()
            
            for pos in open_positions:
                pos_id = pos.get("id") or pos.get("ticket") or pos.get("positionId")
                if pos_id:
                    open_ticket_ids.add(str(pos_id))
            
            # Check each trade with multiple positions
            for trade in list(self.trades.values()):
                if trade.status not in [TradeStatus.ACTIVE, TradeStatus.TP1_HIT, TradeStatus.TP2_HIT, TradeStatus.BREAKEVEN]:
                    continue
                
                if not trade.position_tickets:
                    continue
                
                # Check which positions have been closed (TP hit)
                tp_hit_this_cycle = False
                tp_hit_numbers = []
                remaining_open = 0
                
                for pos_info in trade.position_tickets:
                    ticket = str(pos_info.get("ticket", ""))
                    was_closed = pos_info.get("closed", False)
                    
                    if was_closed:
                        continue  # Already marked as closed
                    
                    if ticket not in open_ticket_ids:
                        # Position closed - TP was hit!
                        pos_info["closed"] = True
                        tp_num = pos_info.get("tp", 0)
                        tp_price = pos_info.get("tp_price", 0)
                        
                        logger.info(f"TP{tp_num} HIT! Position {ticket} closed at {tp_price}")
                        trade.notes.append(f"TP{tp_num} hit @ {tp_price}")
                        
                        tp_hit_this_cycle = True
                        tp_hit_numbers.append(tp_num)
                        
                        # Update trade status based on which TP hit
                        if tp_num == 1:
                            trade.status = TradeStatus.TP1_HIT
                            trade.tp1_hit_at = datetime.utcnow()
                        elif tp_num == 2:
                            trade.status = TradeStatus.TP2_HIT
                            trade.tp2_hit_at = datetime.utcnow()
                        elif tp_num == 3:
                            trade.status = TradeStatus.TP3_HIT
                        
                        log_trade_event(f"TP{tp_num}_HIT", trade.id, trade.symbol, {
                            "ticket": ticket,
                            "tp_price": tp_price
                        })
                        await self._notify_listeners(f"TP{tp_num}_HIT", trade, {"tp_price": tp_price})
                    else:
                        remaining_open += 1
                
                # If TP1 hit and there are remaining positions, move them to breakeven
                if tp_hit_this_cycle and 1 in tp_hit_numbers and remaining_open > 0 and not trade.breakeven_applied:
                    logger.info(f"Trade {trade.id[:8]}... TP1 hit! Moving {remaining_open} remaining positions to breakeven")
                    await self._move_all_to_breakeven(trade)
                
                # If all positions closed, mark trade as closed
                if remaining_open == 0:
                    trade.status = TradeStatus.CLOSED
                    trade.closed_at = datetime.utcnow()
                    trade.current_lot_size = 0
                    logger.info(f"All positions closed for trade {trade.id}")
                    await self._save_trades()
                    
        except Exception as e:
            logger.error(f"Error checking TP levels: {e}", exc_info=True)
    
    async def _move_all_to_breakeven(self, trade: Trade):
        """Move all remaining positions to breakeven (SL = entry for each position)"""
        if trade.breakeven_applied:
            logger.debug(f"Breakeven already applied for trade {trade.id[:8]}")
            return
        
        logger.info(f"🔒 Moving remaining positions to breakeven (SL to each position's entry)")
        
        # Get current price to calculate safe SL distance
        bid, ask = await broker_client.get_current_price(trade.symbol)
        if not bid:
            logger.error("Cannot get current price for breakeven")
            return
        
        current_price = bid if trade.direction == TradeDirection.BUY else ask
        
        success_count = 0
        for pos_info in trade.position_tickets:
            if pos_info.get("closed", False):
                continue  # Skip closed positions
            
            ticket = pos_info.get("ticket")
            entry_price = float(pos_info.get("entry_price", 0))  # Ensure float
            
            if ticket and entry_price:
                # Calculate safe breakeven SL based on current price
                # Use minimum 10 pips buffer from current price
                min_buffer_pips = 10
                
                if trade.direction == TradeDirection.BUY:
                    # For BUY: SL must be below current price
                    # Use entry + small buffer, but ensure it's below current price
                    ideal_sl = entry_price + (config.trading.breakeven_offset_pips * 0.0001)
                    safe_sl = min(ideal_sl, current_price - (min_buffer_pips * 0.0001))
                else:
                    # For SELL: SL must be above current price
                    ideal_sl = entry_price - (config.trading.breakeven_offset_pips * 0.0001)
                    safe_sl = max(ideal_sl, current_price + (min_buffer_pips * 0.0001))
                
                logger.info(f"Modifying position {ticket}: entry={entry_price}, current={current_price}, new_sl={safe_sl}")
                success, msg = await broker_client.modify_position(ticket, sl=safe_sl)
                if success:
                    success_count += 1
                    logger.info(f"✅ Position {ticket} moved to breakeven SL={safe_sl}")
                else:
                    logger.error(f"❌ Failed to move position {ticket} to breakeven: {msg}")
        
        if success_count > 0:
            trade.breakeven_applied = True
            trade.status = TradeStatus.BREAKEVEN
            trade.notes.append(f"Breakeven applied to {success_count} positions")
            
            log_trade_event("BREAKEVEN", trade.id, trade.symbol, {
                "positions_modified": success_count
            })
            await self._notify_listeners("BREAKEVEN", trade, {"positions_modified": success_count})
            await self._save_trades()
            logger.info(f"✅ Breakeven applied successfully to {success_count} positions")
        else:
            logger.warning(f"⚠️ Failed to apply breakeven to any positions")
    
    async def _update_pnl(self):
        """Update P&L for active trades and push to Firebase"""
        try:
            positions = await broker_client.get_positions()
            
            # Create a map of position ID to position data
            pos_map = {}
            for pos in positions:
                pos_id = pos.get("id") or pos.get("ticket") or pos.get("positionId")
                if pos_id:
                    pos_map[str(pos_id)] = pos
            
            # Track if any values changed
            values_changed = False
            
            for trade in self.trades.values():
                if trade.status not in [TradeStatus.ACTIVE, TradeStatus.TP1_HIT, TradeStatus.TP2_HIT, TradeStatus.BREAKEVEN]:
                    continue
                
                old_pnl = trade.unrealized_pnl
                total_pnl = 0
                total_swap = 0
                current_price = None
                
                # Sum up P&L from all open positions for this trade
                for pos_info in trade.position_tickets:
                    if pos_info.get("closed", False):
                        continue
                    
                    ticket = str(pos_info.get("ticket", ""))
                    if ticket in pos_map:
                        pos = pos_map[ticket]
                        total_pnl += pos.get("profit", 0) or pos.get("unrealizedProfit", 0)
                        total_swap += pos.get("swap", 0)
                        if current_price is None:
                            current_price = pos.get("currentPrice") or pos.get("price")
                
                trade.unrealized_pnl = total_pnl
                trade.swap = total_swap
                if current_price:
                    trade.current_price = current_price
                
                # Check if values changed
                if old_pnl != total_pnl:
                    values_changed = True
            
            # Push updated positions to Firebase if values changed
            if values_changed and positions:
                try:
                    from core.firebase_service import firebase_service
                    if firebase_service.initialized:
                        firebase_service.update_positions(positions)
                except Exception as fb_err:
                    logger.debug(f"Firebase update error: {fb_err}")
                    
        except Exception as e:
            logger.debug(f"Error updating PnL: {e}")
    
    async def _save_trades(self):
        """Persist trades to file"""
        try:
            os.makedirs(os.path.dirname(self._persistence_file), exist_ok=True)
            
            data = {
                "trades": {tid: t.to_dict() for tid, t in self.trades.items()},
                "signal_to_trade": self.signal_to_trade,
                "symbol_trades": self.symbol_trades,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self._persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save trades: {e}")
    
    def _load_trades_sync(self):
        """Synchronously load trades from file (for use before bot starts)"""
        try:
            if not os.path.exists(self._persistence_file):
                return
            
            # Only load if trades haven't been loaded yet
            if self.trades:
                return
            
            with open(self._persistence_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct Trade objects
            for tid, tdata in data.get("trades", {}).items():
                trade = Trade()
                trade.id = tdata.get("id", tid)
                trade.signal_id = tdata.get("signal_id", "")
                trade.symbol = tdata.get("symbol", "")
                trade.direction = TradeDirection(tdata["direction"]) if tdata.get("direction") else None
                trade.entry_min = tdata.get("entry_min")
                trade.entry_max = tdata.get("entry_max")
                trade.entry_price = tdata.get("entry_price")
                trade.current_price = tdata.get("current_price")
                trade.stop_loss = tdata.get("stop_loss")
                trade.original_stop_loss = tdata.get("original_stop_loss")
                trade.take_profit_1 = tdata.get("take_profit_1")
                trade.take_profit_2 = tdata.get("take_profit_2")
                trade.take_profit_3 = tdata.get("take_profit_3")
                trade.initial_lot_size = tdata.get("initial_lot_size", 0)
                trade.current_lot_size = tdata.get("current_lot_size", 0)
                trade.order_ticket = tdata.get("order_ticket")
                trade.position_ticket = tdata.get("position_ticket")
                trade.position_tickets = tdata.get("position_tickets", [])  # Load position_tickets
                trade.status = TradeStatus(tdata["status"]) if tdata.get("status") else TradeStatus.WAITING
                trade.breakeven_applied = tdata.get("breakeven_applied", False)
                trade.channel_id = tdata.get("channel_id", "")
                trade.notes = tdata.get("notes", [])
                trade.realized_pnl = tdata.get("realized_pnl", 0.0)
                trade.unrealized_pnl = tdata.get("unrealized_pnl", 0.0)
                
                self.trades[tid] = trade
            
            self.signal_to_trade = data.get("signal_to_trade", {})
            self.symbol_trades = data.get("symbol_trades", {})
            
            logger.info(f"Loaded {len(self.trades)} trades from persistence (sync)")
            
        except Exception as e:
            logger.error(f"Failed to load trades (sync): {e}")
    
    async def _load_trades(self):
        """Load trades from file"""
        try:
            if not os.path.exists(self._persistence_file):
                return
            
            with open(self._persistence_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct Trade objects
            for tid, tdata in data.get("trades", {}).items():
                trade = Trade()
                trade.id = tdata.get("id", tid)
                trade.signal_id = tdata.get("signal_id", "")
                trade.symbol = tdata.get("symbol", "")
                trade.direction = TradeDirection(tdata["direction"]) if tdata.get("direction") else None
                trade.entry_min = tdata.get("entry_min")
                trade.entry_max = tdata.get("entry_max")
                trade.entry_price = tdata.get("entry_price")
                trade.current_price = tdata.get("current_price")
                trade.stop_loss = tdata.get("stop_loss")
                trade.original_stop_loss = tdata.get("original_stop_loss")
                trade.take_profit_1 = tdata.get("take_profit_1")
                trade.take_profit_2 = tdata.get("take_profit_2")
                trade.take_profit_3 = tdata.get("take_profit_3")
                trade.initial_lot_size = tdata.get("initial_lot_size", 0)
                trade.current_lot_size = tdata.get("current_lot_size", 0)
                trade.order_ticket = tdata.get("order_ticket")
                trade.position_ticket = tdata.get("position_ticket")
                trade.position_tickets = tdata.get("position_tickets", [])  # Load position_tickets
                trade.status = TradeStatus(tdata["status"]) if tdata.get("status") else TradeStatus.WAITING
                trade.breakeven_applied = tdata.get("breakeven_applied", False)
                trade.channel_id = tdata.get("channel_id", "")
                trade.notes = tdata.get("notes", [])
                trade.realized_pnl = tdata.get("realized_pnl", 0.0)
                trade.unrealized_pnl = tdata.get("unrealized_pnl", 0.0)
                
                self.trades[tid] = trade
            
            self.signal_to_trade = data.get("signal_to_trade", {})
            self.symbol_trades = data.get("symbol_trades", {})
            
            logger.info(f"Loaded {len(self.trades)} trades from persistence")
            
        except Exception as e:
            logger.error(f"Failed to load trades: {e}")
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID"""
        return self.trades.get(trade_id)
    
    def get_active_trades(self) -> List[Trade]:
        """Get all active trades"""
        # Ensure trades are loaded
        if not self.trades:
            self._load_trades_sync()
        return [
            t for t in self.trades.values()
            if t.status in [TradeStatus.ACTIVE, TradeStatus.WAITING, 
                           TradeStatus.TP1_HIT, TradeStatus.TP2_HIT, TradeStatus.BREAKEVEN]
        ]
    
    def get_all_trades(self) -> List[Trade]:
        """Get all trades"""
        # Ensure trades are loaded
        if not self.trades:
            self._load_trades_sync()
        return list(self.trades.values())
    
    def get_trade_by_ticket(self, ticket: int) -> Optional[Trade]:
        """Find a trade that contains the specified position ticket"""
        # Ensure trades are loaded
        if not self.trades:
            self._load_trades_sync()
            
        ticket_str = str(ticket)
        for trade in self.trades.values():
            # Check main ticket
            if str(trade.order_ticket) == ticket_str or str(trade.position_ticket) == ticket_str:
                return trade
            
            # Check multiple position tickets
            if trade.position_tickets:
                for pos in trade.position_tickets:
                    if str(pos.get("ticket")) == ticket_str:
                        return trade
        return None
    
    def get_trade_stats(self) -> dict:
        """Get trading statistics"""
        from datetime import datetime
        
        # Ensure trades are loaded (for when stats are requested before bot starts)
        if not self.trades:
            self._load_trades_sync()
        
        trades = list(self.trades.values())
        
        closed_trades = [t for t in trades if t.status in [
            TradeStatus.TP1_HIT, TradeStatus.TP2_HIT, TradeStatus.TP3_HIT,
            TradeStatus.SL_HIT, TradeStatus.CLOSED
        ]]
        
        active_trades = self.get_active_trades()
        winning = [t for t in closed_trades if t.realized_pnl > 0]
        losing = [t for t in closed_trades if t.realized_pnl < 0]
        
        # Calculate open P/L using unrealized_pnl
        open_pnl = sum(t.unrealized_pnl or 0 for t in active_trades)
        
        return {
            "total_trades": len(trades),
            "open_trades": len(active_trades),
            "active_trades": len(active_trades),
            "closed_trades": len(closed_trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": len(winning) / len(closed_trades) * 100 if closed_trades else 0,
            "total_profit": sum(t.realized_pnl for t in closed_trades),
            "total_pnl": sum(t.realized_pnl for t in closed_trades),
            "open_pnl": open_pnl,
            "last_updated": datetime.utcnow().isoformat(),
        }


# Singleton instance
trade_manager = TradeManager()
