import asyncio
import logging
import subprocess
import gc
import sys
import platform
from datetime import datetime
from fastapi import HTTPException

from dashboard.state import bot_state, broadcast_to_clients
from core.trade_manager import trade_manager
from core.risk_manager import risk_manager
from core.notifier import notifier
from broker import broker_client
from telegram.listener import telegram_listener
from config.settings import config
from models.trade import Signal, Trade, TradeDirection, TradeStatus
from core.firebase_service import firebase_service
from core.realtime_sync import realtime_sync

logger = logging.getLogger("evobot.dashboard.lifecycle")

# Global tasks
_health_check_task = None

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

async def health_check_task():
    """Background task to monitor and maintain connections for 24/7 operation"""
    logger.info("Starting health check task for 24/7 operation...")
    check_interval = 120  # Check every 2 minutes (reduced overhead)
    
    while True:
        try:
            await asyncio.sleep(check_interval)
            
            if not bot_state.is_running:
                continue
            
            # Check Telegram connection - handled by listener mostly but we check status
            if bot_state.is_connected_telegram:
                if telegram_listener.client and not telegram_listener.client.is_connected():
                    logger.warning("Health check: Telegram disconnected, triggering reconnect...")
                    bot_state.is_connected_telegram = False
                    
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
            
            # Periodic garbage collection to prevent memory buildup (every 10 minutes)
            if int(uptime) % 600 < check_interval:
                gc.collect()
                logger.debug("Periodic garbage collection completed")
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            await asyncio.sleep(30)

async def start_bot():
    """Start the trading bot - requires all connections to succeed"""
    if bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    # Kill any existing main.py processes (Windows-compatible)
    try:
        if platform.system() == 'Windows':
            # Windows: Use tasklist and taskkill
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, shell=True
            )
            if result.returncode == 0 and result.stdout:
                # Parse CSV output and kill processes running main.py
                for line in result.stdout.strip().split('\n'):
                    if 'python' in line.lower():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            # Check if it's running main.py
                            try:
                                cmd_result = subprocess.run(
                                    ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'CommandLine', '/FORMAT:LIST'],
                                    capture_output=True, text=True, shell=True, timeout=2
                                )
                                if 'main.py' in cmd_result.stdout:
                                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, shell=True)
                                    logger.info(f"Killed existing main.py process: {pid}")
                            except:
                                pass
        else:
            # Unix/Linux: Use pgrep and kill
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
        await asyncio.sleep(1)
    except Exception as e:
        logger.warning(f"Could not kill existing processes: {e}")
    
    connection_errors = []
    
    try:
        # Broadcast progress: MT5 connecting
        await broadcast_to_clients({
            "type": "startup_progress",
            "data": {"step": "mt5", "status": "loading"}
        })
        
        # Connect to MT5
        logger.info("Connecting to MT5...")
        mt5_connected = False
        mt5_error = None
        try:
            # Pass user_id if available
            user_id = bot_state.current_user_id if hasattr(bot_state, 'current_user_id') else None
            logger.info(f"Starting MT5 connection with user_id: {user_id}")
            
            # Try to get stored MT5 credentials first
            mt5_creds = None
            if user_id:
                from core.mt5_credentials import mt5_store
                mt5_creds = mt5_store.get(user_id)
                logger.info(f"Retrieved MT5 credentials from store: {mt5_creds is not None}")
                
                if not mt5_creds and firebase_service.db_ref:
                    logger.info("Trying to get MT5 credentials from Firebase...")
                    try:
                        fb_creds = firebase_service.db_ref.child(f"users/{user_id}/mt5_credentials").get()
                        if fb_creds:
                            mt5_store.set(user_id, fb_creds["server"], fb_creds["login"], fb_creds["password"])
                            mt5_creds = fb_creds
                            logger.info("Retrieved MT5 credentials from Firebase")
                    except Exception as fb_err:
                        logger.warning(f"Failed to get credentials from Firebase: {fb_err}")
                
                if mt5_creds:
                    logger.info(f"Using stored MT5 credentials: Server={mt5_creds['server']}, Login={mt5_creds['login']}")
            
            # Check if we have credentials (either from store or .env)
            has_creds = (mt5_creds is not None) or (config.broker.login and config.broker.password)
            if not has_creds:
                mt5_error = "No MT5 credentials configured. Please log in via the MT5 modal or configure .env file"
                logger.error(mt5_error)
            else:
                logger.info(f"Attempting MT5 connection...")
                mt5_connected = await asyncio.wait_for(broker_client.connect(user_id), timeout=30)
                logger.info(f"MT5 connection result: {mt5_connected}")
        except asyncio.TimeoutError:
            mt5_error = "Connection timeout (30s) - Ensure MT5 terminal is running and logged in"
            logger.warning(f"MT5: {mt5_error}")
        except Exception as mt5_err:
            error_msg = str(mt5_err)
            logger.error(f"MT5 connection exception: {error_msg}", exc_info=True)
            if "Authorization failed" in error_msg or "-6" in error_msg:
                mt5_error = "MT5 terminal is not logged in. Please open MT5 and log in to your account"
            elif "Terminal" in error_msg or "-2" in error_msg:
                mt5_error = "MT5 terminal not found. Please ensure MT5 is installed and running"
            elif "timeout" in error_msg.lower():
                mt5_error = "Connection timeout - Ensure MT5 terminal is running"
            else:
                mt5_error = error_msg[:150]
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
        
        # Start Telegram listener
        logger.info("Starting Telegram listener...")
        telegram_connected = False
        telegram_error = None
        try:
            await asyncio.wait_for(telegram_listener.start(), timeout=30)
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
            telegram_error = "Connection timed out after 30s"
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
        
        # Check account info
        await broadcast_to_clients({
            "type": "startup_progress",
            "data": {"step": "account", "status": "loading"}
        })
        
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
        
        await risk_manager.start()
        await trade_manager.start()
        
        notifier.set_telegram_client(telegram_listener.client)
        trade_manager.add_trade_listener(notifier.handle_trade_event)
        
        # Register signal handler
        telegram_listener.on_signal(handle_signal_wrapper)
        
        asyncio.create_task(telegram_listener.run_forever())
        
        bot_state.is_running = True
        bot_state.start_time = datetime.utcnow()
        
        # Initialize and start real-time sync service
        realtime_sync.initialize(
            firebase_service=firebase_service,
            broker_client=broker_client,
            trade_manager=trade_manager,
            websocket_broadcast=broadcast_to_clients,
            bot_state=bot_state
        )
        await realtime_sync.start()
        
        # Start health check task
        global _health_check_task
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

