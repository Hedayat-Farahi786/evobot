"""
Web Dashboard for EvoBot Trading System
FastAPI-based web interface for monitoring and controlling the bot
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
import os
import asyncio
import logging
import mimetypes

from config.settings import config
from core.firebase_service import firebase_service
from core.firebase_auth import firebase_auth_service, init_firebase_auth
from core.security import security_manager
from dashboard.state import bot_state
from dashboard.deps import get_client_ip
from dashboard.lifecycle import auto_start_bot
from core.realtime_sync import realtime_sync

# Import routers
from dashboard.routers import auth, telegram, admin, api, settings, views, channels, signals

logger = logging.getLogger("evobot.dashboard")

# Ensure proper MIME types
mimetypes.init()
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('image/webp', '.webp')

# Initialize Firebase Auth on module load
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
    if request.url.path.startswith("/static") or request.url.path.startswith("/assets"):
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

# Include routers
app.include_router(auth.router)
app.include_router(telegram.router)
app.include_router(admin.router)
app.include_router(api.router)
app.include_router(settings.router)
app.include_router(views.router)
app.include_router(channels.router)
app.include_router(signals.router)

# WebSocket endpoint (outside /api prefix)
from fastapi import WebSocket, WebSocketDisconnect
from uvicorn.protocols.utils import ClientDisconnected
from websockets.exceptions import ConnectionClosedOK

from core.websocket_manager import manager as ws_manager

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
            await websocket.send_json({
                "type": "status",
                "data": {
                    "bot_running": bot_state.is_running,
                    "telegram_connected": bot_state.is_connected_telegram,
                    "mt5_connected": bot_state.is_connected_mt5
                }
            })
    except (WebSocketDisconnect, ClientDisconnected, ConnectionClosedOK):
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error in /ws: {type(e).__name__}: {e}", exc_info=True)
        ws_manager.disconnect(websocket)

# Mount static files if directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount assets directory
assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Initialize on startup
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
    
    # Initialize realtime sync with WebSocket broadcast
    from broker import broker_client
    from core.trade_manager import trade_manager
    
    realtime_sync.initialize(
        firebase_service=firebase_service,
        broker_client=broker_client,
        trade_manager=trade_manager,
        websocket_broadcast=ws_manager.broadcast,
        bot_state=bot_state
    )
    logger.info("Realtime sync initialized")
    
    # Auto-start the bot if AUTO_START environment variable is set
    if os.getenv("AUTO_START_BOT", "false").lower() == "true":
        logger.info("AUTO_START_BOT enabled - starting bot automatically...")
        asyncio.create_task(auto_start_bot())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
