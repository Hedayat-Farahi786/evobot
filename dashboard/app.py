"""
Web Dashboard for EvoBot Trading System
FastAPI-based web interface for monitoring and controlling the bot
Enhanced with secure authentication and admin controls
Optimized for 24/7 long-running operation
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
import asyncio
import os
import gc
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from config.settings import config
from telegram.listener import telegram_listener
from broker import broker_client
from core.trade_manager import trade_manager
from core.risk_manager import risk_manager
from core.notifier import notifier
from parsers.signal_parser import signal_parser
from models.trade import Signal, Trade, TradeDirection, TradeStatus
from core.firebase_service import firebase_service
from core.security import security_manager
from core.firebase_auth import firebase_auth_service, init_firebase_auth
from core.telegram_auth import telegram_auth_service
from pydantic import BaseModel, EmailStr
import jwt

logger = logging.getLogger("evobot.dashboard")

# Initialize Firebase Auth on module load to create default admin
init_firebase_auth()

app = FastAPI(
    title="EvoBot Dashboard",
    version="2.0.0",
    docs_url="/api/docs" if os.getenv("ENABLE_API_DOCS", "false").lower() == "true" else None,
    redoc_url=None
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    client_ip = get_client_ip(request)
    
    # Skip rate limiting for static files
    if request.url.path.startswith("/static"):
        return await call_next(request)
    
    allowed, remaining = security_manager.check_rate_limit(client_ip)
    
    if not allowed:
        security_manager.audit_log(
            "rate_limit_exceeded",
            ip_address=client_ip,
            details={"path": request.url.path},
            severity="warning"
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
            headers={"Retry-After": "60"}
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

# Initialize Firebase on startup
@app.on_event("startup")
async def startup_event():
    firebase_service.initialize()
    firebase_auth_service.initialize()
    
    # Initialize Firebase settings
    from core.firebase_settings import firebase_settings
    if firebase_service.db_ref:
        firebase_settings.initialize(firebase_service.db_ref)
        logger.info("Firebase settings initialized")
    
    logger.info("Firebase services initialized")
    
    # Auto-start the bot if AUTO_START environment variable is set
    import os
    if os.getenv("AUTO_START_BOT", "false").lower() == "true":
        logger.info("AUTO_START_BOT enabled - starting bot automatically...")
        # Schedule bot startup after a short delay to let the server fully start
        asyncio.create_task(_auto_start_bot())

async def _auto_start_bot():
    """Auto-start the bot after a short delay"""
    await asyncio.sleep(2)  # Wait for server to be ready
    try:
        # Import here to avoid circular imports
        from dashboard.app import start_bot
        await start_bot()
        logger.info("Bot auto-started successfully")
    except Exception as e:
        logger.error(f"Failed to auto-start bot: {e}")

# Global state
class BotState:
    def __init__(self):
        self.is_running = False
        self.is_connected_telegram = False
        self.is_connected_mt5 = False
        self.start_time: Optional[datetime] = None
        self.websocket_clients: List[WebSocket] = []

bot_state = BotState()

# Pydantic models for API
class SignalTestRequest(BaseModel):
    message: str

class ConfigUpdate(BaseModel):
    default_lot_size: Optional[float] = None
    max_spread_pips: Optional[float] = None
    max_daily_drawdown: Optional[float] = None
    max_open_trades: Optional[int] = None
    symbol_max_spreads: Optional[Dict[str, float]] = None

class TradeAction(BaseModel):
    trade_id: str
    action: str  # close, modify_sl, modify_tp

# Firebase Auth Models
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str

class UserRoleUpdateRequest(BaseModel):
    role: str  # Admin, User, Viewer

# WebSocket manager
async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected WebSocket clients"""
    for client in bot_state.websocket_clients[:]:
        try:
            await client.send_json(message)
        except:
            bot_state.websocket_clients.remove(client)

# Helper functions
def get_client_ip(request: Request) -> str:
    """Get client IP from request"""
    if x_forwarded := request.headers.get("X-Forwarded-For"):
        return x_forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

async def get_current_user(request: Request):
    """Dependency: Get current user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = firebase_auth_service.verify_jwt_token(token)
    
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = firebase_auth_service.get_user_by_uid(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_admin_user(request: Request):
    """Dependency: Get current user and verify admin role"""
    user = await get_current_user(request)
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# API Routes - Authentication
@app.post("/api/auth/signup")
async def signup(request_data: SignupRequest, request: Request):
    """Register new user with Firebase"""
    client_ip = get_client_ip(request)
    
    success, message, user = firebase_auth_service.create_user(
        email=request_data.email,
        password=request_data.password,
        display_name=request_data.display_name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "user": {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        }
    }

@app.post("/api/auth/login")
async def login(credentials: LoginRequest, request: Request):
    """Login endpoint with Firebase authentication"""
    client_ip = get_client_ip(request)
    
    success, message, token_data = firebase_auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password,
        ip_address=client_ip
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return token_data


@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str, request: Request):
    """Refresh access token"""
    is_valid, payload = firebase_auth_service.verify_jwt_token(refresh_token)
    
    if not is_valid or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = firebase_auth_service.get_user_by_uid(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new access token
    access_token = firebase_auth_service._create_jwt_token(
        user_id=user["uid"],
        email=user["email"],
        role=user.get("role", "Viewer"),
        expires_in=3600
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }


@app.post("/api/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout and invalidate token"""
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.split(" ")[1]
        security_manager.audit_log(
            "logout",
            current_user.get("email"),
            get_client_ip(request),
            details="User logged out",
            severity="info"
        )
    
    return {"message": "Logged out successfully"}


