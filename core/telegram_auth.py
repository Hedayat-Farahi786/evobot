"""
Telegram-based Authentication Service
Uses the existing Telegram session to authenticate users.
When user logs in, they're authenticated via their Telegram account.
"""

import os
import json
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any
import logging

logger = logging.getLogger("evobot.telegram_auth")

# JWT Configuration
def get_or_create_secret_key() -> str:
    """Get existing or create new secure secret key"""
    secret_file = "data/.telegram_auth_secret"
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    secret_key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(secret_file), exist_ok=True)
    with open(secret_file, 'w') as f:
        f.write(secret_key)
    os.chmod(secret_file, 0o600)
    return secret_key

SECRET_KEY = os.getenv("TELEGRAM_AUTH_SECRET") or get_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TelegramUser:
    """Telegram user data model"""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name', '')
        self.username = data.get('username', '')
        self.phone = data.get('phone', '')
        self.photo_path = data.get('photo_path')
        self.premium = data.get('premium', False)
        self.role = data.get('role', 'Admin')  # Default to Admin since this is their own bot
        self.created_at = data.get('created_at', datetime.utcnow().isoformat())
        self.last_login = data.get('last_login')
    
    @property
    def display_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.username or f"User {self.id}"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'phone': self.phone,
            'photo_path': self.photo_path,
            'premium': self.premium,
            'role': self.role,
            'display_name': self.display_name,
            'created_at': self.created_at,
            'last_login': self.last_login
        }


