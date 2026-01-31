"""
MetaApi broker client for trade execution on Linux/cloud.
Uses MetaApi.cloud REST API to connect to MT5 accounts.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import time

try:
    from metaapi_cloud_sdk import MetaApi
    METAAPI_AVAILABLE = True
except ImportError:
    METAAPI_AVAILABLE = False
    MetaApi = None

from config.settings import config
from models.trade import (
    Trade, TradeDirection, TradeStatus, AccountInfo, SymbolInfo
)
from utils.logging_utils import log_trade_event

logger = logging.getLogger("evobot.broker.metaapi")

# Cache settings to avoid rate limiting - reduced for more real-time data
ACCOUNT_INFO_CACHE_TTL = 5  # seconds - cache account info for 5 seconds
POSITIONS_CACHE_TTL = 3  # seconds - cache positions for 3 seconds
PRICE_CACHE_TTL = 2  # seconds - cache prices for 2 seconds

# Rate limit backoff settings
RATE_LIMIT_BACKOFF_BASE = 60  # Base backoff time in seconds when rate limited
RATE_LIMIT_BACKOFF_MAX = 600  # Maximum backoff time (10 minutes)


class MetaApiClient:
    """
    MetaApi client for trade execution via cloud API.
    Works on Linux and any platform without MT5 installed.
    """
    
    def __init__(self):
        self.connected = False
        self._lock = asyncio.Lock()
        self.account_info: Optional[AccountInfo] = None
        self.symbol_cache: Dict[str, SymbolInfo] = {}
        self.api: Optional[MetaApi] = None
        self.account = None
        self.connection = None
        
        # Cache for rate limiting protection
        self._account_info_cache: Optional[AccountInfo] = None
        self._account_info_cache_time: float = 0
        self._positions_cache: List[dict] = []
        self._positions_cache_time: float = 0
        self._price_cache: Dict[str, Tuple[float, float, float]] = {}  # symbol -> (bid, ask, timestamp)
        
        # Rate limit tracking
        self._rate_limit_until: float = 0  # Unix timestamp when rate limit expires
        self._rate_limit_count: int = 0  # Number of consecutive rate limit errors
    
    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited"""
        return time.time() < self._rate_limit_until
    
    def _handle_rate_limit_error(self, error_msg: str):
        """Handle rate limit error by setting backoff time"""
        if 'cpu credits' in str(error_msg).lower() or 'rate' in str(error_msg).lower():
            self._rate_limit_count += 1
            # Exponential backoff with max cap
            backoff_time = min(RATE_LIMIT_BACKOFF_BASE * (2 ** (self._rate_limit_count - 1)), RATE_LIMIT_BACKOFF_MAX)
            self._rate_limit_until = time.time() + backoff_time
            logger.warning(f"Rate limited! Backing off for {backoff_time} seconds (attempt {self._rate_limit_count})")
    
    def _clear_rate_limit(self):
        """Clear rate limit state after successful request"""
        self._rate_limit_count = 0
        self._rate_limit_until = 0
        
    async def connect(self, max_retries: int = 3) -> bool:
        """Connect to MT5 via MetaApi with retry logic"""
        if not METAAPI_AVAILABLE:
            logger.error("metaapi-cloud-sdk not installed. Install with: pip install metaapi-cloud-sdk")
            return False
        
        # Force reload Firebase settings to ensure we have fresh credentials
        try:
            from core.firebase_settings import firebase_settings
            from core.firebase_service import firebase_service
            if firebase_service.db_ref:
                if not firebase_settings._initialized:
                    firebase_settings.initialize(firebase_service.db_ref)
                    logger.info("Firebase settings initialized in broker client")
                else:
                    # Force reload to get fresh credentials
                    firebase_settings.reload_from_firebase()
                    logger.info("Firebase settings reloaded in broker client")
        except Exception as e:
            logger.warning(f"Could not initialize/reload Firebase settings: {e}")
        
        # Get credentials directly from firebase_settings to avoid any caching issues
        try:
            from core.firebase_settings import firebase_settings
            token = firebase_settings.metaapi_token
            account_id = firebase_settings.metaapi_account_id
            logger.info(f"Got credentials from firebase_settings directly")
        except Exception as e:
            logger.warning(f"Could not get credentials from firebase_settings: {e}, falling back to config")
            token = config.broker.metaapi_token
            account_id = config.broker.metaapi_account_id
        
        logger.info(f"MetaAPI Token check: {'SET' if token else 'NOT SET'} (length: {len(token) if token else 0})")
        logger.info(f"MetaAPI Account ID check: {'SET' if account_id else 'NOT SET'}")
        
        if not token:
            logger.error("METAAPI_TOKEN not configured")
            return False
            
        if not account_id:
            logger.error("METAAPI_ACCOUNT_ID not configured")
            return False
        
        # Clean credentials
        token = token.strip()
        account_id = account_id.strip()
        
        # Validate token format
        if not token.startswith('eyJ'):
            logger.error(f"Invalid MetaAPI token format - should be a JWT token (starts with: {token[:10] if token else 'empty'})")
            return False
        
        logger.info(f"MetaAPI Token: {token[:20]}... (length: {len(token)})")
        logger.info(f"MetaAPI Account ID: {account_id}")
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            async with self._lock:
                try:
                    logger.info(f"MetaApi connection attempt {attempt}/{max_retries}...")
                    
                    # Initialize MetaApi with fresh token
                    self.api = MetaApi(token)
                    
                    # Get account
                    logger.info(f"Getting account: {account_id}")
                    self.account = await self.api.metatrader_account_api.get_account(account_id)
                    
                    # Wait for deployment if needed
                    if self.account.state != 'DEPLOYED':
                        logger.info("Deploying MetaApi account...")
                        await self.account.deploy()
                        
                    # Wait for connection
                    if self.account.connection_status != 'CONNECTED':
                        logger.info("Waiting for MetaApi connection...")
                        await self.account.wait_connected()
                    
                    # Create RPC connection
                    self.connection = self.account.get_rpc_connection()
                    await self.connection.connect()
                    await self.connection.wait_synchronized()
                    
                    # Get account info
                    account_info = await self.connection.get_account_information()
                    
                    self.account_info = AccountInfo(
                        balance=account_info['balance'],
                        equity=account_info['equity'],
                        margin=account_info.get('margin', 0),
                        free_margin=account_info.get('freeMargin', account_info['equity']),
                        profit=account_info.get('profit', 0),
                        currency=account_info.get('currency', 'USD'),
                        leverage=account_info.get('leverage', 100),
                        server=account_info.get('server', ''),
                        login=account_info.get('login', 0),
                        name=account_info.get('name', '')
                    )
                    
                    self.connected = True
                    logger.info(f"Connected to MT5 via MetaApi: {self.account_info.server}")
                    logger.info(f"Account balance: {self.account_info.balance} {self.account_info.currency}")
                    
                    return True
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    logger.error(f"MetaApi connection attempt {attempt} failed: {e}")
                    
                    # Check for auth errors - don't retry if token is invalid
                    if 'unauthorized' in error_str.lower() or 'invalid auth-token' in error_str.lower():
                        logger.error("Authentication failed - check your MetaAPI token")
                        break
                    
                    # Wait before retry
                    if attempt < max_retries:
                        wait_time = attempt * 2  # Exponential backoff
                        logger.info(f"Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
        
        logger.error(f"MetaApi connection failed after {max_retries} attempts. Last error: {last_error}")
        return False
    
    async def disconnect(self):
        """Disconnect from MetaApi"""
        logger.info("Disconnecting from MetaApi...")
        try:
            if self.connection:
                try:
                    await self.connection.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
                self.connection = None
            
            if self.api:
                try:
                    await self.api.close()
                except Exception as e:
                    logger.warning(f"Error closing API: {e}")
                self.api = None
            
            self.account = None
            self.connected = False
            
            # Clear caches
            self._account_info_cache = None
            self._positions_cache = []
            self._price_cache = {}
            
            # Give time for resources to be released
            await asyncio.sleep(0.5)
            
            logger.info("Disconnected from MetaApi")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            # Force reset state even on error
            self.connected = False
            self.connection = None
            self.api = None
            self.account = None
    
    async def get_account_info(self, force_refresh: bool = False) -> Optional[AccountInfo]:
        """Get current account info with caching to avoid rate limits"""
        if not self.connected:
            return None
        
        current_time = time.time()
        
        # Check if we're rate limited - return cached data
        if self._is_rate_limited():
            logger.debug(f"Rate limited - returning cached account info")
            return self._account_info_cache or self.account_info
        
        # Return cached data if still valid and not forcing refresh
        if not force_refresh and self._account_info_cache:
            if current_time - self._account_info_cache_time < ACCOUNT_INFO_CACHE_TTL:
                logger.debug(f"Using cached account info (age: {current_time - self._account_info_cache_time:.1f}s)")
                return self._account_info_cache
            
        try:
            account_info = await self.connection.get_account_information()
            self.account_info = AccountInfo(
                balance=account_info['balance'],
                equity=account_info['equity'],
                margin=account_info.get('margin', 0),
                free_margin=account_info.get('freeMargin', account_info['equity']),
                profit=account_info.get('profit', 0),
                currency=account_info.get('currency', 'USD'),
                leverage=account_info.get('leverage', 100),
                server=account_info.get('server', ''),
                login=account_info.get('login', 0),
                name=account_info.get('name', '')
            )
            
            # Update cache
            self._account_info_cache = self.account_info
            self._account_info_cache_time = current_time
            self._clear_rate_limit()  # Clear rate limit on success
            
            return self.account_info
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error getting account info: {e}")
            self._handle_rate_limit_error(error_str)
            # Return cached data on error if available
            if self._account_info_cache:
                logger.info("Returning cached account info due to API error")
                return self._account_info_cache
            return self.account_info
    
    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information"""
        if not self.connected:
            return None
            
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]
        
        try:
            info = await self.connection.get_symbol_specification(symbol)
            price = await self.connection.get_symbol_price(symbol)
            
            if info and price:
                symbol_info = SymbolInfo(
                    name=info.get('symbol', symbol),
                    description=info.get('description', ''),
                    point=info.get('point', 0.00001),
                    digits=info.get('digits', 5),
                    spread=int((price.get('ask', 0) - price.get('bid', 0)) / info.get('point', 0.00001)),
                    spread_float=(price.get('ask', 0) - price.get('bid', 0)),
                    tick_size=info.get('tickSize', 0.00001),
                    tick_value=info.get('tickValue', 1),
                    volume_min=info.get('minVolume', 0.01),
                    volume_max=info.get('maxVolume', 100),
                    volume_step=info.get('volumeStep', 0.01),
                    bid=price.get('bid', 0),
                    ask=price.get('ask', 0)
                )
                self.symbol_cache[symbol] = symbol_info
                return symbol_info
                
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
        
        return None
    
    async def get_current_price(self, symbol: str, force_refresh: bool = False) -> Tuple[Optional[float], Optional[float]]:
        """Get current bid/ask price for symbol with caching"""
        if not self.connected:
            return None, None
        
        current_time = time.time()
        
        # Check if we're rate limited - return cached data
        if self._is_rate_limited() and symbol in self._price_cache:
            bid, ask, _ = self._price_cache[symbol]
            logger.debug(f"Rate limited - returning cached price for {symbol}")
            return bid, ask
        
        # Check cache first
        if not force_refresh and symbol in self._price_cache:
            bid, ask, cache_time = self._price_cache[symbol]
            if current_time - cache_time < PRICE_CACHE_TTL:
                logger.debug(f"Using cached price for {symbol} (age: {current_time - cache_time:.1f}s)")
                return bid, ask
            
        try:
            price = await self.connection.get_symbol_price(symbol)
            if price:
                bid = price.get('bid')
                ask = price.get('ask')
                # Update cache
                self._price_cache[symbol] = (bid, ask, current_time)
                self._clear_rate_limit()  # Clear rate limit on success
                return bid, ask
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error getting price for {symbol}: {e}")
            self._handle_rate_limit_error(error_str)
            # Return cached price on error if available
            if symbol in self._price_cache:
                bid, ask, _ = self._price_cache[symbol]
                return bid, ask
        
        return None, None
    
    async def check_spread(self, symbol: str) -> Tuple[bool, float]:
        """Check if spread is within acceptable limits"""
        if not self.connected:
            # If not connected, allow trade (spread will be checked at execution)
            logger.warning(f"Not connected - skipping spread check for {symbol}")
            return True, 0.0
        
        # If rate limited, use cached price for spread check
        if self._is_rate_limited() and symbol in self._price_cache:
            bid, ask, _ = self._price_cache[symbol]
            if bid and ask:
                spread_raw = ask - bid
                if 'XAU' in symbol:
                    spread_pips = spread_raw / 0.01
                elif 'XAG' in symbol:
                    spread_pips = spread_raw / 0.001
                elif 'JPY' in symbol:
                    spread_pips = spread_raw / 0.01
                else:
                    spread_pips = spread_raw / 0.0001
                max_spread = config.trading.symbol_max_spreads.get(symbol, config.trading.max_spread_pips)
                logger.debug(f"Rate limited - using cached spread for {symbol}: {spread_pips:.1f} pips")
                return spread_pips <= max_spread, spread_pips
        
        try:
            # Get fresh price data for accurate spread
            price = await self.connection.get_symbol_price(symbol)
            if price:
                bid = price.get('bid', 0)
                ask = price.get('ask', 0)
                spread_raw = ask - bid
                
                # Update price cache
                self._price_cache[symbol] = (bid, ask, time.time())
                self._clear_rate_limit()  # Clear rate limit on success
                
                # Convert to pips based on instrument type
                # Gold (XAUUSD): 1 pip = 0.01 (prices like 2750.00)
                # Silver (XAGUSD): 1 pip = 0.001
                # JPY pairs: 1 pip = 0.01 (prices like 150.00)
                # Standard forex: 1 pip = 0.0001 (prices like 1.3500)
                if 'XAU' in symbol:
                    spread_pips = spread_raw / 0.01  # Gold: 1 pip = 0.01
                elif 'XAG' in symbol:
                    spread_pips = spread_raw / 0.001  # Silver
                elif 'JPY' in symbol:
                    spread_pips = spread_raw / 0.01  # JPY pairs
                else:
                    spread_pips = spread_raw / 0.0001  # Standard forex
                
                logger.debug(f"Spread check {symbol}: bid={bid}, ask={ask}, spread={spread_pips:.1f} pips")
                
                # Use per-symbol max spread if defined, otherwise use default
                max_spread = config.trading.symbol_max_spreads.get(symbol, config.trading.max_spread_pips)
                is_acceptable = spread_pips <= max_spread
                
                if not is_acceptable:
                    logger.warning(f"Spread too high for {symbol}: {spread_pips:.1f} pips > {max_spread} max")
                
                return is_acceptable, spread_pips
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error checking spread for {symbol}: {e}")
            self._handle_rate_limit_error(error_str)
        
        # Default to allowing trade if we can't check spread
        return True, 0.0
    
    async def place_market_order(
        self,
        trade: Trade,
        lot_size: float,
        slippage: int = None
    ) -> Tuple[bool, Optional[int], str]:
        """Place a market order via MetaApi"""
        if not self.connected:
            return False, None, "Not connected to MetaApi"
        
        async with self._lock:
            try:
                symbol = trade.symbol
                
                # Normalize lot size
                symbol_info = await self.get_symbol_info(symbol)
                if symbol_info:
                    lot_size = self._normalize_lot(lot_size, symbol_info)
                
                # Place order using the correct method based on direction
                if trade.direction == TradeDirection.BUY:
                    result = await self.connection.create_market_buy_order(
                        symbol=symbol,
                        volume=lot_size,
                        stop_loss=trade.stop_loss,
                        take_profit=trade.take_profit_1,
                        options={'comment': f"EvoBot_{trade.id[:8]}"}
                    )
                else:
                    result = await self.connection.create_market_sell_order(
                        symbol=symbol,
                        volume=lot_size,
                        stop_loss=trade.stop_loss,
                        take_profit=trade.take_profit_1,
                        options={'comment': f"EvoBot_{trade.id[:8]}"}
                    )
                
                if result and (result.get('orderId') or result.get('positionId')):
                    ticket = int(result.get('positionId') or result.get('orderId', 0))
                    price = result.get('openPrice', 0)
                    
                    logger.info(f"Order placed via MetaApi: {symbol} {trade.direction.value} {lot_size} lots @ {price}, ticket: {ticket}")
                    
                    log_trade_event(
                        "ORDER_PLACED",
                        trade.id,
                        symbol,
                        {
                            "ticket": ticket,
                            "direction": trade.direction.value,
                            "lot_size": lot_size,
                            "price": price,
                            "sl": trade.stop_loss,
                            "tp": trade.take_profit_1
                        }
                    )
                    
                    # Invalidate cache after successful order
                    self.invalidate_cache()
                    return True, ticket, f"Order placed at {price}"
                else:
                    error_msg = result.get('stringCode', 'Unknown error') if result else 'No response'
                    logger.error(f"Order failed: {error_msg}")
                    return False, None, error_msg
                    
            except Exception as e:
                logger.error(f"Error placing order via MetaApi: {e}", exc_info=True)
                return False, None, str(e)
    
    async def close_position(self, ticket: int) -> Tuple[bool, str]:
        """Close a position by ticket"""
        if not self.connected:
            return False, "Not connected to MetaApi"
        
        async with self._lock:
            try:
                result = await self.connection.close_position(str(ticket))
                
                if result:
                    logger.info(f"Position {ticket} closed via MetaApi")
                    # Invalidate cache after closing position
                    self.invalidate_cache()
                    return True, "Position closed"
                else:
                    return False, "Failed to close position"
                    
            except Exception as e:
                logger.error(f"Error closing position: {e}")
                return False, str(e)
    
    async def modify_position(
        self,
        ticket: int,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Tuple[bool, str]:
        """Modify position SL/TP"""
        if not self.connected:
            return False, "Not connected to MetaApi"
        
        async with self._lock:
            try:
                result = await self.connection.modify_position(
                    str(ticket),
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                if result:
                    logger.info(f"Position {ticket} modified: SL={stop_loss}, TP={take_profit}")
                    # Invalidate cache after modifying position
                    self.invalidate_cache()
                    return True, "Position modified"
                else:
                    return False, "Failed to modify position"
                    
            except Exception as e:
                logger.error(f"Error modifying position: {e}")
                return False, str(e)
    
    async def get_positions(self, force_refresh: bool = False) -> List[dict]:
        """Get all open positions with caching to avoid rate limits"""
        if not self.connected:
            return []
        
        current_time = time.time()
        
        # Check if we're rate limited - return cached data
        if self._is_rate_limited():
            logger.debug(f"Rate limited - returning cached positions (expires in {self._rate_limit_until - current_time:.0f}s)")
            return self._positions_cache
        
        # Return cached data if still valid and not forcing refresh
        if not force_refresh and self._positions_cache:
            if current_time - self._positions_cache_time < POSITIONS_CACHE_TTL:
                logger.debug(f"Using cached positions (age: {current_time - self._positions_cache_time:.1f}s)")
                return self._positions_cache
        
        try:
            positions = await self.connection.get_positions()
            self._positions_cache = positions or []
            self._positions_cache_time = current_time
            self._clear_rate_limit()  # Clear rate limit on success
            return self._positions_cache
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error getting positions: {e}")
            self._handle_rate_limit_error(error_str)
            # Return cached data on error if available
            if self._positions_cache:
                logger.info("Returning cached positions due to API error")
                return self._positions_cache
            return []
    
    def invalidate_cache(self):
        """Invalidate all caches - call after placing/closing trades"""
        self._account_info_cache = None
        self._account_info_cache_time = 0
        self._positions_cache = []
        self._positions_cache_time = 0
        self._price_cache = {}
        logger.debug("MetaAPI caches invalidated")
    
    async def partial_close(
        self,
        ticket: int,
        volume: float
    ) -> Tuple[bool, Optional[int], str]:
        """Partially close a position"""
        if not self.connected:
            return False, None, "Not connected to MetaApi"
        
        async with self._lock:
            try:
                result = await self.connection.close_position_partially(
                    str(ticket),
                    volume=volume
                )
                
                if result:
                    new_ticket = result.get('positionId', ticket)
                    logger.info(f"Partial close of {ticket}: {volume} lots")
                    # Invalidate cache after partial close
                    self.invalidate_cache()
                    return True, new_ticket, "Partial close successful"
                else:
                    return False, None, "Failed to partially close"
                    
            except Exception as e:
                logger.error(f"Error with partial close: {e}")
                return False, None, str(e)
    
    def _normalize_lot(self, lot_size: float, symbol_info: SymbolInfo) -> float:
        """Normalize lot size to valid increment"""
        step = symbol_info.volume_step
        min_vol = symbol_info.volume_min
        max_vol = symbol_info.volume_max
        
        # Round to nearest step
        normalized = round(lot_size / step) * step
        
        # Clamp to min/max
        normalized = max(min_vol, min(max_vol, normalized))
        
        return round(normalized, 2)

# Singleton instance
metaapi_client = MetaApiClient()