@app.post("/api/auth/change-password")
async def change_password_endpoint(
    data: PasswordChangeRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Change current user's password"""
    success, message = firebase_auth_service.change_password(
        email=current_user["email"],
        current_password=data.current_password,
        new_password=data.new_password,
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "uid": current_user.get("uid"),
        "email": current_user.get("email"),
        "display_name": current_user.get("display_name"),
        "role": current_user.get("role", "Viewer"),
        "created_at": current_user.get("created_at"),
        "last_login": current_user.get("last_login"),
        "login_count": current_user.get("login_count", 0)
    }


# ============================================
# Telegram Authentication Routes
# ============================================

@app.get("/api/auth/telegram/status")
async def telegram_auth_status():
    """Check if Telegram session is available for authentication"""
    is_valid, user_info = await telegram_auth_service.check_telegram_session()
    return {
        "has_session": is_valid,
        "user": user_info if is_valid else None
    }


@app.post("/api/auth/telegram/login")
async def telegram_login(request: Request):
    """
    Authenticate using Telegram session.
    This uses the existing Telegram session to authenticate the user.
    """
    client_ip = get_client_ip(request)
    
    success, message, token_data = await telegram_auth_service.authenticate()
    
    if not success:
        security_manager.audit_log(
            "telegram_login_failed",
            ip_address=client_ip,
            details={"message": message},
            severity="warning"
        )
        raise HTTPException(status_code=401, detail=message)
    
    security_manager.audit_log(
        "telegram_login_success",
        token_data["user"]["username"] or str(token_data["user"]["id"]),
        ip_address=client_ip,
        details={"user_id": token_data["user"]["id"]},
        severity="info"
    )
    
    return token_data


@app.post("/api/auth/telegram/refresh")
async def telegram_refresh_token(request: Request):
    """Refresh access token using refresh token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    refresh_token = auth_header.split(" ")[1]
    success, token_data = telegram_auth_service.refresh_access_token(refresh_token)
    
    if not success:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    return token_data


@app.post("/api/auth/telegram/logout")
async def telegram_logout(request: Request):
    """Logout and invalidate session"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        is_valid, payload = telegram_auth_service.verify_token(token)
        if is_valid and payload:
            telegram_auth_service.invalidate_session(payload.get("user_id"))
            security_manager.audit_log(
                "telegram_logout",
                str(payload.get("user_id")),
                ip_address=get_client_ip(request),
                details="User logged out",
                severity="info"
            )
    
    return {"message": "Logged out successfully"}


@app.get("/api/auth/telegram/me")
async def telegram_get_me(request: Request):
    """Get current Telegram user info from token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = telegram_auth_service.get_user_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user.to_dict()


# ============================================
# Admin Routes
# ============================================

@app.get("/api/admin/users")
async def get_users(current_user: dict = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = firebase_auth_service.list_users()
    return {"users": users}


@app.post("/api/admin/users")
async def create_user_admin(
    request_data: SignupRequest,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Create new user (admin only)"""
    success, message, user = firebase_auth_service.create_user(
        email=request_data.email,
        password=request_data.password,
        display_name=request_data.display_name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "user": {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        }
    }


@app.post("/api/admin/users/{email}/reset-password")
async def reset_password_admin(
    email: str,
    data: PasswordResetRequest,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Admin reset user password"""
    success, message = firebase_auth_service.reset_password(
        email=email,
        new_password=data.new_password,
        admin_email=current_user.get("email"),
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@app.post("/api/admin/users/{email}/role")
async def update_user_role(
    email: str,
    data: UserRoleUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Update user role (admin only)"""
    success, message = firebase_auth_service.update_user_role(
        email=email,
        new_role=data.role,
        admin_email=current_user.get("email"),
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@app.post("/api/admin/users/{email}/unlock")
async def unlock_user_account(
    email: str,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Unlock user account (remove login lockout)"""
    success, message = firebase_auth_service.unlock_account(
        email=email,
        admin_email=current_user.get("email"),
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@app.get("/api/admin/security/stats")
async def get_security_stats(current_user: dict = Depends(get_admin_user)):
    """Get security statistics"""
    return {
        "users": len(firebase_auth_service.list_users()),
        "failed_attempts": len(security_manager.failed_attempts),
        "locked_accounts": len(security_manager.account_lockouts),
        "active_sessions": len(security_manager.active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/admin/security/audit")
async def get_audit_logs(skip: int = 0, limit: int = 100, current_user: dict = Depends(get_admin_user)):
    """Get audit logs"""
    try:
        with open("logs/audit.log", "r") as f:
            logs = []
            for line in f:
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except:
                    pass
            logs.reverse()
            return {"logs": logs[skip:skip+limit], "total": len(logs)}
    except FileNotFoundError:
        return {"logs": [], "total": 0}


# Page Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    with open(dashboard_path, 'r') as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    login_path = os.path.join(os.path.dirname(__file__), "templates", "login.html")
    with open(login_path, 'r') as f:
        return f.read()

@app.get("/assets/{folder}/{filename}")
async def serve_asset(folder: str, filename: str):
    """Serve static assets from assets folder"""
    from fastapi.responses import FileResponse
    asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", folder, filename)
    if os.path.exists(asset_path):
        return FileResponse(asset_path)
    raise HTTPException(status_code=404, detail="Asset not found")

@app.get("/api/status")
async def get_status():
    """Get bot status"""
    account_info = None
    if bot_state.is_connected_mt5:
        account_info = await broker_client.get_account_info()
    
    risk_status = risk_manager.get_risk_status() if bot_state.is_running else {}
    # Always get trade stats - they're stored in persistence even when bot is not running
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
    
    # Sync to Firebase
    firebase_service.update_status(status_data)
    if account_info:
        firebase_service.update_account(account_info.to_dict())
    firebase_service.update_stats(trade_stats)
    
    return status_data


@app.get("/api/positions")
async def get_mt5_positions():
    """Get all open positions directly from MT5 with signal/channel info"""
    if not bot_state.is_connected_mt5:
        return {"positions": [], "count": 0, "grouped": {}, "error": "MT5 not connected"}
    
    try:
        positions = await broker_client.get_positions()
        formatted_positions = []
        
        # Load channels cache for channel info
        channels_cache = load_cached_channels()
        channels_by_id = {}
        for ch in channels_cache.get("channels", []):
            ch_id = str(ch.get("id", ""))
            channels_by_id[ch_id] = ch
            # Also map without -100 prefix
            if ch_id.startswith("-100"):
                channels_by_id[ch_id[4:]] = ch
        
        # Get all trades (not just active) to match positions with signals
        all_trades = trade_manager.get_all_trades()
        trades_by_ticket = {}
        trades_by_id_suffix = {}
        
        for trade in all_trades:
            # Map by ticket
            if trade.position_ticket:
                trades_by_ticket[str(trade.position_ticket)] = trade
            # Also check position_tickets list
            for pt in trade.position_tickets:
                if pt.get("ticket"):
                    trades_by_ticket[str(pt.get("ticket"))] = trade
            # Map by trade ID suffix (last 8 chars) for matching EvoBot_xxxxx comments
            trade_id_suffix = trade.id[-8:] if trade.id else ""
            if trade_id_suffix:
                trades_by_id_suffix[trade_id_suffix] = trade
        
        for pos in positions:
            ticket = str(pos.get("id", ""))
            trade = trades_by_ticket.get(ticket)
            
            # If not found by ticket, try matching by comment (EvoBot_xxxxx)
            if not trade:
                comment = pos.get("comment", "")
                if comment.startswith("EvoBot_"):
                    suffix = comment[7:]  # Extract xxxxx from EvoBot_xxxxx
                    trade = trades_by_id_suffix.get(suffix)
            
            # Get channel info if trade exists
            channel_info = None
            signal_time = None
            signal_id = None
            
            if trade:
                signal_id = trade.signal_id
                channel_id = str(trade.channel_id) if trade.channel_id else ""
                signal_time = trade.created_at.isoformat() if trade.created_at else None
                
                # Try to find channel info
                if channel_id in channels_by_id:
                    ch = channels_by_id[channel_id]
                    channel_info = {
                        "id": ch.get("id"),
                        "name": ch.get("name", "Unknown Channel"),
                        "photo": ch.get("photo")
                    }
            
            formatted_positions.append({
                "id": str(pos.get("id", "")),
                "position_ticket": ticket,
                "symbol": pos.get("symbol", ""),
                "direction": "BUY" if pos.get("type") == "POSITION_TYPE_BUY" else "SELL",
                "lot_size": pos.get("volume", 0),
                "entry_price": pos.get("openPrice", 0),
                "current_price": pos.get("currentPrice", 0),
                "stop_loss": pos.get("stopLoss", 0),
                "take_profit_1": pos.get("takeProfit", 0),
                "profit": pos.get("profit", 0) + pos.get("swap", 0) + pos.get("commission", 0),
                "swap": pos.get("swap", 0),
                "commission": pos.get("commission", 0),
                "open_time": pos.get("time", ""),
                "magic": pos.get("magic", 0),
                "comment": pos.get("comment", ""),
                "signal_id": signal_id,
                "signal_time": signal_time,
                "channel": channel_info
            })
        
        # Group positions by signal_id, or by symbol+time for unmatched positions
        grouped = {}
        
        # First, try to group positions without signal_id by symbol and open time
        from datetime import timedelta
        unmatched_positions = [p for p in formatted_positions if not p.get("signal_id")]
        matched_positions = [p for p in formatted_positions if p.get("signal_id")]
        
        # Group unmatched positions by symbol and similar open time (within 5 seconds)
        time_groups = {}
        for pos in unmatched_positions:
            symbol = pos.get("symbol", "")
            open_time_str = pos.get("open_time", "")
            entry_price = pos.get("entry_price", 0)
            
            # Create a group key based on symbol and entry price
            # Positions from the same signal typically have same symbol, entry price
            group_key = f"{symbol}_{entry_price}"
            
            if group_key not in time_groups:
                time_groups[group_key] = {
                    "signal_id": f"auto_{symbol}_{len(time_groups)}",
                    "channel": None,
                    "signal_time": open_time_str,
                    "positions": [],
                    "total_profit": 0,
                    "total_lots": 0,
                    "symbol": symbol
                }
            time_groups[group_key]["positions"].append(pos)
            time_groups[group_key]["total_profit"] += pos.get("profit", 0)
            time_groups[group_key]["total_lots"] += pos.get("lot_size", 0)
        
        # Add time-based groups to main grouped dict
        for key, group in time_groups.items():
            grouped[group["signal_id"]] = group
        
        # Add matched positions to their signal groups
        for pos in matched_positions:
            sig_id = pos.get("signal_id")
            if sig_id not in grouped:
                grouped[sig_id] = {
                    "signal_id": sig_id,
                    "channel": pos.get("channel"),
                    "signal_time": pos.get("signal_time"),
                    "positions": [],
                    "total_profit": 0,
                    "total_lots": 0
                }
            grouped[sig_id]["positions"].append(pos)
            grouped[sig_id]["total_profit"] += pos.get("profit", 0)
            grouped[sig_id]["total_lots"] += pos.get("lot_size", 0)
        
        return {
            "positions": formatted_positions,
            "grouped": grouped,
            "count": len(formatted_positions),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching MT5 positions: {e}")
        return {"positions": [], "count": 0, "grouped": {}, "error": str(e)}


@app.post("/api/positions/{ticket}/close")
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


@app.get("/api/prices")
async def get_prices(symbols: str = "XAUUSD,EURUSD,GBPUSD,USDJPY,GBPJPY"):
    """Get real-time prices for specified symbols"""
    if not bot_state.is_connected_mt5:
        return {"prices": {}, "timestamp": datetime.utcnow().isoformat()}
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    prices = {}
    
    for symbol in symbol_list:
        try:
            bid, ask = await broker_client.get_current_price(symbol)
            spread_ok, spread_pips = await broker_client.check_spread(symbol)
            
            prices[symbol] = {
                "bid": bid,
                "ask": ask,
                "spread_pips": round(spread_pips, 2) if spread_pips else None,
                "spread_ok": spread_ok,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            prices[symbol] = {"bid": None, "ask": None, "spread_pips": None, "spread_ok": False}
    
    # Sync to Firebase
    firebase_service.update_prices(prices)
    
    return {"prices": prices, "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/bot/start")
async def start_bot():
    """Start the trading bot - requires all connections to succeed"""
    if bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    # Kill any existing main.py processes
    import subprocess
    result = subprocess.run(['pgrep', '-f', 'python.*main.py'], capture_output=True, text=True)
    if result.returncode == 0:
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid:
                try:
                    subprocess.run(['kill', '-9', pid], capture_output=True)
                    logger.info(f"Killed existing main.py process: {pid}")
                except:
                    pass
        # Wait a moment for processes to terminate
        await asyncio.sleep(1)
    
    connection_errors = []
    
    try:
        # Broadcast progress: MT5 connecting
        await broadcast_to_clients({
            "type": "startup_progress",
            "data": {"step": "mt5", "status": "loading"}
        })
        
        # Connect to MT5 with timeout - increased to 60s for slow connections
        logger.info("Connecting to MT5...")
        mt5_connected = False
        mt5_error = None
        try:
            mt5_connected = await asyncio.wait_for(broker_client.connect(), timeout=60)
        except asyncio.TimeoutError:
            mt5_error = "Connection timed out after 60s"
            logger.warning(f"MT5: {mt5_error}")
        except Exception as mt5_err:
            mt5_error = str(mt5_err)[:100]
            logger.error(f"MT5 connection error: {mt5_err}")
        
        bot_state.is_connected_mt5 = mt5_connected
        
        if not mt5_connected:
            connection_errors.append(f"MT5: {mt5_error or 'Connection failed'}")
            await broadcast_to_clients({
                "type": "startup_progress",
                "data": {"step": "mt5", "status": "failed", "connected": False, "message": mt5_error or "Connection failed"}
            })
        else:
            logger.info("MT5 connected successfully")
            await broadcast_to_clients({
                "type": "startup_progress",
                "data": {"step": "mt5", "status": "success", "connected": True}
            })
        
        # Broadcast progress: Telegram connecting
        await broadcast_to_clients({
            "type": "startup_progress",
            "data": {"step": "telegram", "status": "loading"}
        })
        
        # Start Telegram listener with timeout - increased to 45s
        logger.info("Starting Telegram listener...")
        telegram_connected = False
        telegram_error = None
        try:
            await asyncio.wait_for(telegram_listener.start(), timeout=45)
            telegram_connected = telegram_listener.client and telegram_listener.client.is_connected()
            bot_state.is_connected_telegram = telegram_connected
            if telegram_connected:
                logger.info("Telegram connected successfully")
                await broadcast_to_clients({
                    "type": "startup_progress",
                    "data": {"step": "telegram", "status": "success", "connected": True}
                })
            else:
                telegram_error = "Client not fully connected"
                logger.warning(f"Telegram: {telegram_error}")
                await broadcast_to_clients({
                    "type": "startup_progress",
                    "data": {"step": "telegram", "status": "failed", "connected": False, "message": telegram_error}
                })
        except asyncio.TimeoutError:
            telegram_error = "Connection timed out after 45s"
            logger.warning(f"Telegram: {telegram_error}")
            bot_state.is_connected_telegram = False
            await broadcast_to_clients({
                "type": "startup_progress",
                "data": {"step": "telegram", "status": "failed", "connected": False, "message": telegram_error}
            })
        except Exception as tel_err:
            telegram_error = str(tel_err)[:100]
            logger.error(f"Telegram connection failed: {tel_err}")
            bot_state.is_connected_telegram = False
            await broadcast_to_clients({
                "type": "startup_progress",
                "data": {"step": "telegram", "status": "failed", "connected": False, "message": telegram_error}
            })
        
        if not telegram_connected:
            connection_errors.append(f"Telegram: {telegram_error or 'Connection failed'}")
        
        # Broadcast progress: Account data loading
        await broadcast_to_clients({
            "type": "startup_progress",
            "data": {"step": "account", "status": "loading"}
        })
        
        # Check account info
        account_ok = False
        account_error = None
        if mt5_connected:
            try:
                account_info = await broker_client.get_account_info()
                if account_info and hasattr(account_info, 'balance') and account_info.balance is not None:
                    account_ok = True
                    logger.info(f"Account info retrieved: balance={account_info.balance}")
                else:
                    account_error = "Could not retrieve account balance"
            except Exception as acc_err:
                account_error = str(acc_err)[:100]
                logger.error(f"Account info error: {acc_err}")
        else:
            account_error = "MT5 not connected"
        
        if not account_ok:
            connection_errors.append(f"Account: {account_error or 'Failed to get account info'}")
            await broadcast_to_clients({
                "type": "startup_progress",
                "data": {"step": "account", "status": "failed", "connected": False, "message": account_error}
            })
        else:
            await broadcast_to_clients({
                "type": "startup_progress",
                "data": {"step": "account", "status": "success", "connected": True}
            })
        
        # Check if all connections succeeded
        all_connected = mt5_connected and telegram_connected and account_ok
        
        if not all_connected:
            # Clean up partial connections
            if telegram_connected:
                try:
                    await telegram_listener.stop()
                except:
                    pass
            if mt5_connected:
                try:
                    await broker_client.disconnect()
                except:
                    pass
            
            bot_state.is_connected_mt5 = False
            bot_state.is_connected_telegram = False
            
            error_summary = "; ".join(connection_errors)
            logger.error(f"Bot startup failed - not all connections succeeded: {error_summary}")
            
            await broadcast_to_clients({
                "type": "startup_failed",
                "data": {
                    "message": "Not all connections succeeded. Please retry.",
                    "errors": connection_errors,
                    "mt5_connected": mt5_connected,
                    "telegram_connected": telegram_connected,
                    "account_ok": account_ok
                }
            })
            
            return {
                "status": "failed",
                "message": "Not all connections succeeded",
                "errors": connection_errors,
                "mt5_connected": mt5_connected,
                "telegram_connected": telegram_connected,
                "account_ok": account_ok
            }
        
        # All connections successful - start the bot
        logger.info("All connections successful, starting bot components...")
        
        # Start core components
        await risk_manager.start()
        await trade_manager.start()
        
        # Setup notifier
        notifier.set_telegram_client(telegram_listener.client)
        trade_manager.add_trade_listener(notifier.handle_trade_event)
        
        # Setup signal handler
        async def handle_signal_wrapper(signal: Signal):
            # Get market data for context
            bid, ask = await broker_client.get_current_price(signal.symbol)
            spread_ok, spread = await broker_client.check_spread(signal.symbol)
            current_price = None
            if bid and ask:
                current_price = bid if signal.direction == TradeDirection.SELL else ask
            
            # Calculate price difference from entry zone
            price_diff_pips = None
            in_entry_zone = False
            if current_price and signal.entry_min and signal.entry_max:
                entry_mid = (signal.entry_min + signal.entry_max) / 2
                price_diff = current_price - entry_mid
                # Convert to pips (assuming 5-digit broker)
                if 'JPY' in signal.symbol:
                    price_diff_pips = price_diff / 0.01
                else:
                    price_diff_pips = price_diff / 0.0001
                # Check if in zone (with tolerance)
                tolerance = config.trading.entry_zone_tolerance * 0.0001
                in_entry_zone = (signal.entry_min - tolerance) <= current_price <= (signal.entry_max + tolerance)
            
            # Send signal received with market context
            await broadcast_to_clients({
                "type": "signal_received",
                "data": {
                    **signal.to_dict(),
                    "market_context": {
                        "current_price": current_price,
                        "bid": bid,
                        "ask": ask,
                        "spread_pips": round(spread, 2) if spread else None,
                        "spread_ok": spread_ok,
                        "price_diff_pips": round(price_diff_pips, 1) if price_diff_pips else None,
                        "in_entry_zone": in_entry_zone,
                        "execute_immediately": config.trading.execute_immediately
                    }
                }
            })
            
            # Process signal through risk manager
            can_trade, reason = await risk_manager.can_trade(signal)
            
            if not can_trade:
                # Create a rejected trade record for tracking
                from models.trade import Trade, TradeStatus
                rejected_trade = Trade.from_signal(signal, config.trading.default_lot_size)
                rejected_trade.status = TradeStatus.REJECTED
                rejected_trade.rejection_reason = reason
                rejected_trade.market_price_at_signal = current_price
                rejected_trade.spread_at_signal = spread
                rejected_trade.notes.append(f"Rejected: {reason}")
                if price_diff_pips:
                    rejected_trade.notes.append(f"Price was {abs(price_diff_pips):.1f} pips {'above' if price_diff_pips > 0 else 'below'} entry zone")
                
                # Store in trade manager for history
                trade_manager.trades[rejected_trade.id] = rejected_trade
                await trade_manager._save_trades()
                
                await broadcast_to_clients({
                    "type": "signal_rejected",
                    "data": {
                        "signal_id": signal.id,
                        "trade_id": rejected_trade.id,
                        "reason": reason,
                        "trade": rejected_trade.to_dict(),
                        "market_context": {
                            "current_price": current_price,
                            "spread_pips": round(spread, 2) if spread else None,
                            "price_diff_pips": round(price_diff_pips, 1) if price_diff_pips else None,
                            "in_entry_zone": in_entry_zone
                        }
                    }
                })
                return
            
            # Process signal through trade manager
            trade = await trade_manager.process_signal(signal)
            if trade:
                # Add market context to trade
                trade.market_price_at_signal = current_price
                trade.spread_at_signal = spread
                
                # Sync to Firebase
                firebase_service.add_trade(trade.id, trade.to_dict())
                firebase_service.add_activity({
                    "type": "trade_opened",
                    "title": f"Trade Opened - {trade.symbol}",
                    "symbol": trade.symbol,
                    "direction": trade.direction.value if hasattr(trade.direction, 'value') else str(trade.direction)
                })
                
                await broadcast_to_clients({
                    "type": "trade_created",
                    "data": {
                        "trade": trade.to_dict(),
                        "market_context": {
                            "current_price": current_price,
                            "spread_pips": round(spread, 2) if spread else None,
                            "price_diff_pips": round(price_diff_pips, 1) if price_diff_pips else None,
                            "in_entry_zone": in_entry_zone
                        }
                    }
                })
        
        telegram_listener.on_signal(handle_signal_wrapper)
        
        # Start listener in background
        asyncio.create_task(telegram_listener.run_forever())
        
        bot_state.is_running = True
        bot_state.start_time = datetime.utcnow()
        
        # Start real-time update task
        global _realtime_task, _health_check_task
        if _realtime_task is None or _realtime_task.done():
            _realtime_task = asyncio.create_task(realtime_update_task())
            logger.info("Real-time update task started")
        
        # Start health check task for 24/7 operation
        if _health_check_task is None or _health_check_task.done():
            _health_check_task = asyncio.create_task(health_check_task())
            logger.info("Health check task started for 24/7 operation")
        
        await broadcast_to_clients({
            "type": "bot_started",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "mt5_connected": bot_state.is_connected_mt5,
                "telegram_connected": bot_state.is_connected_telegram
            }
        })
        
        # Log final connection status
        logger.info(f"Bot started successfully - MT5: {bot_state.is_connected_mt5}, Telegram: {bot_state.is_connected_telegram}")
        
        return {
            "status": "success", 
            "message": "Bot started successfully",
            "mt5_connected": bot_state.is_connected_mt5,
            "telegram_connected": bot_state.is_connected_telegram
        }
    
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        # Clean up on error
        try:
            await telegram_listener.stop()
        except:
            pass
        try:
            await broker_client.disconnect()
        except:
            pass
        bot_state.is_connected_mt5 = False
        bot_state.is_connected_telegram = False
        
        await broadcast_to_clients({
            "type": "startup_failed",
            "data": {"step": "error", "status": "error", "message": str(e)[:100]}
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/reconnect")
async def reconnect_services():
    """Attempt to reconnect failed services (MT5, Telegram)"""
    if not bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    results = {"mt5": None, "telegram": None}
    
    try:
        # Try to reconnect MT5 if disconnected
        if not bot_state.is_connected_mt5:
            logger.info("Attempting MT5 reconnection...")
            await broadcast_to_clients({
                "type": "reconnect_progress",
                "data": {"service": "mt5", "status": "connecting"}
            })
            try:
                connected = await asyncio.wait_for(broker_client.connect(), timeout=30)
                bot_state.is_connected_mt5 = connected
                results["mt5"] = "connected" if connected else "failed"
                await broadcast_to_clients({
                    "type": "reconnect_progress",
                    "data": {"service": "mt5", "status": "success" if connected else "failed"}
                })
                if connected:
                    logger.info("MT5 reconnected successfully")
            except asyncio.TimeoutError:
                results["mt5"] = "timeout"
                await broadcast_to_clients({
                    "type": "reconnect_progress",
                    "data": {"service": "mt5", "status": "timeout"}
                })
                logger.warning("MT5 reconnection timed out")
            except Exception as e:
                results["mt5"] = f"error: {str(e)[:50]}"
                await broadcast_to_clients({
                    "type": "reconnect_progress",
                    "data": {"service": "mt5", "status": "error", "message": str(e)[:50]}
                })
                logger.error(f"MT5 reconnection error: {e}")
        else:
            results["mt5"] = "already_connected"
        
        # Try to reconnect Telegram if disconnected
        if not bot_state.is_connected_telegram:
            logger.info("Attempting Telegram reconnection...")
            await broadcast_to_clients({
                "type": "reconnect_progress",
                "data": {"service": "telegram", "status": "connecting"}
            })
            try:
                await asyncio.wait_for(telegram_listener.start(), timeout=30)
                bot_state.is_connected_telegram = True
                results["telegram"] = "connected"
                await broadcast_to_clients({
                    "type": "reconnect_progress",
                    "data": {"service": "telegram", "status": "success"}
                })
                # Restart the listener loop
                asyncio.create_task(telegram_listener.run_forever())
                logger.info("Telegram reconnected successfully")
            except asyncio.TimeoutError:
                results["telegram"] = "timeout"
                await broadcast_to_clients({
                    "type": "reconnect_progress",
                    "data": {"service": "telegram", "status": "timeout"}
                })
                logger.warning("Telegram reconnection timed out")
            except Exception as e:
                results["telegram"] = f"error: {str(e)[:50]}"
                await broadcast_to_clients({
                    "type": "reconnect_progress",
                    "data": {"service": "telegram", "status": "error", "message": str(e)[:50]}
                })
                logger.error(f"Telegram reconnection error: {e}")
        else:
            results["telegram"] = "already_connected"
        
        return {
            "status": "completed",
            "results": results,
            "mt5_connected": bot_state.is_connected_mt5,
            "telegram_connected": bot_state.is_connected_telegram
        }
    
    except Exception as e:
        logger.error(f"Reconnect failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    if not bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    try:
        logger.info("Stopping bot...")
        
        await trade_manager.stop()
        await risk_manager.stop()
        await telegram_listener.stop()
        
        # Always try to disconnect broker, regardless of state
        try:
            await broker_client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting broker: {e}")
        
        bot_state.is_running = False
        bot_state.is_connected_telegram = False
        bot_state.is_connected_mt5 = False
        
        # Give time for all resources to be released
        await asyncio.sleep(1)
        
        await broadcast_to_clients({
            "type": "bot_stopped",
            "data": {"timestamp": datetime.utcnow().isoformat()}
        })
        
        logger.info("Bot stopped successfully")
        return {"status": "success", "message": "Bot stopped successfully"}
    
    except Exception as e:
        logger.error(f"Failed to stop bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
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

@app.get("/api/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get specific trade details"""
    trade = trade_manager.get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade.to_dict()

@app.post("/api/trades/{trade_id}/close")
async def close_trade(trade_id: str):
    """Close a specific trade"""
    trade = trade_manager.get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.position_ticket:
        success, msg = await broker_client.close_position(trade.position_ticket)
        if success:
            trade.status = "closed"
            trade.closed_at = datetime.utcnow()
            return {"status": "success", "message": "Trade closed"}
        else:
            raise HTTPException(status_code=500, detail=msg)
    else:
        raise HTTPException(status_code=400, detail="No position to close")

@app.post("/api/signal/test")
async def test_signal(request: SignalTestRequest):
    """Test signal parsing"""
    signal = signal_parser.parse(request.message)
    return {
        "parsed": signal.to_dict(),
        "success": signal.parsed_successfully,
        "errors": signal.parse_errors
    }

@app.post("/api/config/update")
async def update_config(updates: ConfigUpdate):
    """Update bot configuration"""
    if updates.default_lot_size is not None:
        config.trading.default_lot_size = updates.default_lot_size
    if updates.max_spread_pips is not None:
        config.trading.max_spread_pips = updates.max_spread_pips
    if updates.max_daily_drawdown is not None:
        config.trading.max_daily_drawdown_percent = updates.max_daily_drawdown
    if updates.max_open_trades is not None:
        config.trading.max_open_trades = updates.max_open_trades
    if updates.symbol_max_spreads is not None:
        config.trading.symbol_max_spreads = updates.symbol_max_spreads
    
    config.save()
    return {"status": "success", "message": "Configuration updated"}

# =====================================================
# SETTINGS API - All settings stored in Firebase
# =====================================================

@app.get("/api/settings")
async def get_all_settings():
    """Get all settings from Firebase (public read, masked sensitive data)"""
    from core.firebase_settings import firebase_settings
    settings = firebase_settings.get_all()
    
    # Mask sensitive data for public access
    if 'telegram' in settings:
        if settings['telegram'].get('api_hash'):
            settings['telegram']['api_hash'] = '***masked***'
    if 'broker' in settings:
        if settings['broker'].get('metaapi_token'):
            settings['broker']['metaapi_token'] = '***masked***'
        if settings['broker'].get('password'):
            settings['broker']['password'] = '***masked***'
    
    return settings

@app.get("/api/settings/{section}")
async def get_settings_section(section: str):
    """Get settings for a specific section (public read, masked sensitive)"""
    from core.firebase_settings import firebase_settings
    settings = firebase_settings.get_section(section)
    
    # Mask sensitive data
    if section == 'telegram' and settings.get('api_hash'):
        settings['api_hash'] = '***masked***'
    if section == 'broker':
        if settings.get('metaapi_token'):
            settings['metaapi_token'] = '***masked***'
        if settings.get('password'):
            settings['password'] = '***masked***'
    
    return {
        "section": section,
        "settings": settings,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.put("/api/settings")
async def update_all_settings(settings: Dict[str, Any]):
    """Update all settings at once"""
    from core.firebase_settings import firebase_settings
    firebase_settings.update_all(settings)
    
    security_manager.audit_log(
        "settings_updated",
        "dashboard",
        details={"sections": list(settings.keys())},
        severity="info"
    )
    
    return {"status": "success", "message": "All settings updated"}

@app.put("/api/settings/{section}")
async def update_settings_section(section: str, values: Dict[str, Any]):
    """Update settings for a specific section"""
    from core.firebase_settings import firebase_settings
    firebase_settings.set_section(section, values)
    
    security_manager.audit_log(
        "settings_updated",
        "dashboard",
        details={"section": section},
        severity="info"
    )
    
    return {"status": "success", "message": f"Settings for {section} updated"}

@app.put("/api/settings/{section}/{key}")
async def update_single_setting(section: str, key: str, request: Request):
    """Update a single setting value"""
    from core.firebase_settings import firebase_settings
    body = await request.json()
    value = body.get("value")
    
    firebase_settings.set(section, key, value)
    
    security_manager.audit_log(
        "setting_updated",
        "dashboard",
        details={"section": section, "key": key},
        severity="info"
    )
    
    return {"status": "success", "message": f"Setting {section}.{key} updated"}

@app.post("/api/settings/telegram/channels")
async def update_telegram_channels(request: Request):
    """Update Telegram signal channels"""
    from core.firebase_settings import firebase_settings
    body = await request.json()
    signal_channels = body.get("signal_channels", [])
    notification_channel = body.get("notification_channel", "")
    
    firebase_settings.set("telegram", "signal_channels", signal_channels)
    firebase_settings.set("telegram", "notification_channel", notification_channel)
    
    security_manager.audit_log(
        "telegram_channels_updated",
        "dashboard",
        details={"signal_channels": signal_channels, "notification_channel": notification_channel},
        severity="info"
    )
    
    return {"status": "success", "message": "Telegram channels updated"}

@app.post("/api/settings/telegram/credentials")
async def update_telegram_credentials(request: Request):
    """Update Telegram API credentials"""
    from core.firebase_settings import firebase_settings
    body = await request.json()
    
    if "api_id" in body:
        firebase_settings.set("telegram", "api_id", int(body["api_id"]))
    if "api_hash" in body:
        firebase_settings.set("telegram", "api_hash", body["api_hash"])
    if "phone_number" in body:
        firebase_settings.set("telegram", "phone_number", body["phone_number"])
    
    security_manager.audit_log(
        "telegram_credentials_updated",
        "dashboard",
        severity="warning"
    )
    
    return {"status": "success", "message": "Telegram credentials updated. Restart required."}

@app.post("/api/settings/broker/credentials")
async def update_broker_credentials(request: Request):
    """Update MetaApi/MT5 broker credentials"""
    from core.firebase_settings import firebase_settings
    body = await request.json()
    
    if "metaapi_token" in body:
        firebase_settings.set("broker", "metaapi_token", body["metaapi_token"])
    if "metaapi_account_id" in body:
        firebase_settings.set("broker", "metaapi_account_id", body["metaapi_account_id"])
    if "server" in body:
        firebase_settings.set("broker", "server", body["server"])
    if "login" in body:
        firebase_settings.set("broker", "login", int(body["login"]))
    if "password" in body:
        firebase_settings.set("broker", "password", body["password"])
    
    security_manager.audit_log(
        "broker_credentials_updated",
        "dashboard",
        severity="warning"
    )
    
    return {"status": "success", "message": "Broker credentials updated. Restart required."}

@app.post("/api/settings/reload")
async def reload_settings():
    """Reload settings from Firebase"""
    from core.firebase_settings import firebase_settings
    firebase_settings.reload_from_firebase()
    config.reload()
    
    return {"status": "success", "message": "Settings reloaded from Firebase"}

# =====================================================
# Connection Test Endpoints
# =====================================================

@app.post("/api/test/telegram")
async def test_telegram_connection(request: Request):
    """Test Telegram connection with provided credentials"""
    body = await request.json()
    api_id = body.get("api_id")
    api_hash = body.get("api_hash")
    phone_number = body.get("phone_number")
    
    if not api_id or not api_hash or not phone_number:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Missing required credentials (api_id, api_hash, phone_number)"}
        )
    
    try:
        # Check if credentials look valid (basic validation)
        api_id_int = int(api_id) if isinstance(api_id, str) else api_id
        if api_id_int <= 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid API ID"}
            )
        
        if len(str(api_hash)) < 10:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid API Hash (too short)"}
            )
        
        if not phone_number.startswith('+'):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Phone number must start with + and country code"}
            )
        
        # If we get here, credentials format looks valid
        # Full connection test would require actually connecting which needs session
        return {
            "success": True,
            "message": "Credentials format valid. Full connection test requires bot restart."
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Invalid credentials format: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Telegram test error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Test failed: {str(e)}"}
        )

@app.post("/api/test/broker")
async def test_broker_connection(request: Request):
    """Test MetaApi broker connection with provided credentials"""
    body = await request.json()
    metaapi_token = body.get("metaapi_token")
    metaapi_account_id = body.get("metaapi_account_id")
    
    if not metaapi_token or not metaapi_account_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Missing required credentials (metaapi_token, metaapi_account_id)"}
        )
    
    try:
        # Basic validation
        if len(str(metaapi_token)) < 20:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid MetaApi token (too short)"}
            )
        
        if len(str(metaapi_account_id)) < 10:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid MetaApi Account ID (too short)"}
            )
        
        # Try to actually test the connection if we have the metaapi SDK
        try:
            from metaapi_cloud_sdk import MetaApi
            
            # Create a temporary MetaApi instance to test
            api = MetaApi(metaapi_token)
            account = await api.metatrader_account_api.get_account(metaapi_account_id)
            
            if account:
                account_info = {
                    "name": account.name if hasattr(account, 'name') else 'Unknown',
                    "type": account.type if hasattr(account, 'type') else 'Unknown',
                    "state": account.state if hasattr(account, 'state') else 'Unknown',
                    "connection_status": account.connection_status if hasattr(account, 'connection_status') else 'Unknown'
                }
                return {
                    "success": True,
                    "message": f"Connected! Account: {account_info['name']}, State: {account_info['state']}",
                    "account": account_info
                }
            else:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Account not found"}
                )
                
        except ImportError:
            # MetaApi SDK not available, just validate format
            return {
                "success": True,
                "message": "Credentials format valid. Full connection test requires MetaApi SDK."
            }
        except Exception as e:
            error_msg = str(e)
            if "unauthorized" in error_msg.lower() or "401" in error_msg:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "message": "Invalid MetaApi token - unauthorized"}
                )
            elif "not found" in error_msg.lower() or "404" in error_msg:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "Account ID not found"}
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"Connection test failed: {error_msg}"}
                )
        
    except Exception as e:
        logger.error(f"Broker test error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Test failed: {str(e)}"}
        )

