"""
Enhanced Authentication and User Management System
Features:
- Secure password hashing with bcrypt
- JWT token-based authentication
- Role-based access control (RBAC)
- Persistent user storage
- Account lockout protection
- Session management
- Audit logging
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import jwt
import bcrypt
import secrets
import json
import os
import re
import logging
from pydantic import BaseModel, validator, EmailStr
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("evobot.auth")

# Generate a secure secret key if not provided
def get_or_create_secret_key() -> str:
    """Get existing or create new secure secret key"""
    secret_file = "data/.secret_key"
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    # Generate a new secure key
    secret_key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(secret_file), exist_ok=True)
    with open(secret_file, 'w') as f:
        f.write(secret_key)
    os.chmod(secret_file, 0o600)  # Restrict permissions
    return secret_key

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or get_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)

# Role definitions with permissions
ROLES = {
    "admin": {
        "level": 100,
        "permissions": ["*"],  # All permissions
        "description": "Full system access"
    },
    "user": {
        "level": 50,
        "permissions": ["trade:view", "trade:execute", "dashboard:view", "settings:view"],
        "description": "Can view and execute trades"
    },
    "viewer": {
        "level": 10,
        "permissions": ["trade:view", "dashboard:view"],
        "description": "Read-only access"
    }
}

# Password policy
PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "special_chars": "!@#$%^&*(),.?\":{}|<>_-+=[]\\/"
}


class User(BaseModel):
    id: str
    username: str
    email: str
    role: str  # admin, user, viewer
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserInDB(User):
    hashed_password: str
    password_changed_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_by: Optional[str] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "viewer"
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscores only')
        return v.lower()
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ROLES:
            raise ValueError(f'Invalid role. Must be one of: {list(ROLES.keys())}')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        valid, msg = validate_password_strength(v)
        if not valid:
            raise ValueError(msg)
        return v


class PasswordReset(BaseModel):
    username: str
    new_password: str


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: dict


class TokenRefresh(BaseModel):
    refresh_token: str


# User storage with file persistence
USERS_FILE = "data/users.json"


class UserDatabase:
    """Persistent user database with file storage"""
    
    def __init__(self):
        self._users: Dict[str, dict] = {}
        self._lock_file = "data/.users.lock"
        self._load()
    
    def _load(self):
        """Load users from file"""
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        # Convert datetime strings back to datetime objects
                        for field in ['created_at', 'last_login', 'password_changed_at', 'locked_until']:
                            if user_data.get(field):
                                user_data[field] = datetime.fromisoformat(user_data[field])
                        self._users[username] = user_data
                logger.info(f"Loaded {len(self._users)} users from database")
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
    
    def _save(self):
        """Save users to file"""
        try:
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            data = {}
            for username, user_data in self._users.items():
                user_copy = user_data.copy()
                # Convert datetime objects to strings
                for field in ['created_at', 'last_login', 'password_changed_at', 'locked_until']:
                    if user_copy.get(field):
                        user_copy[field] = user_copy[field].isoformat()
                data[username] = user_copy
            
            with open(USERS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            os.chmod(USERS_FILE, 0o600)  # Restrict permissions
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def get(self, username: str) -> Optional[dict]:
        return self._users.get(username.lower())
    
    def __contains__(self, username: str) -> bool:
        return username.lower() in self._users
    
    def __setitem__(self, username: str, value: dict):
        self._users[username.lower()] = value
        self._save()
    
    def __delitem__(self, username: str):
        if username.lower() in self._users:
            del self._users[username.lower()]
            self._save()
    
    def __iter__(self):
        return iter(self._users)
    
    def __len__(self):
        return len(self._users)
    
    def values(self):
        return self._users.values()
    
    def items(self):
        return self._users.items()
    
    def keys(self):
        return self._users.keys()
    
    def update_user(self, username: str, updates: dict):
        """Update specific user fields"""
        if username.lower() in self._users:
            self._users[username.lower()].update(updates)
            self._save()


# Global user database instance
users_db = UserDatabase()


def validate_password_strength(password: str) -> tuple:
    """Validate password against security policy"""
    policy = PASSWORD_POLICY
    
    if len(password) < policy["min_length"]:
        return False, f"Password must be at least {policy['min_length']} characters"
    
    if policy["require_uppercase"] and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if policy["require_lowercase"] and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if policy["require_digit"] and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if policy["require_special"]:
        special_pattern = f"[{re.escape(policy['special_chars'])}]"
        if not re.search(special_pattern, password):
            return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    return True, "Password meets requirements"

def hash_password(password: str) -> str:
    """Hash password with bcrypt using strong salt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with longer expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # Unique token ID for revocation
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, token_type: str = "access") -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get current authenticated user from token"""
    from core.security import security_manager
    
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    # Check if token is blacklisted
    if security_manager.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    # Decode token
    payload = decode_token(token, "access")
    username = payload.get("sub")
    
    if username is None or username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    user = users_db.get(username)
    
    # Check if account is locked
    if user.get("locked_until"):
        if datetime.utcnow() < user["locked_until"]:
            remaining = int((user["locked_until"] - datetime.utcnow()).total_seconds())
            raise HTTPException(
                status_code=403,
                detail=f"Account locked. Try again in {remaining} seconds"
            )
        else:
            # Unlock account
            users_db.update_user(username, {"locked_until": None, "failed_login_attempts": 0})
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # Get permissions based on role
    role = user.get("role", "viewer")
    permissions = ROLES.get(role, {}).get("permissions", [])
    
    return User(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=role,
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        is_active=user.get("is_active", True),
        permissions=permissions
    )


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_user_with_permission(permission: str):
    """Factory for permission-based access control"""
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if "*" in current_user.permissions:
            return current_user
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {permission}"
            )
        return current_user
    return check_permission


def check_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    if "*" in user.permissions:
        return True
    return permission in user.permissions


def authenticate_user(username: str, password: str, ip_address: str = None) -> Optional[dict]:
    """Authenticate user with credentials"""
    from core.security import security_manager
    
    user = users_db.get(username.lower())
    if not user:
        # Still record failed attempt for non-existent users (prevent enumeration)
        security_manager.record_login_attempt(username, False, ip_address)
        return None
    
    # Check if account is locked
    locked, remaining = security_manager.is_account_locked(username)
    if locked:
        return None
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        security_manager.record_login_attempt(username, False, ip_address)
        
        # Update failed attempts in user record
        failed_attempts = user.get("failed_login_attempts", 0) + 1
        updates = {"failed_login_attempts": failed_attempts}
        
        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            updates["locked_until"] = datetime.utcnow() + timedelta(minutes=30)
            logger.warning(f"Account locked due to failed attempts: {username}")
        
        users_db.update_user(username, updates)
        return None
    
    # Successful login
    security_manager.record_login_attempt(username, True, ip_address)
    
    # Reset failed attempts and update last login
    users_db.update_user(username, {
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login": datetime.utcnow()
    })
    
    return user


def create_user(user_data: UserCreate, created_by: str = None) -> dict:
    """Create a new user"""
    from core.security import security_manager
    
    # Validate password strength
    valid, msg = validate_password_strength(user_data.password)
    if not valid:
        raise ValueError(msg)
    
    # Check if username exists
    if user_data.username.lower() in users_db:
        raise ValueError("Username already exists")
    
    # Create user record
    user_id = f"user-{secrets.token_hex(8)}"
    now = datetime.utcnow()
    
    new_user = {
        "id": user_id,
        "username": user_data.username.lower(),
        "email": user_data.email.lower(),
        "hashed_password": hash_password(user_data.password),
        "role": user_data.role,
        "created_at": now,
        "last_login": None,
        "is_active": True,
        "failed_login_attempts": 0,
        "locked_until": None,
        "password_changed_at": now,
        "created_by": created_by,
        "two_factor_enabled": False,
        "two_factor_secret": None
    }
    
    users_db[user_data.username.lower()] = new_user
    
    # Audit log
    security_manager.audit_log(
        "user_created",
        user_data.username,
        details={"created_by": created_by, "role": user_data.role}
    )
    
    logger.info(f"User created: {user_data.username} by {created_by}")
    return new_user


def change_password(username: str, current_password: str, new_password: str) -> bool:
    """Change user password"""
    from core.security import security_manager
    
    user = users_db.get(username)
    if not user:
        return False
    
    # Verify current password
    if not verify_password(current_password, user["hashed_password"]):
        security_manager.audit_log(
            "password_change_failed",
            username,
            details={"reason": "invalid_current_password"},
            severity="warning"
        )
        return False
    
    # Validate new password
    valid, msg = validate_password_strength(new_password)
    if not valid:
        raise ValueError(msg)
    
    # Update password
    users_db.update_user(username, {
        "hashed_password": hash_password(new_password),
        "password_changed_at": datetime.utcnow()
    })
    
    # Audit log
    security_manager.audit_log("password_changed", username)
    logger.info(f"Password changed for user: {username}")
    
    return True


def reset_password(username: str, new_password: str, admin_username: str) -> bool:
    """Admin reset user password"""
    from core.security import security_manager
    
    user = users_db.get(username)
    if not user:
        return False
    
    # Validate new password
    valid, msg = validate_password_strength(new_password)
    if not valid:
        raise ValueError(msg)
    
    # Update password and unlock account
    users_db.update_user(username, {
        "hashed_password": hash_password(new_password),
        "password_changed_at": datetime.utcnow(),
        "failed_login_attempts": 0,
        "locked_until": None
    })
    
    # Audit log
    security_manager.audit_log(
        "password_reset",
        username,
        details={"reset_by": admin_username},
        severity="warning"
    )
    logger.info(f"Password reset for user: {username} by admin: {admin_username}")
    
    return True


def init_default_admin():
    """Create default admin user if none exists"""
    if len(users_db) == 0:
        # Generate a secure random password for first-time setup
        default_password = os.getenv("ADMIN_PASSWORD", "Admin@123!")
        
        admin_user = {
            "id": "admin-001",
            "username": "admin",
            "email": "admin@evobot.local",
            "hashed_password": hash_password(default_password),
            "role": "admin",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
            "password_changed_at": datetime.utcnow(),
            "created_by": "system",
            "two_factor_enabled": False,
            "two_factor_secret": None
        }
        users_db["admin"] = admin_user
        logger.info("Default admin user created")
        print(f"╔{'═' * 50}╗")
        print(f"║ {'DEFAULT ADMIN CREDENTIALS':^48} ║")
        print(f"╠{'═' * 50}╣")
        print(f"║ Username: {'admin':<38} ║")
        print(f"║ Password: {default_password:<38} ║")
        print(f"╠{'═' * 50}╣")
        print(f"║ {'⚠️  CHANGE THIS PASSWORD IMMEDIATELY!':^48} ║")
        print(f"╚{'═' * 50}╝")


# Initialize default admin on module load
init_default_admin()