async def stop_bot():
    """Stop the trading bot"""
    if not bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    try:
        logger.info("Stopping bot...")
        
        # Stop real-time sync
        await realtime_sync.stop()
        
        await trade_manager.stop()
        await risk_manager.stop()
        await telegram_listener.stop()
        
        try:
            await broker_client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting broker: {e}")
        
        bot_state.is_running = False
        bot_state.is_connected_telegram = False
        bot_state.is_connected_mt5 = False
        
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

async def reconnect_services():
    """Attempt to reconnect failed services (MT5, Telegram)"""
    if not bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    results = {"mt5": None, "telegram": None}
    
    try:
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
            except Exception as e:
                 results["mt5"] = f"error: {str(e)[:50]}"
        else:
            results["mt5"] = "already_connected"
            
        if not bot_state.is_connected_telegram:
             logger.info("Attempting Telegram reconnection...")
             try:
                await asyncio.wait_for(telegram_listener.start(), timeout=30)
                bot_state.is_connected_telegram = True
                results["telegram"] = "connected"
                # Restart the listener loop for telegram
                asyncio.create_task(telegram_listener.run_forever())
             except Exception as e:
                results["telegram"] = f"error: {str(e)[:50]}"
        else:
            results["telegram"] = "already_connected"
            
        return {
            "status": "completed",
            "results": results,
            "mt5_connected": bot_state.is_connected_mt5,
            "telegram_connected": bot_state.is_connected_telegram
        }
    except Exception as e:
        logger.error(f"Reconnect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def auto_start_bot():
    """Auto-start the bot after a short delay"""
    await asyncio.sleep(2)
    try:
        await start_bot()
        logger.info("Bot auto-started successfully")
    except Exception as e:
        logger.error(f"Failed to auto-start bot: {e}")
