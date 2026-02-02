"""
MetaTrader 5 broker client for trade execution.
Handles order placement, modification, and position management.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from enum import Enum

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

from config.settings import config
from models.trade import (
    Trade, TradeDirection, TradeStatus, AccountInfo, SymbolInfo
)
from utils.logging_utils import log_trade_event

logger = logging.getLogger("evobot.broker")


class OrderType(Enum):
    """MT5 Order types"""
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5


class MT5Client:
    """
    MetaTrader 5 client for trade execution.
    Provides thread-safe order operations with retry logic.
    """
    
    def __init__(self):
        self.connected = False
        self._lock = asyncio.Lock()
        self.account_info: Optional[AccountInfo] = None
        self.symbol_cache: Dict[str, SymbolInfo] = {}
        
    async def connect(self, user_id: str = None) -> bool:
        """Connect to MT5 terminal"""
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
            return False
            
        async with self._lock:
            try:
                # Shutdown any existing connection first
                try:
                    mt5.shutdown()
                    logger.info("Shut down any existing MT5 connection")
                    await asyncio.sleep(0.5)
                except:
                    pass
                
                # Try to connect to already running MT5 terminal first (no credentials needed)
                logger.info("Attempting to connect to running MT5 terminal...")
                try:
                    if mt5.initialize(path=config.broker.path if config.broker.path else None):
                        # Successfully connected to running terminal
                        account = mt5.account_info()
                        if account:
                            logger.info(f"Connected to running MT5 terminal: {account.server} (Login: {account.login})")
                            self.account_info = AccountInfo(
                                balance=account.balance,
                                equity=account.equity,
                                margin=account.margin,
                                free_margin=account.margin_free,
                                profit=account.profit,
                                currency=account.currency,
                                leverage=account.leverage,
                                server=account.server,
                                login=account.login,
                                name=account.name
                            )
                            self.connected = True
                            logger.info(f"Account balance: {account.balance} {account.currency}")
                            return True
                except Exception as e:
                    logger.debug(f"Simple connection failed: {e}")
                
                # If simple connection failed, try with credentials
                logger.info("Simple connection failed, trying with credentials...")
                
                # Load credentials from store if user_id provided
                if user_id:
                    from core.mt5_credentials import mt5_store
                    creds = mt5_store.get(user_id)
                    if not creds:
                        logger.error(f"No MT5 credentials found for user {user_id}")
                        return False
                    login = int(creds["login"])
                    password = creds["password"]
                    server = creds["server"]
                    logger.info(f"Using stored credentials: Server={server}, Login={login}")
                else:
                    # Fallback to config (for backward compatibility)
                    if not config.broker.login or not config.broker.password:
                        logger.error("No MT5 credentials configured")
                        return False
                    login = config.broker.login
                    password = config.broker.password
                    server = config.broker.server
                    logger.info(f"Using config credentials: Server={server}, Login={login}")
                
                # Initialize MT5 with credentials
                logger.info(f"Initializing MT5 with: server={server}, login={login}, path={config.broker.path}")
                if not mt5.initialize(
                    path=config.broker.path if config.broker.path else None,
                    login=login,
                    password=password,
                    server=server,
                    timeout=config.broker.timeout
                ):
                    error = mt5.last_error()
                    logger.error(f"MT5 initialization failed: {error}")
                    return False
                
                # Verify connection
                account = mt5.account_info()
                if account is None:
                    logger.error("Failed to get account info")
                    mt5.shutdown()
                    return False
                
                self.account_info = AccountInfo(
                    balance=account.balance,
                    equity=account.equity,
                    margin=account.margin,
                    free_margin=account.margin_free,
                    profit=account.profit,
                    currency=account.currency,
                    leverage=account.leverage,
                    server=account.server,
                    login=account.login,
                    name=account.name
                )
                
                self.connected = True
                logger.info(f"Connected to MT5: {account.server} (Login: {account.login})")
                logger.info(f"Account balance: {account.balance} {account.currency}")
                
                return True
                
            except Exception as e:
                logger.error(f"MT5 connection error: {e}", exc_info=True)
                try:
                    mt5.shutdown()
                except:
                    pass
                return False
    
    async def disconnect(self):
        """Disconnect from MT5"""
        if MT5_AVAILABLE and self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information"""
        if not self.connected:
            return None
            
        # Check cache
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]
        
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                # Try to enable symbol
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Symbol {symbol} not found or cannot be selected")
                    return None
                info = mt5.symbol_info(symbol)
            
            if info:
                symbol_info = SymbolInfo(
                    name=info.name,
                    description=info.description,
                    point=info.point,
                    digits=info.digits,
                    spread=info.spread,
                    spread_float=info.spread * info.point,
                    tick_size=info.trade_tick_size,
                    tick_value=info.trade_tick_value,
                    volume_min=info.volume_min,
                    volume_max=info.volume_max,
                    volume_step=info.volume_step,
                    bid=info.bid,
                    ask=info.ask
                )
                self.symbol_cache[symbol] = symbol_info
                return symbol_info
                
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
        
        return None
    
    async def get_current_price(self, symbol: str) -> Tuple[Optional[float], Optional[float]]:
        """Get current bid/ask price for symbol"""
        if not self.connected:
            return None, None
            
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick.bid, tick.ask
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
        
        return None, None
    
    async def check_spread(self, symbol: str) -> Tuple[bool, float]:
        """
        Check if spread is within acceptable limits.
        Returns (is_acceptable, spread_in_pips)
        """
        symbol_info = await self.get_symbol_info(symbol)
        if not symbol_info:
            return False, 0.0
        
        spread_pips = symbol_info.spread_in_pips()
        is_acceptable = spread_pips <= config.trading.max_spread_pips
        
        return is_acceptable, spread_pips
    
    async def place_market_order(
        self,
        trade: Trade,
        lot_size: float,
        slippage: int = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Place a market order.
        
        Returns:
            (success, ticket, message)
        """
        if not self.connected:
            return False, None, "Not connected to MT5"
        
        slippage = slippage or config.trading.max_slippage
        
        async with self._lock:
            try:
                symbol = trade.symbol
                
                # Ensure symbol is selected
                if not mt5.symbol_select(symbol, True):
                    return False, None, f"Cannot select symbol {symbol}"
                
                # Get current price
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    return False, None, f"Cannot get price for {symbol}"
                
                # Determine order type and price
                if trade.direction == TradeDirection.BUY:
                    order_type = mt5.ORDER_TYPE_BUY
                    price = tick.ask
                else:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = tick.bid
                
                # Normalize lot size
                symbol_info = await self.get_symbol_info(symbol)
                if symbol_info:
                    lot_size = self._normalize_lot(lot_size, symbol_info)
                
                # Prepare order request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": lot_size,
                    "type": order_type,
                    "price": price,
                    "sl": trade.stop_loss or 0.0,
                    "tp": trade.take_profit_1 or 0.0,
                    "deviation": slippage,
                    "magic": 123456,  # Magic number for identification
                    "comment": f"EvoBot_{trade.id[:8]}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Send order with retry
                for attempt in range(config.broker.retry_attempts):
                    result = mt5.order_send(request)
                    
                    if result is None:
                        error = mt5.last_error()
                        logger.error(f"Order send failed (attempt {attempt + 1}): {error}")
                        await asyncio.sleep(config.broker.retry_delay)
                        continue
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        ticket = result.order
                        logger.info(f"Order placed: {symbol} {trade.direction.value} {lot_size} lots @ {result.price}, ticket: {ticket}")
                        
                        log_trade_event(
                            "ORDER_PLACED",
                            trade.id,
                            symbol,
                            {
                                "ticket": ticket,
                                "direction": trade.direction.value,
                                "lot_size": lot_size,
                                "price": result.price,
                                "sl": trade.stop_loss,
                                "tp": trade.take_profit_1
                            }
                        )
                        
                        return True, ticket, f"Order placed at {result.price}"
                    
                    # Handle specific error codes
                    error_msg = self._get_error_message(result.retcode)
                    logger.warning(f"Order failed (attempt {attempt + 1}): {error_msg}")
                    
                    # Some errors are not worth retrying
                    if result.retcode in [
                        mt5.TRADE_RETCODE_INVALID_VOLUME,
                        mt5.TRADE_RETCODE_INVALID_STOPS,
                        mt5.TRADE_RETCODE_MARKET_CLOSED
                    ]:
                        return False, None, error_msg
                    
                    await asyncio.sleep(config.broker.retry_delay)
                
                return False, None, "Max retry attempts reached"
                
            except Exception as e:
                logger.error(f"Error placing order: {e}", exc_info=True)
                return False, None, str(e)
    
    async def place_pending_order(
        self,
        trade: Trade,
        lot_size: float,
        entry_price: float
    ) -> Tuple[bool, Optional[int], str]:
        """Place a pending order (limit or stop)"""
        if not self.connected:
            return False, None, "Not connected to MT5"
        
        async with self._lock:
            try:
                symbol = trade.symbol
                
                if not mt5.symbol_select(symbol, True):
                    return False, None, f"Cannot select symbol {symbol}"
                
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    return False, None, f"Cannot get price for {symbol}"
                
                # Determine order type based on direction and price
                if trade.direction == TradeDirection.BUY:
                    if entry_price < tick.ask:
                        order_type = mt5.ORDER_TYPE_BUY_LIMIT
                    else:
                        order_type = mt5.ORDER_TYPE_BUY_STOP
                else:
                    if entry_price > tick.bid:
                        order_type = mt5.ORDER_TYPE_SELL_LIMIT
                    else:
                        order_type = mt5.ORDER_TYPE_SELL_STOP
                
                symbol_info = await self.get_symbol_info(symbol)
                if symbol_info:
                    lot_size = self._normalize_lot(lot_size, symbol_info)
                
                request = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": lot_size,
                    "type": order_type,
                    "price": entry_price,
                    "sl": trade.stop_loss or 0.0,
                    "tp": trade.take_profit_1 or 0.0,
                    "deviation": config.trading.max_slippage,
                    "magic": 123456,
                    "comment": f"EvoBot_{trade.id[:8]}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                }
                
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"Pending order placed: {symbol} @ {entry_price}, ticket: {result.order}")
                    return True, result.order, "Pending order placed"
                
                error_msg = self._get_error_message(result.retcode if result else 0)
                return False, None, error_msg
                
            except Exception as e:
                logger.error(f"Error placing pending order: {e}", exc_info=True)
                return False, None, str(e)
    
    async def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Modify an existing position's SL/TP"""
        if not self.connected:
            return False, "Not connected to MT5"
        
        async with self._lock:
            try:
                # Get position info
                position = mt5.positions_get(ticket=ticket)
                if not position:
                    return False, f"Position {ticket} not found"
                
                position = position[0]
                
                # Get symbol info for stop level
                symbol_info = await self.get_symbol_info(position.symbol)
                if not symbol_info:
                    return False, "Cannot get symbol info"
                
                # Get current price
                tick = mt5.symbol_info_tick(position.symbol)
                if not tick:
                    return False, "Cannot get current price"
                
                # Validate SL distance from current price
                if sl is not None:
                    # Convert to float if string
                    sl = float(sl)
                    
                    # Get stop level (minimum distance from current price)
                    stops_level = mt5.symbol_info(position.symbol).trade_stops_level
                    min_distance = stops_level * symbol_info.point
                    
                    # Check distance based on position type
                    if position.type == mt5.POSITION_TYPE_BUY:
                        current_price = tick.bid
                        if sl >= current_price - min_distance:
                            # SL too close, adjust it
                            sl = current_price - (min_distance * 2)  # Double the minimum distance
                            logger.warning(f"SL too close, adjusted to {sl} (min distance: {min_distance})")
                    else:  # SELL
                        current_price = tick.ask
                        if sl <= current_price + min_distance:
                            # SL too close, adjust it
                            sl = current_price + (min_distance * 2)
                            logger.warning(f"SL too close, adjusted to {sl} (min distance: {min_distance})")
                
                # Validate TP distance
                if tp is not None:
                    tp = float(tp)
                
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": position.symbol,
                    "position": ticket,
                    "sl": sl if sl is not None else position.sl,
                    "tp": tp if tp is not None else position.tp,
                }
                
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"Position {ticket} modified: SL={sl}, TP={tp}")
                    return True, "Position modified"
                
                error_msg = self._get_error_message(result.retcode if result else 0)
                return False, error_msg
                
            except Exception as e:
                logger.error(f"Error modifying position: {e}", exc_info=True)
                return False, str(e)
    
    async def close_position(
        self,
        ticket: int,
        volume: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Close a position (fully or partially).
        
        Args:
            ticket: Position ticket
            volume: Volume to close (None for full close)
        """
        if not self.connected:
            return False, "Not connected to MT5"
        
        async with self._lock:
            try:
                # Get position info
                positions = mt5.positions_get(ticket=ticket)
                if not positions:
                    return False, f"Position {ticket} not found"
                
                position = positions[0]
                close_volume = volume if volume else position.volume
                
                # Determine close type
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(position.symbol).bid
                else:
                    order_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(position.symbol).ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position.symbol,
                    "volume": close_volume,
                    "type": order_type,
                    "position": ticket,
                    "price": price,
                    "deviation": config.trading.max_slippage,
                    "magic": 123456,
                    "comment": f"EvoBot_Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"Position {ticket} closed: {close_volume} lots @ {result.price}")
                    return True, f"Closed {close_volume} lots"
                
                error_msg = self._get_error_message(result.retcode if result else 0)
                return False, error_msg
                
            except Exception as e:
                logger.error(f"Error closing position: {e}", exc_info=True)
                return False, str(e)
    
    async def get_positions(self, symbol: Optional[str] = None, force_refresh: bool = False) -> List[dict]:
        """Get open positions (no caching for real-time updates)"""
        if not self.connected:
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            return [
                {
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL",
                    "volume": p.volume,
                    "open_price": p.price_open,
                    "current_price": p.price_current,
                    "sl": p.sl,
                    "tp": p.tp,
                    "profit": float(p.profit),
                    "swap": float(p.swap),
                    "commission": float(getattr(p, 'commission', 0)),
                    "magic": p.magic,
                    "comment": p.comment,
                    "time": datetime.fromtimestamp(p.time)
                }
                for p in positions
            ]
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_account_info(self, force_refresh: bool = False) -> Optional[AccountInfo]:
        """Get updated account information (no caching for real-time updates)"""
        if not self.connected:
            return None
        
        try:
            account = mt5.account_info()
            if account:
                self.account_info = AccountInfo(
                    balance=account.balance,
                    equity=account.equity,
                    margin=account.margin,
                    free_margin=account.margin_free,
                    margin_level=account.margin_level if account.margin_level else 0,
                    profit=account.profit,
                    currency=account.currency,
                    leverage=account.leverage,
                    server=account.server,
                    login=account.login,
                    name=account.name
                )
                return self.account_info
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
        
        return None
    
    def _normalize_lot(self, lot_size: float, symbol_info: SymbolInfo) -> float:
        """Normalize lot size to symbol's volume step"""
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        step = symbol_info.volume_step
        
        # Clamp to min/max
        lot_size = max(min_lot, min(lot_size, max_lot))
        
        # Round to step
        if step > 0:
            lot_size = round(lot_size / step) * step
        
        return round(lot_size, 2)
    
    def _get_error_message(self, retcode: int) -> str:
        """Get human-readable error message for MT5 return code"""
        error_messages = {
            10004: "Requote",
            10006: "Request rejected",
            10007: "Request canceled by trader",
            10008: "Order placed",
            10009: "Request completed",
            10010: "Only part of request completed",
            10011: "Request processing error",
            10012: "Request canceled by timeout",
            10013: "Invalid request",
            10014: "Invalid volume",
            10015: "Invalid price",
            10016: "Invalid stops",
            10017: "Trade disabled",
            10018: "Market closed",
            10019: "Insufficient funds",
            10020: "Prices changed",
            10021: "No quotes to process request",
            10022: "Invalid order expiration date",
            10023: "Order state changed",
            10024: "Too frequent requests",
            10025: "No changes in request",
            10026: "Autotrading disabled by server",
            10027: "Autotrading disabled by client",
            10028: "Request locked for processing",
            10029: "Order or position frozen",
            10030: "Invalid order filling type",
            10031: "No connection with trade server",
            10032: "Operation allowed only for live accounts",
            10033: "Maximum pending orders reached",
            10034: "Maximum order volume reached",
            10035: "Invalid or prohibited order type",
            10036: "Position with specified ticket not found",
            10038: "Close order already exists",
            10039: "Maximum positions reached",
            10040: "Position close rejected",
            10041: "Too long request",
            10042: "Close volume exceeds current position volume",
            10043: "Invalid close volume",
        }
        return error_messages.get(retcode, f"Unknown error ({retcode})")


# Singleton instance
mt5_client = MT5Client()
