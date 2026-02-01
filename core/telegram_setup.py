"""
Telegram Setup Service
Handles the interactive login flow for Telegram from the web interface.
"""
import asyncio
import logging
import os
import shutil
import time
from typing import Optional, Tuple, Dict
from telethon import TelegramClient, errors
from config.settings import config
from telegram.listener import telegram_listener

logger = logging.getLogger("evobot.telegram_setup")

class TelegramSetupService:
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.phone_code_hash: Optional[str] = None
        self.phone_number: Optional[str] = None
        # Create a unique session name for this instance to avoid file locks
        self.temp_session_name = f"{config.telegram.session_name}_setup_{int(time.time())}"
        
    def _get_temp_session_file(self) -> str:
        """Get the temp session file path"""
        return f"{self.temp_session_name}.session"
        
    def _cleanup_temp_session_file(self):
        """Remove temp session file to ensure fresh state"""
        temp_file = self._get_temp_session_file()
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.info(f"Removed stale temp session file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not remove temp session file: {e}")
        
    async def get_client(self, force_new: bool = False) -> TelegramClient:
        """Get or create the Telegram client"""
        if self.client and not force_new:
            if not self.client.is_connected():
                await self.client.connect()
            return self.client
        
        # If forcing new client, cleanup existing
        if force_new and self.client:
            try:
                await self.client.disconnect()
            except:
                pass
            self.client = None
            
        # Clean up any existing temp session file to ensure fresh state
        self._cleanup_temp_session_file()
            
        # Use a temporary session for setup to avoid conflicts with existing bad sessions
        # self.temp_session_name is set in __init__ to include timestamp
        
        # DEBUG: Verify credentials
        api_id = config.telegram.api_id
        api_hash = config.telegram.api_hash
        
        logger.info(f"Creating Telegram client with API_ID: {api_id}")
        
        self.client = TelegramClient(
            self.temp_session_name,
            config.telegram.api_id,
            config.telegram.api_hash
        )
        
        await self.client.connect()
        return self.client

    async def request_code(self, phone: str) -> Tuple[bool, str]:
        """Request verification code for phone number"""
        try:
            # STOP backend listener to ensure it doesn't swallow the code or lock the session
            if telegram_listener:
                logger.info("Pausing background Telegram listener during setup...")
                await telegram_listener.stop()

            # Clean up any existing temp session to ensure fresh start
            self._cleanup_temp_session_file()
            # If same phone and we have a hash, try resend first
            if self.client and self.phone_number == phone and self.phone_code_hash:
                try:
                    logger.info(f"Attempting to resend code to {phone}")
                    if not self.client.is_connected():
                        await self.client.connect()
                    sent = await self.client.resend_code_request(phone, self.phone_code_hash)
                    self.phone_code_hash = sent.phone_code_hash
                    delivery_type = self._get_delivery_type(sent)
                    logger.info(f"Code resent via {delivery_type} to {phone}")
                    return True, f"Verification code resent via {delivery_type}. Check your Telegram app on your phone."
                except errors.FloodWaitError as e:
                    return False, f"Too many attempts. Please wait {e.seconds} seconds."
                except Exception as e:
                    logger.info(f"Resend failed ({e}), requesting fresh code")
                    # Reset state and fall through to send new code
                    await self.reset_setup()
            
            # Get fresh client (clean session)
            client = await self.get_client(force_new=True)
            self.phone_number = phone
            
            sent = await client.send_code_request(phone)
            self.phone_code_hash = sent.phone_code_hash
            
            delivery_type = self._get_delivery_type(sent)
            
            # Log detailed info about where code was sent
            logger.info(f"Code sent via {delivery_type} to {phone}")
            logger.info(f"Code type: {type(sent.type).__name__}")
            
            # Provide specific instructions based on delivery type
            if delivery_type == "Telegram App":
                return True, f"Verification code sent to your Telegram app. Look for a message from 'Telegram' in your chats (not SMS)."
            elif delivery_type == "SMS":
                return True, f"Verification code sent via SMS to {phone}."
            else:
                return True, f"Verification code sent via {delivery_type}. Check your phone."
            
        except errors.FloodWaitError as e:
            return False, f"Too many attempts. Please wait {e.seconds} seconds."
        except errors.PhoneNumberInvalidError:
            return False, "Invalid phone number format. Use international format like +1234567890."
        except Exception as e:
            err_msg = str(e)
            if "options for this type of number were already used" in err_msg:
                 return False, "Code already sent recently. Please wait 2 minutes and check your Telegram app."
            logger.error(f"Error requesting code: {e}")
            return False, f"Error: {err_msg}"
    
    async def resend_code_sms(self) -> Tuple[bool, str]:
        """Force resend verification code via SMS"""
        try:
            # STOP backend listener
            if telegram_listener:
                await telegram_listener.stop()

            if not self.client or not self.phone_number or not self.phone_code_hash:
                return False, "No active code request. Please request a new code first."
        
            if not self.client.is_connected():
                await self.client.connect()
            
            # Force SMS using send_code_request with force_sms=True
            # This creates a NEW request but forces SMS delivery
            sent = await self.client.send_code_request(self.phone_number, force_sms=True)
            self.phone_code_hash = sent.phone_code_hash
            
            delivery_type = self._get_delivery_type(sent)
            logger.info(f"Code resent via {delivery_type} (FORCED SMS) to {self.phone_number}")
            
            return True, f"Code resent via {delivery_type}. Check your phone for SMS."
            
        except errors.FloodWaitError as e:
            return False, f"Too many attempts. Please wait {e.seconds} seconds."
        except Exception as e:
            logger.error(f"Error resending code: {e}")
            return False, f"Error: {str(e)}"
    
    def _get_delivery_type(self, sent) -> str:
        """Determine how the code was delivered"""
        delivery_type = "Telegram App"
        try:
            type_str = str(type(sent.type).__name__)
            if 'Sms' in type_str:
                delivery_type = "SMS"
            elif 'Call' in type_str:
                delivery_type = "Phone Call"
            elif 'App' in type_str:
                delivery_type = "Telegram App"
        except:
            pass
        return delivery_type
    
    async def reset_setup(self):
        """Reset setup state and clean up files"""
        if telegram_listener:
            await telegram_listener.stop()
            
        if self.client:
            try:
                await self.client.disconnect()
            except:
                pass
            self.client = None
        
        self.phone_code_hash = None
        self.phone_number = None
        self._cleanup_temp_session_file()
            
    async def _finalize_login(self):
        """Finalize login by moving temp session to main session"""
        try:
            # STOP listener to release file lock on main session
            if telegram_listener:
                await telegram_listener.stop()

            if self.client:
                await self.client.disconnect()
            
            target_session = config.telegram.session_name
            
            # Add .session extension if not present
            temp_file = self.temp_session_name
            if not temp_file.endswith('.session'):
                temp_file += '.session'
                
            target_file = target_session
            if not target_file.endswith('.session'):
                target_file += '.session'
            
            # Backup existing if present
            if os.path.exists(target_file):
                backup = f"{target_file}.bak"
                if os.path.exists(backup):
                    os.remove(backup)
                os.rename(target_file, backup)
            
            # Move temp to target
            if os.path.exists(temp_file):
                os.rename(temp_file, target_file)
                logger.info(f"Session setup complete. Moved {temp_file} to {target_file}")
            else:
                logger.error(f"Temp session file {temp_file} not found!")
                
            self.client = None
            return True
        except Exception as e:
            logger.error(f"Error finalizing setup: {e}")
            return False

    async def verify_code(self, code: str) -> Tuple[bool, str, bool]:
        """
        Verify the code.
        Returns: (success, message, requires_password)
        """
        if not self.client or not self.phone_number or not self.phone_code_hash:
            return False, "Setup session expired. Please start over.", False

        try:
            await self.client.sign_in(
                phone=self.phone_number,
                code=code,
                phone_code_hash=self.phone_code_hash
            )
            
            # Successful sign in
            await self._finalize_login()
            return True, "Authentication successful", False
        except errors.SessionPasswordNeededError:
            return True, "Two-step verification enabled", True
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return False, str(e), False

    async def verify_password(self, password: str) -> Tuple[bool, str]:
        """Verify 2FA password"""
        if not self.client:
            return False, "Setup session expired"

        try:
            await self.client.sign_in(password=password)
            await self._finalize_login()
            return True, "Authentication successful"
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False, str(e)
            
    async def cleanup(self):
        """Disconnect and cleanup"""
        if self.client:
            await self.client.disconnect()
            self.client = None
        
        # Cleanup temp file if it still exists (failed/aborted setup)
        if self.temp_session_name:
            temp_file = self.temp_session_name
            if not temp_file.endswith('.session'):
                temp_file += '.session'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

# Singleton instance
telegram_setup_service = TelegramSetupService()