# =====================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    bot_state.websocket_clients.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in bot_state.websocket_clients:
            bot_state.websocket_clients.remove(websocket)

# Background task for real-time updates
async def realtime_update_task():
    """Background task to push real-time updates to WebSocket clients"""
    logger.info("Starting real-time update task...")
    while True:
        try:
            if bot_state.is_running and bot_state.websocket_clients:
                # Get fresh data with force_refresh
                if bot_state.is_connected_mt5:
                    # Force refresh to get real-time data
                    account_info = await broker_client.get_account_info(force_refresh=True)
                    positions = await broker_client.get_positions(force_refresh=True)
                    
                    if account_info:
                        await broadcast_to_clients({
                            "type": "account_update",
                            "data": account_info.to_dict()
                        })
                    
                    if positions is not None:
                        formatted_positions = []
                        for pos in positions:
                            formatted_positions.append({
                                "id": str(pos.get("id", "")),
                                "position_ticket": pos.get("id"),
                                "symbol": pos.get("symbol", ""),
                                "direction": "BUY" if pos.get("type") == "POSITION_TYPE_BUY" else "SELL",
                                "lot_size": pos.get("volume", 0),
                                "entry_price": pos.get("openPrice", 0),
                                "current_price": pos.get("currentPrice", 0),
                                "stop_loss": pos.get("stopLoss", 0),
                                "take_profit_1": pos.get("takeProfit", 0),
                                "profit": pos.get("profit", 0) + pos.get("swap", 0) + pos.get("commission", 0),
                                "swap": pos.get("swap", 0),
                                "commission": pos.get("commission", 0),
                                "open_time": pos.get("time", ""),
                            })
                        await broadcast_to_clients({
                            "type": "positions_update",
                            "data": {"positions": formatted_positions, "count": len(formatted_positions)}
                        })
            
            await asyncio.sleep(1)  # Update every 1 second
        except Exception as e:
            logger.error(f"Real-time update error: {e}")
            await asyncio.sleep(5)  # Wait longer on error

