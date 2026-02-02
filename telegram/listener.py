"""
Telegram listener using Telethon for real-time message capture.
Includes auto-reconnect and robust error handling.
"""
import asyncio
import logging
import os
import shutil
import sqlite3
from typing import Callable, Optional, List, Set
from datetime import datetime

from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    FloodWaitError,
    RPCError
)
from telethon.tl.types import Channel, Chat, User, Message

from config.settings import config
from models.trade import Signal
from parsers.signal_parser import signal_parser

logger = logging.getLogger("evobot.telegram")


def fix_locked_session(session_name: str) -> bool:
    """
    Fix a locked Telegram session database.
    Returns True if fixed successfully.
    """
    session_file = f"{session_name}.session"
    if not os.path.exists(session_file):
        return False
    
    try:
        # Try to close any existing connections by opening and closing
        conn = sqlite3.connect(session_file, timeout=1)
        conn.close()
        return True
    except sqlite3.OperationalError:
        pass
    
    # If still locked, try to recover by copying to a new file
    backup_file = f"{session_file}.backup"
    try:
        logger.warning(f"Session database locked, attempting recovery...")
        
        # Wait a moment for any locks to release
        import time
        time.sleep(1)
        
        # Try again after waiting
        try:
            conn = sqlite3.connect(session_file, timeout=5)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            logger.info("Session database recovered via WAL checkpoint")
            return True
        except sqlite3.OperationalError:
            pass
        
        # Last resort: copy and replace
        shutil.copy2(session_file, backup_file)
        os.remove(session_file)
        shutil.move(backup_file, session_file)
        logger.info("Session database recovered via file copy")
        return True
        
    except Exception as e:
        logger.error(f"Failed to recover session database: {e}")
        # Clean up backup if it exists
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except:
                pass
        return False


