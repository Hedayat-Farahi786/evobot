"""Signal messages API router"""
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import os

try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Import signal storage singleton
try:
    from core.signal_storage import signal_storage
    SIGNAL_STORAGE_AVAILABLE = True
except ImportError:
    SIGNAL_STORAGE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signals", tags=["signals"])

# Firebase reference
_firebase_ref = None

def get_firebase_ref():
    """Get Firebase database reference for signals"""
    global _firebase_ref
    if _firebase_ref is None and FIREBASE_AVAILABLE:
        try:
            # Get the signal_messages child reference
            _firebase_ref = db.reference('signal_messages')
            logger.info("Firebase reference initialized for signals API")
        except Exception as e:
            logger.error(f"Failed to get Firebase reference: {e}")
    return _firebase_ref


@router.get("/messages")
async def get_signal_messages(
    limit: int = Query(100, ge=1, le=500),
    channel_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get recent signal messages with filtering"""
    try:
        messages = []
        
        # Try Firebase first
        firebase_ref = get_firebase_ref()
        if firebase_ref:
            signals_data = firebase_ref.get() or {}
            messages = list(signals_data.values()) if signals_data else []
            logger.info(f"Fetched {len(messages)} signal messages from Firebase")
        
        # Fallback to in-memory storage if Firebase is empty
        if not messages and SIGNAL_STORAGE_AVAILABLE:
            in_memory_messages = signal_storage.get_messages(limit=500)
            messages = [msg.to_dict() for msg in in_memory_messages]
            logger.info(f"Using {len(messages)} signal messages from in-memory storage")
        
        if not messages:
            logger.debug("No signal messages found in Firebase or memory")
        
        # Filter by channel
        if channel_id:
            messages = [m for m in messages if m.get("channel_id") == channel_id]
        
        # Filter by date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            messages = [m for m in messages if datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00')) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            messages = [m for m in messages if datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00')) <= end_dt]
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply limit
        messages = messages[:limit]
        
        logger.info(f"Returning {len(messages)} filtered signal messages")
        return {
            "success": True,
            "count": len(messages),
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error fetching signal messages: {e}", exc_info=True)
        return {
            "success": False,
            "count": 0,
            "messages": [],
            "error": str(e)
        }


@router.get("/channel/{channel_id}/analytics")
async def get_channel_analytics(channel_id: str):
    """Get analytics for a specific channel"""
    try:
        all_signals = []
        
        # Try Firebase first
        firebase_ref = get_firebase_ref()
        if firebase_ref:
            signals_data = firebase_ref.get() or {}
            all_signals = list(signals_data.values()) if signals_data else []
        
        # Fallback to in-memory storage
        if not all_signals and SIGNAL_STORAGE_AVAILABLE:
            in_memory_messages = signal_storage.get_messages(limit=500)
            all_signals = [msg.to_dict() for msg in in_memory_messages]
        
        channel_signals = [s for s in all_signals if s.get("channel_id") == channel_id]
        executed = [s for s in channel_signals if s.get("executed", False)]
        closed = [s for s in executed if s.get("status") in ["tp3_hit", "tp2_hit", "tp1_hit", "sl_hit", "closed"]]
        wins = [s for s in closed if s.get("total_profit", 0) > 0]
        
        total_profit = sum(s.get("total_profit", 0) for s in closed if s.get("total_profit") is not None)
        
        analytics = {
            "total_signals": len(channel_signals),
            "executed_signals": len(executed),
            "closed_signals": len(closed),
            "win_rate": (len(wins) / len(closed) * 100) if closed else 0,
            "total_profit": total_profit,
            "avg_profit": (total_profit / len(closed)) if closed else 0
        }
        
        return {
            "success": True,
            "channel_id": channel_id,
            "analytics": analytics
        }
    except Exception as e:
        logger.error(f"Error calculating channel analytics: {e}", exc_info=True)
        return {
            "success": False,
            "channel_id": channel_id,
            "analytics": {
                "total_signals": 0,
                "executed_signals": 0,
                "closed_signals": 0,
                "win_rate": 0,
                "total_profit": 0,
                "avg_profit": 0
            },
            "error": str(e)
        }


@router.get("/analytics")
async def get_all_analytics():
    """Get analytics for all channels"""
    try:
        firebase_ref = get_firebase_ref()
        
        if firebase_ref:
            signals_data = firebase_ref.get() or {}
            all_signals = list(signals_data.values()) if signals_data else []
        else:
            all_signals = []
        
        channels = set(s.get("channel_id") for s in all_signals if s.get("channel_id"))
        analytics = {}
        
        for channel_id in channels:
            channel_signals = [s for s in all_signals if s.get("channel_id") == channel_id]
            executed = [s for s in channel_signals if s.get("executed", False)]
            closed = [s for s in executed if s.get("status") in ["tp3_hit", "tp2_hit", "tp1_hit", "sl_hit", "closed"]]
            wins = [s for s in closed if s.get("total_profit", 0) > 0]
            
            total_profit = sum(s.get("total_profit", 0) for s in closed if s.get("total_profit") is not None)
            
            analytics[channel_id] = {
                "total_signals": len(channel_signals),
                "executed_signals": len(executed),
                "closed_signals": len(closed),
                "win_rate": (len(wins) / len(closed) * 100) if closed else 0,
                "total_profit": total_profit,
                "avg_profit": (total_profit / len(closed)) if closed else 0
            }
        
        return {
            "success": True,
            "channels": analytics
        }
    except Exception as e:
        logger.error(f"Error calculating all analytics: {e}")
        return {
            "success": False,
            "channels": {},
            "error": str(e)
        }


@router.post("/add")
async def add_signal_message(signal: dict):
    """Add a new signal message (called by the bot)"""
    try:
        # Add timestamp if not present
        if "timestamp" not in signal:
            signal["timestamp"] = datetime.now().isoformat()
        
        # Add unique ID if not present
        if "id" not in signal:
            signal["id"] = f"sig_{int(datetime.now().timestamp() * 1000)}"
        
        firebase_ref = get_firebase_ref()
        
        if firebase_ref:
            # Store in Firebase
            firebase_ref.child(signal["id"]).set(signal)
            logger.info(f"Signal {signal['id']} stored in Firebase")
        else:
            logger.warning("Firebase not available, signal not persisted")
        
        return {
            "success": True,
            "message": "Signal added successfully",
            "signal_id": signal["id"]
        }
    except Exception as e:
        logger.error(f"Error adding signal message: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.put("/update/{signal_id}")
async def update_signal_message(signal_id: str, updates: dict):
    """Update an existing signal message (called by the bot)"""
    try:
        firebase_ref = get_firebase_ref()
        
        if firebase_ref:
            signal_ref = firebase_ref.child(signal_id)
            existing = signal_ref.get()
            
            if existing:
                signal_ref.update(updates)
                logger.info(f"Signal {signal_id} updated in Firebase")
                return {
                    "success": True,
                    "message": "Signal updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Signal not found"
                }
        else:
            return {
                "success": False,
                "error": "Firebase not available"
            }
    except Exception as e:
        logger.error(f"Error updating signal message: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/clear")
async def clear_signal_messages():
    """Clear all signal messages"""
    try:
        firebase_ref = get_firebase_ref()
        
        if firebase_ref:
            firebase_ref.delete()
            logger.info("All signals cleared from Firebase")
        
        return {
            "success": True,
            "message": "All signals cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing signals: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/debug/status")
async def get_debug_status():
    """Debug endpoint to check signal storage status"""
    try:
        status = {
            "firebase_available": FIREBASE_AVAILABLE,
            "signal_storage_available": SIGNAL_STORAGE_AVAILABLE,
            "firebase_connected": False,
            "firebase_signal_count": 0,
            "memory_signal_count": 0
        }
        
        # Check Firebase
        firebase_ref = get_firebase_ref()
        if firebase_ref:
            status["firebase_connected"] = True
            signals_data = firebase_ref.get() or {}
            status["firebase_signal_count"] = len(signals_data)
        
        # Check in-memory storage
        if SIGNAL_STORAGE_AVAILABLE:
            status["memory_signal_count"] = len(signal_storage.messages)
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting debug status: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/debug/add-test-signal")
async def add_test_signal():
    """Add a test signal for debugging (only use in development)"""
    try:
        test_signal = {
            "id": f"test_{int(datetime.now().timestamp() * 1000)}",
            "channel_id": "test_channel",
            "channel_name": "Test Channel",
            "message_id": 12345,
            "text": "XAUUSD BUY\nEntry: 2050.00\nSL: 2045.00\nTP1: 2055.00\nTP2: 2060.00\nTP3: 2065.00",
            "timestamp": datetime.now().isoformat(),
            "symbol": "XAUUSD",
            "direction": "BUY",
            "signal_type": "new_signal",
            "entry_min": 2050.00,
            "entry_max": None,
            "stop_loss": 2045.00,
            "take_profit_1": 2055.00,
            "take_profit_2": 2060.00,
            "take_profit_3": 2065.00,
            "executed": False,
            "status": "pending"
        }
        
        firebase_ref = get_firebase_ref()
        if firebase_ref:
            firebase_ref.child(test_signal["id"]).set(test_signal)
            logger.info(f"Test signal {test_signal['id']} added to Firebase")
        
        # Also add to memory if available
        if SIGNAL_STORAGE_AVAILABLE:
            from models.signal_message import SignalMessage
            signal_msg = SignalMessage(
                id=test_signal["id"],
                channel_id=test_signal["channel_id"],
                channel_name=test_signal["channel_name"],
                message_id=test_signal["message_id"],
                text=test_signal["text"],
                timestamp=datetime.fromisoformat(test_signal["timestamp"]),
                symbol=test_signal["symbol"],
                direction=test_signal["direction"],
                signal_type=test_signal["signal_type"],
                entry_min=test_signal["entry_min"],
                stop_loss=test_signal["stop_loss"],
                take_profit_1=test_signal["take_profit_1"],
                take_profit_2=test_signal["take_profit_2"],
                take_profit_3=test_signal["take_profit_3"]
            )
            signal_storage.messages.insert(0, signal_msg)
            logger.info(f"Test signal added to memory storage")
        
        return {
            "success": True,
            "message": "Test signal added successfully",
            "signal": test_signal
        }
    except Exception as e:
        logger.error(f"Error adding test signal: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
