from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from uvicorn.protocols.utils import ClientDisconnected
from websockets.exceptions import ConnectionClosedOK
from fastapi.responses import JSONResponse
import asyncio
import logging
import os
from datetime import datetime
from dashboard.schemas import SignalTestRequest, ConfigUpdate, TradeAction
from dashboard.state import bot_state, broadcast_to_clients
from core.trade_manager import trade_manager
from core.risk_manager import risk_manager
from broker import broker_client
from telegram.listener import telegram_listener
from config.settings import config
from parsers.signal_parser import signal_parser
from core.firebase_service import firebase_service
# Import lifecycle functions
from dashboard.lifecycle import start_bot, stop_bot, reconnect_services

logger = logging.getLogger("evobot.dashboard.api")

router = APIRouter(prefix="/api", tags=["api"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(manager.active_connections)}")
    
    try:
        # Send initial snapshot
        if bot_state.is_running and bot_state.is_connected_mt5:
            try:
                account_info = await broker_client.get_account_info()
                if account_info:
                    await websocket.send_json({
                        "type": "account_update",
                        "data": account_info.to_dict()
                    })
            except:
                pass
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({"type": "ping"})
    
    except (WebSocketDisconnect, ClientDisconnected, ConnectionClosedOK):
        manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected. Remaining clients: {len(manager.active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {type(e).__name__}: {e}")
        manager.disconnect(websocket)

# Status & Bot Control

@router.get("/status")
async def get_status():
    """Get bot status"""
    account_info = None
    if bot_state.is_connected_mt5:
        # Avoid blocking if MT5 is slow
        try:
             account_info = await asyncio.wait_for(broker_client.get_account_info(), timeout=5.0)
        except:
             pass
    
    risk_status = risk_manager.get_risk_status() if bot_state.is_running else {}
    trade_stats = trade_manager.get_trade_stats()
    
    status_data = {
        "bot_running": bot_state.is_running,
        "telegram_connected": bot_state.is_connected_telegram,
        "mt5_connected": bot_state.is_connected_mt5,
        "start_time": bot_state.start_time.isoformat() if bot_state.start_time else None,
        "uptime_seconds": (datetime.utcnow() - bot_state.start_time).total_seconds() if bot_state.start_time else 0,
        "account": account_info.to_dict() if account_info else None,
        "risk": risk_status,
        "stats": trade_stats,
        "config": {
            "default_lot_size": config.trading.default_lot_size,
            "max_spread_pips": config.trading.max_spread_pips,
            "max_daily_drawdown_percent": config.trading.max_daily_drawdown_percent,
            "max_open_trades": config.trading.max_open_trades,
            "symbol_max_spreads": config.trading.symbol_max_spreads,
            "signal_channels": config.telegram.signal_channels,
            "notification_channel": config.telegram.notification_channel,
        }
    }
    
    # Sync to Firebase in background to not block response
    asyncio.create_task(firebase_service.update_status_async(status_data))
    
    return status_data

@router.post("/bot/start")
async def start_bot_endpoint(request: Request):
    """Start the trading bot"""
    from core.telegram_auth import telegram_auth_service
    
    # Get user from token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        is_valid, payload = telegram_auth_service.verify_token(token)
        if is_valid and payload:
            user_id = payload.get("user_id")
            # Store user_id in bot_state for MT5 connection
            bot_state.current_user_id = user_id
    
    return await start_bot()

@router.post("/bot/stop")
async def stop_bot_endpoint():
    """Stop the trading bot"""
    return await stop_bot()

@router.post("/bot/reconnect")
async def reconnect_endpoint():
    """Reconnect services"""
    return await reconnect_services()

# Trading Endpoints

@router.get("/positions")
async def get_mt5_positions():
    """Get all open positions directly from MT5"""
    if not bot_state.is_connected_mt5:
        return {"positions": [], "count": 0, "grouped": {}, "error": "MT5 not connected"}
    
    try:
        positions = await broker_client.get_positions()
        
        # Group positions
        grouped = {}
        processed_positions = []
        
        for p in positions or []:
            ticket = p.get("id")
            pos_data = {
                "id": str(ticket),
                "position_ticket": str(ticket),
                "symbol": p.get("symbol", ""),
                "lot_size": p.get("volume", 0),
                "profit": float(p.get("profit", 0)) + float(p.get("swap", 0)) + (float(p.get("commission", 0)) if isinstance(p.get("commission"), (int, float)) else 0),
                "entry_price": p.get("openPrice", 0),
                "current_price": p.get("currentPrice", 0),
                "direction": "BUY" if p.get("type") == "POSITION_TYPE_BUY" else "SELL",
            }
            processed_positions.append(pos_data)
            
            # Find associated trade to get grouping info
            trade = trade_manager.get_trade_by_ticket(ticket)
            signal_id = trade.signal_id if trade else "manual"
            channel_id = trade.channel_id if trade else None
            
            # Create or update group
            if signal_id not in grouped:
                # Try to get channel info if we have a channel_id
                channel_info = None
                if channel_id and firebase_service.db_ref:
                    channel_info = firebase_service.db_ref.child(f"users/{bot_state.current_user_id or 'default'}/channels_meta/{channel_id}").get()
                
                grouped[signal_id] = {
                    "positions": [],
                    "total_profit": 0,
                    "total_lots": 0,
                    "symbol": p.get("symbol", ""),
                    "channel_id": channel_id,
                    "channel": channel_info,
                    "signal_time": trade.created_at.isoformat() if trade else None,
                    "collapsed": False
                }
            
            grp = grouped[signal_id]
            grp["positions"].append(pos_data)
            grp["total_profit"] += pos_data["profit"]
            grp["total_lots"] += pos_data["lot_size"]

        return {
            "positions": processed_positions,
            "count": len(processed_positions),
            "grouped": grouped
        }
    except Exception as e:
        logger.error(f"Error fetching MT5 positions: {e}")
        return {"positions": [], "count": 0, "grouped": {}, "error": str(e)}

@router.post("/positions/{ticket}/close")
async def close_mt5_position(ticket: int):
    """Close a specific MT5 position by ticket number"""
    if not bot_state.is_connected_mt5:
        raise HTTPException(status_code=400, detail="MT5 not connected")
    
    try:
        success, msg = await broker_client.close_position(ticket)
        if success:
            return {"status": "success", "message": f"Position {ticket} closed"}
        else:
            raise HTTPException(status_code=500, detail=msg)
    except Exception as e:
        logger.error(f"Error closing position {ticket}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades")
async def get_trades(active_only: bool = False):
    """Get all trades or active trades only"""
    if active_only:
        trades = trade_manager.get_active_trades()
    else:
        trades = trade_manager.get_all_trades()
    
    return {
        "trades": [t.to_dict() for t in trades],
        "count": len(trades)
    }

@router.get("/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get specific trade details"""
    trade = trade_manager.get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade.to_dict()

@router.post("/signal/test")
async def test_signal(request: SignalTestRequest):
    """Test signal parsing"""
    signal = signal_parser.parse(request.message)
    return {
        "parsed": signal.to_dict(),
        "success": signal.parsed_successfully,
        "errors": signal.parse_errors
    }

@router.post("/config/update")
async def update_config(updates: ConfigUpdate):
    """Update bot configuration"""
    if updates.default_lot_size is not None:
        config.trading.default_lot_size = updates.default_lot_size
    if updates.max_spread_pips is not None:
        config.trading.max_spread_pips = updates.max_spread_pips
    if updates.max_daily_drawdown is not None:
        config.trading.max_daily_drawdown_percent = updates.max_daily_drawdown
    
    config.save()
    return {"status": "success", "message": "Configuration updated"}

@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    log_file = "logs/system.log"
    if not os.path.exists(log_file):
        return {"logs": []}
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        return {"logs": [line.strip() for line in recent_lines]}
    except:
        return {"logs": []}

@router.post("/test/telegram")
async def test_telegram_connection(request: Request):
    """Test Telegram connection"""
    body = await request.json()
    # Simple validation
    if not body.get("api_id") or not body.get("api_hash"):
         return JSONResponse(status_code=400, content={"success": False, "message": "Missing credentials"})
    return {"success": True, "message": "Credentials format valid"}

@router.post("/test/broker")
async def test_broker_connection(request: Request):
    """Test Broker connection"""
    body = await request.json()
    if not body.get("metaapi_token"):
         return JSONResponse(status_code=400, content={"success": False, "message": "Missing token"})
    return {"success": True, "message": "Credentials format valid"}

@router.get("/mt5/servers")
async def search_mt5_servers(query: str = ""):
    """Search available MT5 servers from terminal config"""
    import MetaTrader5 as mt5
    import configparser
    
    servers = []
    
    try:
        # Try to read servers from MT5 terminal config
        mt5_path = os.getenv('MT5_PATH', 'C:\\Program Files\\MetaTrader 5\\terminal64.exe')
        mt5_dir = os.path.dirname(mt5_path)
        config_path = os.path.join(mt5_dir, 'config', 'manager.ini')
        
        # Also check common.ini
        common_config = os.path.join(mt5_dir, 'config', 'common.ini')
        
        # Try to initialize MT5 and get symbols to infer server
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                current_server = account_info.server
                if current_server:
                    servers.append(current_server)
            mt5.shutdown()
        
        # Add comprehensive list of known MT5 servers worldwide
        known_servers = [
            # Exness
            'Exness-MT5Real', 'Exness-MT5Real2', 'Exness-MT5Real3', 'Exness-MT5Trial',
            'ExnessEU-Real', 'ExnessEU-Demo',
            # XM
            'XMGlobal-Real', 'XMGlobal-Real 2', 'XMGlobal-Real 3', 'XMGlobal-Demo',
            'XM-Real', 'XM-Demo',
            # IC Markets
            'ICMarkets-Live', 'ICMarkets-Live02', 'ICMarkets-Live03', 'ICMarkets-Demo',
            'ICMarketsSC-Live', 'ICMarketsSC-Demo',
            # FBS
            'FBS-Real', 'FBS-Real-2', 'FBS-Demo', 'FBS-MT5', 'FBS-MT5-Demo',
            # Pepperstone
            'Pepperstone-Live', 'Pepperstone-Live-01', 'Pepperstone-Demo',
            'PepperstoneUK-Live', 'PepperstoneUK-Demo',
            # FXTM / ForexTime
            'FXTM-ECN', 'FXTM-ECN-2', 'FXTM-ECN-Demo', 'FXTM-ECN-UK', 'FXTM-ECN-UK-Demo',
            # Alpari
            'Alpari-MT5-Demo', 'Alpari-MT5-Real', 'AlpariEU-Demo', 'AlpariEU-Real',
            # HotForex / HFMarkets
            'HotForex-Real', 'HotForex-Demo', 'HFMarkets-Real', 'HFMarkets-Demo',
            # OctaFX
            'OctaFX-Real', 'OctaFX-Demo', 'OctaFX-MT5Real', 'OctaFX-MT5Demo',
            # RoboForex
            'RoboForex-Pro', 'RoboForex-ProCent', 'RoboForex-ECN', 'RoboForex-Demo',
            # FxPro
            'FxPro-MT5', 'FxPro-MT5-Demo', 'FxProUK-MT5', 'FxProUK-MT5-Demo',
            # AvaTrade
            'AvaTrade-Live', 'AvaTrade-Demo', 'AvaTradeEU-Live', 'AvaTradeEU-Demo',
            # Admiral Markets
            'Admiral-Live', 'Admiral-Demo', 'AdmiralEU-Live', 'AdmiralEU-Demo',
            # Tickmill
            'Tickmill-Live', 'Tickmill-Demo', 'TickmillUK-Live', 'TickmillUK-Demo',
            # FusionMarkets
            'FusionMarkets-Live', 'FusionMarkets-Demo',
            # Vantage / VantageFX
            'Vantage-Live', 'Vantage-Demo', 'VantageFX-Live', 'VantageFX-Demo',
            'VantageInternational-Live', 'VantageInternational-Demo',
            # OANDA
            'OANDA-v20-Live', 'OANDA-v20-Practice',
            # IG
            'IG-Live', 'IG-Demo',
            # Plus500
            'Plus500-Live', 'Plus500-Demo',
            # eToro
            'eToro-Real', 'eToro-Demo',
            # Interactive Brokers
            'InteractiveBrokers-Live', 'InteractiveBrokers-Paper',
            # Saxo Bank
            'SaxoBank-Live', 'SaxoBank-Demo',
            # CMC Markets
            'CMCMarkets-Live', 'CMCMarkets-Demo',
            # City Index
            'CityIndex-Live', 'CityIndex-Demo',
            # FXCM
            'FXCM-USDReal', 'FXCM-Demo',
            # Forex.com / GAIN Capital
            'Forex.com-Live', 'Forex.com-Demo',
            # TD Ameritrade
            'TDAmeritrade-Live', 'TDAmeritrade-Paper',
            # ThinkMarkets
            'ThinkMarkets-Live', 'ThinkMarkets-Demo',
            # Swissquote
            'Swissquote-Live', 'Swissquote-Demo',
            # Dukascopy
            'Dukascopy-Live', 'Dukascopy-Demo',
            # FXDD
            'FXDD-MT5Live', 'FXDD-MT5Demo',
            # ATC Brokers
            'ATCBrokers-Live', 'ATCBrokers-Demo',
            # Blueberry Markets
            'BlueberryMarkets-Live', 'BlueberryMarkets-Demo',
            # EightCap
            'EightCap-Live', 'EightCap-Demo',
            # FP Markets
            'FPMarkets-Live', 'FPMarkets-Demo',
            # GO Markets
            'GOMarkets-Live', 'GOMarkets-Demo',
            # Axi (AxiTrader)
            'Axi-Live', 'Axi-Demo', 'AxiTrader-Live', 'AxiTrader-Demo',
            # BlackBull Markets
            'BlackBullMarkets-Live', 'BlackBullMarkets-Demo',
            # Eightcap
            'Eightcap-Live', 'Eightcap-Demo',
            # Global Prime
            'GlobalPrime-Live', 'GlobalPrime-Demo',
            # Hantec Markets
            'HantecMarkets-Live', 'HantecMarkets-Demo',
            # LiteForex
            'LiteForex-Real', 'LiteForex-Demo',
            # NordFX
            'NordFX-Real', 'NordFX-Demo',
            # Orbex
            'Orbex-Live', 'Orbex-Demo',
            # Traders Trust
            'TradersTrust-Live', 'TradersTrust-Demo',
            # Turnkey Forex
            'TurnkeyForex-Live', 'TurnkeyForex-Demo',
            # Valutrades
            'Valutrades-Live', 'Valutrades-Demo',
            # Windsor Brokers
            'WindsorBrokers-Live', 'WindsorBrokers-Demo',
            # XTB
            'XTB-Real', 'XTB-Demo',
            # FXGT
            'FXGT-Live', 'FXGT-Demo',
            # Errante
            'Errante-Live', 'Errante-Demo',
            # Weltrade
            'Weltrade-Live', 'Weltrade-Demo',
            # FXOpen
            'FXOpen-Real', 'FXOpen-Demo',
            # InstaForex
            'InstaForex-Server', 'InstaForex-Demo',
            # AMarkets
            'AMarkets-Real', 'AMarkets-Demo',
            # FreshForex
            'FreshForex-Server', 'FreshForex-Demo',
            # JustForex
            'JustForex-Real', 'JustForex-Demo',
            # LiteFinance
            'LiteFinance-ECN', 'LiteFinance-Demo',
            # Forex4you
            'Forex4you-Real', 'Forex4you-Demo',
            # FXChoice
            'FXChoice-Live', 'FXChoice-Demo',
            # FXCC
            'FXCC-ECN', 'FXCC-Demo',
            # FXGlory
            'FXGlory-Real', 'FXGlory-Demo',
            # FXPRIMUS
            'FXPRIMUS-Live', 'FXPRIMUS-Demo',
            # IronFX
            'IronFX-Live', 'IronFX-Demo',
            # JustMarkets
            'JustMarkets-Live', 'JustMarkets-Demo',
            # Libertex
            'Libertex-Live', 'Libertex-Demo',
            # Markets.com
            'Markets.com-Live', 'Markets.com-Demo',
            # Moneta Markets
            'MonetaMarkets-Live', 'MonetaMarkets-Demo',
            # MultiBank
            'MultiBank-Live', 'MultiBank-Demo',
            # Octa (OctaFX)
            'Octa-Real', 'Octa-Demo',
            # PaxForex
            'PaxForex-Live', 'PaxForex-Demo',
            # Scope Markets
            'ScopeMarkets-Live', 'ScopeMarkets-Demo',
            # Spreadex
            'Spreadex-Live', 'Spreadex-Demo',
            # Squared Financial
            'SquaredFinancial-Live', 'SquaredFinancial-Demo',
            # Titan FX
            'TitanFX-Live', 'TitanFX-Demo',
            # Trade Nation
            'TradeNation-Live', 'TradeNation-Demo',
            # Tradeview
            'Tradeview-Live', 'Tradeview-Demo',
            # VT Markets
            'VTMarkets-Live', 'VTMarkets-Demo',
        ]
        
        servers.extend(known_servers)
        # Remove duplicates while preserving order
        seen = set()
        servers = [x for x in servers if not (x in seen or seen.add(x))]
        
        # Filter by query
        if query:
            filtered = [s for s in servers if query.lower() in s.lower()]
            return {"servers": filtered[:15]}
        
        return {"servers": servers[:15]}
        
    except Exception as e:
        logger.error(f"Error searching MT5 servers: {e}")
        # Fallback to basic list
        basic_servers = [
            'Exness-MT5Real', 'XMGlobal-Real', 'ICMarkets-Live', 'Pepperstone-Live',
            'FBS-Real', 'FXTM-ECN', 'Alpari-MT5-Real', 'HotForex-Real',
            'OctaFX-Real', 'RoboForex-Pro', 'FxPro-MT5', 'AvaTrade-Live',
            'Admiral-Live', 'Tickmill-Live', 'FusionMarkets-Live'
        ]
        if query:
            filtered = [s for s in basic_servers if query.lower() in s.lower()]
            return {"servers": filtered}
        return {"servers": basic_servers}

@router.get("/mt5/credentials")
async def get_mt5_credentials(request: Request):
    """Check if user has MT5 credentials stored"""
    from core.mt5_credentials import mt5_store
    from core.telegram_auth import telegram_auth_service
    
    # Get user from token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    has_creds = mt5_store.has_credentials(user_id)
    creds = mt5_store.get(user_id) if has_creds else None
    
    # If not in local store, try Firebase
    if not creds and firebase_service.db_ref:
        fb_creds = firebase_service.db_ref.child(f"users/{user_id}/mt5_credentials").get()
        if fb_creds:
            mt5_store.set(user_id, fb_creds["server"], fb_creds["login"], fb_creds["password"])
            creds = fb_creds
            has_creds = True
    
    return {
        "has_credentials": has_creds,
        "server": creds["server"] if creds else None,
        "login": creds["login"] if creds else None
    }

@router.post("/mt5/test")
async def test_mt5_connection(request: Request):
    """Test MT5 connection and store credentials on success"""
    from core.mt5_credentials import mt5_store
    from core.telegram_auth import telegram_auth_service
    
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "MetaTrader5 package not installed"}
        )
    
    # Get user from token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid request body")
    
    server = body.get("server", "").strip()
    login = body.get("login", "").strip()
    password = body.get("password", "").strip()
    
    if not all([server, login, password]):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Server, login, and password are required"}
        )
    
    # Validate login is numeric
    try:
        login_int = int(login)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Login must be a number"}
        )
    
    # Test connection
    try:
        mt5.shutdown()
        
        # Initialize with credentials directly
        if not mt5.initialize(login=login_int, password=password, server=server):
            error = mt5.last_error()
            error_code = error[0] if isinstance(error, tuple) else error
            
            if error_code == -2:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "MT5 terminal not found. Install MetaTrader 5."}
                )
            elif error_code == -6:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Login failed. Verify your server name, login, and password."}
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"Connection failed: {error}"}
                )
        
        # Get account info to verify
        account_info = mt5.account_info()
        if not account_info:
            error = mt5.last_error()
            mt5.shutdown()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Failed to get account info: {error}"}
            )
        
        # Success - store credentials
        user_id = payload.get("user_id")
        mt5_store.set(user_id, server, login, password)
        
        # Store in Firebase
        if firebase_service.db_ref:
            firebase_service.db_ref.child(f"users/{user_id}/mt5_credentials").set({
                "server": server,
                "login": login,
                "password": password
            })
        
        mt5.shutdown()
        
        return {
            "success": True,
            "message": "MT5 connection successful",
            "account": {
                "login": account_info.login,
                "server": account_info.server,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "profit": account_info.profit,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "name": account_info.name,
                "company": account_info.company
            }
        }
    except Exception as e:
        try:
            mt5.shutdown()
        except:
            pass
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Connection error: {str(e)}"}
        )