# Start real-time update task when bot starts
_realtime_task = None
_health_check_task = None

# Health check task to ensure connections stay alive
async def health_check_task():
    """Background task to monitor and maintain connections for 24/7 operation"""
    logger.info("Starting health check task for 24/7 operation...")
    check_interval = 60  # Check every 60 seconds
    
    while True:
        try:
            await asyncio.sleep(check_interval)
            
            if not bot_state.is_running:
                continue
            
            # Check Telegram connection
            if bot_state.is_connected_telegram:
                if telegram_listener.client and not telegram_listener.client.is_connected():
                    logger.warning("Health check: Telegram disconnected, triggering reconnect...")
                    bot_state.is_connected_telegram = False
                    # The run_forever loop should handle reconnection
                    
            # Check MT5 connection
            if bot_state.is_connected_mt5:
                try:
                    # Simple check - try to get account info
                    account = await broker_client.get_account_info(force_refresh=True)
                    if not account:
                        logger.warning("Health check: MT5 returned no account info")
                except Exception as e:
                    logger.warning(f"Health check: MT5 connection issue: {e}")
                    # Try to reconnect
                    try:
                        await broker_client.disconnect()
                        connected = await broker_client.connect()
                        bot_state.is_connected_mt5 = connected
                        if connected:
                            logger.info("Health check: MT5 reconnected successfully")
                    except Exception as re:
                        logger.error(f"Health check: MT5 reconnect failed: {re}")
            
            # Log status periodically
            uptime = (datetime.utcnow() - bot_state.start_time).total_seconds() if bot_state.start_time else 0
            days = int(uptime // 86400)
            hours = int((uptime % 86400) // 3600)
            minutes = int((uptime % 3600) // 60)
            
            uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"
            logger.info(f"Health check OK - Uptime: {uptime_str}, Telegram: {bot_state.is_connected_telegram}, MT5: {bot_state.is_connected_mt5}")
            
            # Periodic garbage collection to prevent memory buildup (every 10 minutes)
            if int(uptime) % 600 < check_interval:
                gc.collect()
                logger.debug("Periodic garbage collection completed")
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            await asyncio.sleep(30)

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    log_file = "logs/system.log"
    if not os.path.exists(log_file):
        return {"logs": []}
    
    with open(log_file, 'r') as f:
        all_lines = f.readlines()
        recent_lines = all_lines[-lines:]
    
    return {"logs": [line.strip() for line in recent_lines]}

# Channel cache file path
CHANNELS_CACHE_FILE = "data/channels_cache.json"
SETTINGS_CACHE_FILE = "data/settings_cache.json"

def get_settings_with_fallback():
    """Load settings from cache file"""
    try:
        if os.path.exists(SETTINGS_CACHE_FILE):
            with open(SETTINGS_CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading settings cache: {e}")
    return {}

def load_cached_channels():
    """Load cached channel info from local file"""
    try:
        if os.path.exists(CHANNELS_CACHE_FILE):
            with open(CHANNELS_CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading channels cache: {e}")
    return {"channels": [], "timestamp": None}

def save_channels_cache(channels_info):
    """Save channel info to local cache file"""
    try:
        os.makedirs(os.path.dirname(CHANNELS_CACHE_FILE), exist_ok=True)
        with open(CHANNELS_CACHE_FILE, 'w') as f:
            json.dump({
                "channels": channels_info,
                "timestamp": datetime.utcnow().isoformat()
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving channels cache: {e}")

async def fetch_channels_from_telegram():
    """Fetch channel info directly from Telegram using existing session"""
    from telethon import TelegramClient
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Load settings
        settings = get_settings_with_fallback()
        api_id = settings.get('telegram', {}).get('api_id')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        signal_channels = settings.get('telegram', {}).get('signal_channels', [])
        
        if not api_id or not api_hash or not signal_channels:
            return None
        
        session_path = 'evobot_session'
        if not os.path.exists(f'{session_path}.session'):
            return None
        
        client = TelegramClient(session_path, api_id, api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
        
        channels_data = []
        for channel_id in signal_channels:
            try:
                cid = int(str(channel_id))
                entity = await client.get_entity(cid)
                
                # Download profile photo
                photo_path = None
                if hasattr(entity, 'photo') and entity.photo:
                    os.makedirs('data/channel_photos', exist_ok=True)
                    photo_file = f'data/channel_photos/{entity.id}.jpg'
                    await client.download_profile_photo(entity, file=photo_file)
                    if os.path.exists(photo_file):
                        photo_path = photo_file
                
                channel_info = {
                    "id": entity.id,
                    "title": entity.title,
                    "username": getattr(entity, 'username', None),
                    "type": "channel",
                    "photo_path": photo_path,
                    "participants_count": getattr(entity, 'participants_count', None),
                    "verified": getattr(entity, 'verified', False),
                    "scam": getattr(entity, 'scam', False)
                }
                channels_data.append(channel_info)
            except Exception as e:
                logger.error(f"Error fetching channel {channel_id}: {e}")
        
        await client.disconnect()
        return channels_data
    except Exception as e:
        logger.error(f"Error in fetch_channels_from_telegram: {e}")
        return None

def is_cache_fresh(cache_data, max_age_seconds=300):
    """Check if cache is fresh (default 5 minutes)"""
    if not cache_data or not cache_data.get("timestamp"):
        return False
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"].replace('Z', '+00:00'))
        age = (datetime.utcnow() - cache_time.replace(tzinfo=None)).total_seconds()
        return age < max_age_seconds
    except:
        return False

@app.get("/api/telegram/channels")
async def get_telegram_channels(refresh: bool = False):
    """Get info about monitored Telegram channels including profile images"""
    # Check cached data first
    cached = load_cached_channels()
    
    # If cache is fresh and not forcing refresh, return cached data
    if not refresh and cached.get("channels") and is_cache_fresh(cached):
        return {
            "channels": cached["channels"],
            "count": len(cached["channels"]),
            "timestamp": cached.get("timestamp"),
            "source": "cache"
        }
    
    # If Telegram bot is connected, use it
    if bot_state.is_connected_telegram:
        try:
            channels_info = await telegram_listener.get_all_monitored_channels_info()
            save_channels_cache(channels_info)
            firebase_service.update_channels_info(channels_info)
            return {
                "channels": channels_info,
                "count": len(channels_info),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "live"
            }
        except Exception as e:
            logger.error(f"Error fetching channel info from bot: {e}")
    
    # Try to fetch directly from Telegram using existing session
    try:
        channels_data = await fetch_channels_from_telegram()
        if channels_data:
            save_channels_cache(channels_data)
            return {
                "channels": channels_data,
                "count": len(channels_data),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "telegram"
            }
    except Exception as e:
        logger.error(f"Error fetching from Telegram: {e}")
    
    # Fallback to cached data (even if stale)
    if cached.get("channels"):
        return {
            "channels": cached["channels"],
            "count": len(cached["channels"]),
            "timestamp": cached.get("timestamp"),
            "source": "cache"
        }
    
    return {"channels": [], "error": "Unable to fetch channels"}

@app.get("/api/telegram/channel/{channel_ref}/photo")
async def get_channel_photo(channel_ref: str):
    """Get channel profile photo"""
    from fastapi.responses import FileResponse
    
    photo_path = f"data/channel_photos/{channel_ref}.jpg"
    if os.path.exists(photo_path):
        return FileResponse(photo_path, media_type="image/jpeg")
    else:
        # Return a default avatar
        return JSONResponse(
            status_code=404,
            content={"error": "Photo not found"}
        )

# Cache for telegram user info
TELEGRAM_USER_CACHE_FILE = "data/telegram_user_cache.json"

def load_telegram_user_cache():
    """Load cached telegram user info"""
    try:
        if os.path.exists(TELEGRAM_USER_CACHE_FILE):
            with open(TELEGRAM_USER_CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading telegram user cache: {e}")
    return {}

def save_telegram_user_cache(user_info):
    """Save telegram user info to cache"""
    try:
        os.makedirs('data', exist_ok=True)
        with open(TELEGRAM_USER_CACHE_FILE, 'w') as f:
            json.dump(user_info, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving telegram user cache: {e}")

@app.get("/api/telegram/user")
async def get_telegram_user():
    """Get logged in Telegram user info"""
    from telethon import TelegramClient
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check cache first
    cached = load_telegram_user_cache()
    if cached.get("user") and is_cache_fresh(cached, max_age_seconds=3600):  # 1 hour cache
        return cached
    
    try:
        settings = get_settings_with_fallback()
        api_id = settings.get('telegram', {}).get('api_id')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return {"error": "Telegram not configured"}
        
        session_path = 'evobot_session'
        if not os.path.exists(f'{session_path}.session'):
            return {"error": "No Telegram session"}
        
        client = TelegramClient(session_path, api_id, api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return {"error": "Not authorized"}
        
        me = await client.get_me()
        
        # Download profile photo
        photo_path = None
        if me.photo:
            os.makedirs('data/user_photos', exist_ok=True)
            photo_file = f'data/user_photos/{me.id}.jpg'
            await client.download_profile_photo(me, file=photo_file)
            if os.path.exists(photo_file):
                photo_path = photo_file
        
        user_info = {
            "user": {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone,
                "photo_path": photo_path,
                "premium": getattr(me, 'premium', False)
            },
            "api_id": api_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await client.disconnect()
        save_telegram_user_cache(user_info)
        
        return user_info
    except Exception as e:
        logger.error(f"Error getting telegram user: {e}")
        # Return cached data if available
        if cached.get("user"):
            return cached
        return {"error": str(e)}

@app.get("/api/telegram/user/photo")
async def get_telegram_user_photo():
    """Get logged in user's profile photo"""
    from fastapi.responses import FileResponse
    
    cached = load_telegram_user_cache()
    if cached.get("user", {}).get("photo_path"):
        photo_path = cached["user"]["photo_path"]
        if os.path.exists(photo_path):
            return FileResponse(photo_path, media_type="image/jpeg")
    
    return JSONResponse(status_code=404, content={"error": "Photo not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