class TelegramAuthService:
    """
    Telegram-based authentication service.
    Uses the existing Telegram session for authentication.
    """
    
    def __init__(self):
        self.users_file = 'data/telegram_users.json'
        self.sessions_file = 'data/telegram_sessions.json'
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure data files exist"""
        os.makedirs('data', exist_ok=True)
        for file_path in [self.users_file, self.sessions_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({}, f)
    
    def _load_users(self) -> Dict:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: Dict):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2, default=str)
    
    def _load_sessions(self) -> Dict:
        """Load active sessions"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_sessions(self, sessions: Dict):
        """Save sessions to file"""
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2, default=str)
    
    def _get_default_user(self) -> Dict:
        """Get default user when Telegram connection isn't available"""
        return {
            'id': 0,
            'first_name': 'EvoBot',
            'last_name': 'User',
            'username': 'evobot_user',
            'phone': '',
            'photo_path': None,
            'premium': False
        }
    
    def _get_cached_user(self) -> Optional[Dict]:
        """Get cached Telegram user info to avoid session conflicts"""
        cache_file = 'data/telegram_user_cache.json'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                # Cache valid for 24 hours
                cached_at = datetime.fromisoformat(cache.get('cached_at', '2000-01-01'))
                if datetime.utcnow() - cached_at < timedelta(hours=24):
                    return cache.get('user_info')
            except:
                pass
        return None
    
    def _cache_user(self, user_info: Dict):
        """Cache Telegram user info"""
        cache_file = 'data/telegram_user_cache.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'user_info': user_info,
                    'cached_at': datetime.utcnow().isoformat()
                }, f, indent=2)
        except:
            pass
    
    async def check_telegram_session(self) -> Tuple[bool, Optional[Dict]]:
        """
        Check if there's a valid Telegram session and get user info.
        Returns (is_valid, user_info)
        Uses cached user info to avoid session conflicts.
        """
        # First check cache to avoid session conflicts
        cached_user = self._get_cached_user()
        if cached_user:
            logger.info("Using cached Telegram user info")
            return True, cached_user
        
        # Check if session file exists (basic validation)
        session_path = 'evobot_session'
        if not os.path.exists(f'{session_path}.session'):
            logger.warning("No Telegram session file")
            return False, None
        
        # Try to get fresh user info from Telegram
        from telethon import TelegramClient
        from dotenv import load_dotenv
        load_dotenv()
        
        try:
            # Get settings
            settings_file = 'data/settings_cache.json'
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            
            api_id = settings.get('telegram', {}).get('api_id')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            
            if not api_id or not api_hash:
                logger.warning("Telegram not configured")
                # If session exists but can't connect, allow login with default user
                return True, self._get_default_user()
            
            # Use a separate session for auth checks to avoid conflicts
            auth_session_path = 'data/auth_session'
            
            # Copy session file if needed
            import shutil
            if not os.path.exists(f'{auth_session_path}.session'):
                try:
                    shutil.copy(f'{session_path}.session', f'{auth_session_path}.session')
                except:
                    pass
            
            client = TelegramClient(auth_session_path, api_id, api_hash)
            
            try:
                await client.connect()
                
                if not await client.is_user_authorized():
                    await client.disconnect()
                    logger.warning("Telegram session not authorized")
                    return True, self._get_default_user()
                
                me = await client.get_me()
                
                # Download profile photo
                photo_path = None
                if me.photo:
                    os.makedirs('data/user_photos', exist_ok=True)
                    photo_file = f'data/user_photos/{me.id}.jpg'
                    try:
                        await client.download_profile_photo(me, file=photo_file)
                        if os.path.exists(photo_file):
                            photo_path = photo_file
                    except:
                        pass
                
                user_info = {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'username': me.username,
                    'phone': me.phone,
                    'photo_path': photo_path,
                    'premium': getattr(me, 'premium', False)
                }
                
                await client.disconnect()
                
                # Cache the user info
                self._cache_user(user_info)
                
                return True, user_info
                
            except Exception as conn_err:
                logger.error(f"Connection error: {conn_err}")
                try:
                    await client.disconnect()
                except:
                    pass
                # If session exists, allow with default user
                return True, self._get_default_user()
            
        except Exception as e:
            logger.error(f"Error checking Telegram session: {e}")
            return False, None
    
    def get_or_create_user(self, telegram_user: Dict) -> TelegramUser:
        """Get existing user or create new one from Telegram data"""
        users = self._load_users()
        user_id = str(telegram_user['id'])
        
        if user_id in users:
            # Update existing user
            user_data = users[user_id]
            user_data.update({
                'first_name': telegram_user.get('first_name', user_data.get('first_name', '')),
                'last_name': telegram_user.get('last_name', user_data.get('last_name', '')),
                'username': telegram_user.get('username', user_data.get('username', '')),
                'phone': telegram_user.get('phone', user_data.get('phone', '')),
                'photo_path': telegram_user.get('photo_path', user_data.get('photo_path')),
                'premium': telegram_user.get('premium', user_data.get('premium', False)),
                'last_login': datetime.utcnow().isoformat()
            })
        else:
            # Create new user
            user_data = {
                'id': telegram_user['id'],
                'first_name': telegram_user.get('first_name', ''),
                'last_name': telegram_user.get('last_name', ''),
                'username': telegram_user.get('username', ''),
                'phone': telegram_user.get('phone', ''),
                'photo_path': telegram_user.get('photo_path'),
                'premium': telegram_user.get('premium', False),
                'role': 'Admin',  # First user is admin
                'created_at': datetime.utcnow().isoformat(),
                'last_login': datetime.utcnow().isoformat()
            }
        
        users[user_id] = user_data
        self._save_users(users)
        
        return TelegramUser(user_data)
    
    def create_tokens(self, user: TelegramUser) -> Dict:
        """Create access and refresh tokens for user"""
        now = datetime.utcnow()
        
        # Access token
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        }
        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Refresh token
        refresh_payload = {
            'user_id': user.id,
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        }
        refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Store session
        session_id = secrets.token_hex(16)
        sessions = self._load_sessions()
        sessions[session_id] = {
            'user_id': user.id,
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
            'refresh_token_hash': hashlib.sha256(refresh_token.encode()).hexdigest()
        }
        self._save_sessions(sessions)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            'user': user.to_dict()
        }
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True, payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return False, None
    
    def get_user_by_id(self, user_id: int) -> Optional[TelegramUser]:
        """Get user by Telegram ID"""
        users = self._load_users()
        user_data = users.get(str(user_id))
        if user_data:
            return TelegramUser(user_data)
        return None
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict]]:
        """Refresh access token using refresh token"""
        is_valid, payload = self.verify_token(refresh_token)
        
        if not is_valid or payload.get('type') != 'refresh':
            return False, None
        
        user = self.get_user_by_id(payload['user_id'])
        if not user:
            return False, None
        
        # Create new access token only
        now = datetime.utcnow()
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        }
        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        return True, {
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_HOURS * 3600
        }
    
    def invalidate_session(self, user_id: int):
        """Invalidate all sessions for a user"""
        sessions = self._load_sessions()
        sessions = {k: v for k, v in sessions.items() if v.get('user_id') != user_id}
        self._save_sessions(sessions)
    
    async def authenticate(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Main authentication method.
        Checks Telegram session and creates tokens if valid.
        Returns (success, message, token_data)
        """
        # Check Telegram session
        is_valid, telegram_user = await self.check_telegram_session()
        
        if not is_valid or not telegram_user:
            return False, "No valid Telegram session. Please set up Telegram first.", None
        
        # Get or create user
        user = self.get_or_create_user(telegram_user)
        
        # Create tokens
        token_data = self.create_tokens(user)
        
        logger.info(f"User authenticated: {user.display_name} (ID: {user.id})")
        
        return True, "Authentication successful", token_data


# Singleton instance
telegram_auth_service = TelegramAuthService()