@router.get("/mt5/account")
async def get_mt5_account_info(request: Request):
    """Get MT5 account information"""
    from core.mt5_credentials import mt5_store
    from core.telegram_auth import telegram_auth_service
    
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise HTTPException(status_code=400, detail="MetaTrader5 not installed")
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    creds = mt5_store.get(user_id)
    if not creds:
        raise HTTPException(status_code=404, detail="No MT5 credentials found")
    
    try:
        mt5.shutdown()
        if not mt5.initialize(login=int(creds["login"]), password=creds["password"], server=creds["server"]):
            raise HTTPException(status_code=400, detail="Failed to connect to MT5")
        
        account_info = mt5.account_info()
        if not account_info:
            mt5.shutdown()
            raise HTTPException(status_code=400, detail="Failed to get account info")
        
        mt5.shutdown()
        
        return {
            "login": account_info.login,
            "server": account_info.server,
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "profit": account_info.profit,
            "currency": account_info.currency,
            "leverage": account_info.leverage,
            "name": account_info.name,
            "company": account_info.company
        }
    except Exception as e:
        try:
            mt5.shutdown()
        except:
            pass
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mt5/logout")
async def logout_mt5(request: Request):
    """Logout from MT5 and clear stored credentials"""
    from core.mt5_credentials import mt5_store
    from core.telegram_auth import telegram_auth_service
    from core.firebase_settings import firebase_settings
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    mt5_store.remove(user_id)
    
    # Remove from Firebase
    if firebase_service.db_ref:
        firebase_service.db_ref.child(f"users/{user_id}/mt5_credentials").delete()
    
    return {"success": True, "message": "Logged out from MT5"}