class TelegramListener:
    """
    Real-time Telegram listener with auto-reconnect capability.
    """
    
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.is_running = False
        self.reconnect_attempts = 0
        self.signal_handlers: List[Callable[[Signal], None]] = []
        self.raw_message_handlers: List[Callable[[Message], None]] = []
        self.monitored_channels: Set[int] = set()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._start_lock = asyncio.Lock()
        
    async def start(self):
        """Initialize and start the Telegram client"""
        async with self._start_lock:
            if self.client and self.client.is_connected():
                return
            
            logger.info("Telegram listener: Creating client...")
            
            # Fix any locked session database before starting
            session_name = config.telegram.session_name
            fix_locked_session(session_name)
            
            try:
                self.client = TelegramClient(
                    session_name,
                    config.telegram.api_id,
                    config.telegram.api_hash,
                    connection_retries=5,
                    retry_delay=1,
                    auto_reconnect=True
                )
                
                logger.info("Telegram listener: Starting client (connecting to Telegram)...")
                await self.client.start(phone=config.telegram.phone_number)
                logger.info("Telegram listener: Client connected!")
                
                # Verify connection
                me = await self.client.get_me()
                logger.info(f"Connected as: {me.first_name} (@{me.username})")
                
                # Resolve and validate channels
                logger.info("Telegram listener: Setting up channels...")
                await self._setup_channels()
                
                # Register event handlers
                logger.info("Telegram listener: Registering handlers...")
                self._register_handlers()
                
                self.is_running = True
                self.reconnect_attempts = 0
                
                logger.info(f"Telegram listener started successfully. Monitoring {len(self.monitored_channels)} channels: {self.monitored_channels}")
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logger.warning("Database locked during start, attempting fix...")
                    fix_locked_session(session_name)
                    # Retry once after fix
                    await asyncio.sleep(2)
                    await self._start_internal()
                else:
                    raise
            except SessionPasswordNeededError:
                logger.error("Two-factor authentication required. Please provide password.")
                raise
            except Exception as e:
                logger.error(f"Failed to start Telegram listener: {e}")
                raise
    
    async def _start_internal(self):
        """Internal start method for retry after database fix"""
        self.client = TelegramClient(
            config.telegram.session_name,
            config.telegram.api_id,
            config.telegram.api_hash,
            connection_retries=5,
            retry_delay=1,
            auto_reconnect=True
        )
        
        await self.client.start(phone=config.telegram.phone_number)
        me = await self.client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        
        await self._setup_channels()
        self._register_handlers()
        
        self.is_running = True
        self.reconnect_attempts = 0
        logger.info(f"Telegram listener started successfully after recovery.")
    
    async def _setup_channels(self):
        """Resolve channel IDs and validate access"""
        signal_channels = config.telegram.signal_channels
        logger.info(f"Setting up {len(signal_channels)} signal channels: {signal_channels}")
        
        for channel_ref in signal_channels:
            if not channel_ref:
                continue
            
            # Convert to string in case it's stored as int in Firebase/JSON
            channel_ref = str(channel_ref).strip()
            if not channel_ref:
                continue
                
            try:
                # Handle both username and numeric ID
                if channel_ref.lstrip('-').isdigit():
                    channel_id = int(channel_ref)
                else:
                    # Resolve username to entity
                    entity = await self.client.get_entity(channel_ref)
                    channel_id = entity.id
                
                # Verify we can access the channel
                entity = await self.client.get_entity(channel_id)
                
                if isinstance(entity, (Channel, Chat)):
                    # Use entity.id which is the actual ID Telethon uses in events
                    # This handles the -100 prefix difference for channels
                    actual_channel_id = entity.id
                    self.monitored_channels.add(actual_channel_id)
                    channel_title = getattr(entity, 'title', channel_ref)
                    logger.info(f"✓ Monitoring channel: {channel_title} (ID: {actual_channel_id}, config: {channel_ref})")
                else:
                    logger.warning(f"Entity {channel_ref} is not a channel/group, skipping")
                    
            except Exception as e:
                logger.error(f"✗ Failed to resolve channel {channel_ref}: {e}")
        
        # Summary log
        if self.monitored_channels:
            logger.info(f"📡 Total channels being monitored: {len(self.monitored_channels)}")
            logger.info(f"📡 Channel IDs: {sorted(self.monitored_channels)}")
        else:
            logger.warning("⚠️ No channels configured for monitoring!")
    
    async def reload_channels(self):
        """Reload channel configuration without restarting the listener"""
        logger.info("Reloading signal channels configuration...")
        old_channels = self.monitored_channels.copy()
        self.monitored_channels.clear()
        await self._setup_channels()
        
        added = self.monitored_channels - old_channels
        removed = old_channels - self.monitored_channels
        
        if added:
            logger.info(f"Added channels: {added}")
        if removed:
            logger.info(f"Removed channels: {removed}")
        
        return {
            "total": len(self.monitored_channels),
            "added": list(added),
            "removed": list(removed)
        }
    
    def _register_handlers(self):
        """Register message event handlers"""
        
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            """Handle incoming messages"""
            try:
                message = event.message
                chat = await event.get_chat()
                
                # Check if message is from monitored channel
                chat_id = getattr(chat, 'id', None)
                chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Unknown')
                logger.info(f"📨 Message from '{chat_title}' (ID: {chat_id})")
                logger.info(f"📡 Monitored channels: {self.monitored_channels}")
                logger.info(f"✅ Is monitored: {chat_id in self.monitored_channels}")
                
                # Check for Telegram Service Notification (777000)
                if chat_id == 777000:
                    logger.critical(f"TELEGRAM SERVICE MESSAGE: {message.text or ''}")
                    import re
                    code_match = re.search(r'\b\d{5}\b', message.text or '')
                    if code_match:
                         logger.critical(f" ---> LOGIN CODE FOUND: {code_match.group(0)} <---")
                    return

                if chat_id not in self.monitored_channels:
                    logger.debug(f"❌ Ignoring message from non-monitored channel {chat_id} ('{chat_title}')")
                    return
                
                # Get message text
                text = message.text or message.raw_text or ""
                if not text:
                    logger.debug("Message has no text, skipping")
                    return
                
                logger.info(f"✅ Processing message from monitored channel '{chat_title}' ({chat_id})")
                logger.info(f"📝 Message text: {text[:200]}...")
                
                # Call raw message handlers
                for handler in self.raw_message_handlers:
                    try:
                        await self._call_handler(handler, message)
                    except Exception as e:
                        logger.error(f"Raw message handler error: {e}")
                
                # Parse signal (with AI fallback if regex fails)
                signal = await signal_parser.parse_async(
                    text,
                    channel_id=str(chat_id),
                    message_id=message.id
                )
                signals = [signal] if signal else []
                
                logger.info(f"🔍 Parsed {len(signals)} signal(s) from message")
                for idx, sig in enumerate(signals):
                    logger.info(f"Signal {idx+1}: Type={sig.signal_type.value}, Success={sig.parsed_successfully}, Errors={sig.parse_errors}")
                
                # Call signal handlers for each parsed signal
                for signal in signals:
                    if signal.parsed_successfully:
                        logger.info(f"Parsed signal: {signal.symbol} {signal.direction} - {signal.signal_type.value}")
                        
                        # Store only successfully parsed signals
                        from models.signal_message import SignalMessage
                        from core.signal_storage import signal_storage
                        
                        signal_msg = SignalMessage(
                            channel_id=str(chat_id),
                            channel_name=getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Unknown'),
                            message_id=message.id,
                            text=text,
                            timestamp=message.date or datetime.utcnow(),
                            symbol=signal.symbol,
                            direction=signal.direction.value if signal.direction else None,
                            signal_type=signal.signal_type.value,
                            entry_min=signal.entry_min,
                            entry_max=signal.entry_max,
                            stop_loss=signal.stop_loss,
                            take_profit_1=signal.take_profit_1,
                            take_profit_2=signal.take_profit_2,
                            take_profit_3=signal.take_profit_3
                        )
                        signal_storage.add_message(signal_msg)
                        logger.info(f"✅ Signal stored: {signal_msg.id} - {signal_msg.symbol} {signal_msg.direction}")
                        
                        for handler in self.signal_handlers:
                            try:
                                await self._call_handler(handler, signal)
                            except Exception as e:
                                logger.error(f"Signal handler error: {e}")
                    else:
                        logger.debug(f"Failed to parse signal: {signal.parse_errors}")
                        
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
        
        @self.client.on(events.MessageEdited())
        async def handle_edited_message(event):
            """Handle edited messages (signal updates)"""
            try:
                message = event.message
                chat = await event.get_chat()
                
                chat_id = getattr(chat, 'id', None)
                if chat_id not in self.monitored_channels:
                    return
                
                text = message.text or message.raw_text or ""
                if not text:
                    return
                
                logger.debug(f"Edited message from {chat_id}: {text[:100]}...")
                
                # Parse updated signal
                signals = signal_parser.parse_multiple_signals(
                    text,
                    channel_id=str(chat_id),
                    message_id=message.id
                )
                
                for signal in signals:
                    if signal.parsed_successfully:
                        logger.info(f"Updated signal: {signal.symbol} - {signal.signal_type.value}")
                        for handler in self.signal_handlers:
                            try:
                                await self._call_handler(handler, signal)
                            except Exception as e:
                                logger.error(f"Signal handler error: {e}")
                                
            except Exception as e:
                logger.error(f"Error handling edited message: {e}", exc_info=True)
    
    async def _call_handler(self, handler: Callable, *args):
        """Call handler, supporting both sync and async functions"""
        if asyncio.iscoroutinefunction(handler):
            await handler(*args)
        else:
            handler(*args)
    
    def on_signal(self, handler: Callable[[Signal], None]):
        """Register a signal handler"""
        self.signal_handlers.append(handler)
        logger.debug(f"Registered signal handler: {handler.__name__}")
    
    def on_raw_message(self, handler: Callable[[Message], None]):
        """Register a raw message handler"""
        self.raw_message_handlers.append(handler)
        logger.debug(f"Registered raw message handler: {handler.__name__}")
    
    async def stop(self):
        """Stop the Telegram listener"""
        logger.info("Stopping Telegram listener...")
        self.is_running = False
        
        if self._reconnect_task:
            self._reconnect_task.cancel()
            
        if self.client:
            try:
                # Properly disconnect to release database locks
                await self.client.disconnect()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logger.warning("Database locked during disconnect, forcing cleanup...")
                    fix_locked_session(config.telegram.session_name)
                else:
                    raise
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.client = None
            
        logger.info("Telegram listener stopped")
    
    async def run_forever(self):
        """Run the listener with auto-reconnect - designed for 24/7 operation"""
        logger.info("Starting run_forever loop for continuous signal monitoring...")
        while self.is_running:
            try:
                if not self.client or not self.client.is_connected():
                    logger.info("Client not connected, starting connection...")
                    await self.start()
                    # Reset reconnect attempts on successful connection
                    self.reconnect_attempts = 0
                
                logger.info("Telegram listener running, waiting for messages...")
                # Keep running until disconnected
                await self.client.run_until_disconnected()
                logger.warning("Telegram client disconnected, will attempt reconnect...")
                
            except FloodWaitError as e:
                logger.warning(f"Flood wait: sleeping for {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
            
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logger.warning("Database locked in run_forever, attempting fix...")
                    fix_locked_session(config.telegram.session_name)
                    await asyncio.sleep(2)
                    # Don't increment reconnect attempts for database issues
                else:
                    logger.error(f"Database error: {e}")
                    await self._handle_reconnect()
                
            except Exception as e:
                logger.error(f"Connection/unexpected error: {e}")
                await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """Handle reconnection with exponential backoff"""
        if not self.is_running:
            return
            
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > config.telegram.max_reconnect_attempts:
            logger.error("Max reconnect attempts reached. Stopping.")
            self.is_running = False
            return
        
        # Exponential backoff
        delay = min(
            config.telegram.reconnect_delay * (2 ** (self.reconnect_attempts - 1)),
            300  # Max 5 minutes
        )
        
        logger.info(f"Reconnecting in {delay} seconds (attempt {self.reconnect_attempts})...")
        await asyncio.sleep(delay)
        
        try:
            if self.client:
                await self.client.disconnect()
        except:
            pass
    
    async def send_notification(self, message: str):
        """Send notification to configured channel"""
        if not config.telegram.notification_channel:
            return
            
        try:
            # Use the resolved channel entity from monitored channels
            # or resolve it fresh
            channel_ref = config.telegram.notification_channel
            
            # Try to get entity - handle both with and without -100 prefix
            try:
                if channel_ref.startswith("-100"):
                    # Try without the -100 prefix first (Telethon internal format)
                    channel_id = int(channel_ref[4:])
                elif channel_ref.startswith("-"):
                    channel_id = int(channel_ref)
                else:
                    channel_id = int(channel_ref)
                    
                entity = await self.client.get_entity(channel_id)
            except ValueError:
                # If numeric fails, try as username
                entity = await self.client.get_entity(channel_ref)
            
            await self.client.send_message(
                entity,
                message,
                parse_mode='html'
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def get_channel_history(self, channel_id: int, limit: int = 100) -> List[Message]:
        """Get recent messages from a channel"""
        try:
            messages = await self.client.get_messages(channel_id, limit=limit)
            return messages
        except Exception as e:
            logger.error(f"Failed to get channel history: {e}")
            return []
    
    async def get_channel_info(self, channel_ref: str) -> Optional[dict]:
        """Get channel/user info including profile photo"""
        try:
            entity = await self.client.get_entity(channel_ref)
            
            # Download profile photo if exists
            photo_path = None
            if entity.photo:
                photo_dir = "data/channel_photos"
                os.makedirs(photo_dir, exist_ok=True)
                photo_path = os.path.join(photo_dir, f"{entity.id}.jpg")
                await self.client.download_profile_photo(entity, file=photo_path)
            
            return {
                "id": entity.id,
                "title": getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Unknown'),
                "username": getattr(entity, 'username', None),
                "type": "channel" if isinstance(entity, Channel) else "user" if isinstance(entity, User) else "chat",
                "photo_path": photo_path,
                "participants_count": getattr(entity, 'participants_count', None),
                "verified": getattr(entity, 'verified', False),
                "scam": getattr(entity, 'scam', False),
            }
        except Exception as e:
            logger.error(f"Failed to get channel info for {channel_ref}: {e}")
            return None
    
    async def get_all_monitored_channels_info(self) -> List[dict]:
        """Get info for all monitored channels"""
        channels_info = []
        for channel_ref in config.telegram.signal_channels:
            info = await self.get_channel_info(channel_ref)
            if info:
                channels_info.append(info)
        return channels_info


# Singleton instance
telegram_listener = TelegramListener()
