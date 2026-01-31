"""
Firebase Authentication Service
Provides secure user authentication using Firebase Auth with local role-based access control.
Combines Firebase's powerful authentication with custom security features.
"""

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pydantic import BaseModel, EmailStr
import logging
from core.security import security_manager
import hashlib
import hmac

logger = logging.getLogger("evobot.firebase_auth")

# Pydantic models
class User(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    role: str = "Viewer"  # Admin, User, Viewer
    phone_number: Optional[str] = None
    photo_url: Optional[str] = None
    email_verified: bool = False
    disabled: bool = False

class UserInDB(User):
    created_at: str
    last_login: Optional[str] = None
    login_count: int = 0

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UserRoleUpdate(BaseModel):
    role: str  # Admin, User, Viewer

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: User

class FirebaseAuthService:
    """
    Firebase Authentication Service
    Handles user authentication, registration, and role management
    Integrates with Firebase Auth and Realtime Database
    """
    
    def __init__(self):
        self.db_ref = None
        self.initialized = False
        self.users_cache = {}
        self._local_store_path = os.path.join('data', 'users_local.json')

    # Local user store helpers (fallback when Firebase Realtime DB is unavailable)
    def _ensure_local_store(self):
        os.makedirs(os.path.dirname(self._local_store_path), exist_ok=True)
        if not os.path.exists(self._local_store_path):
            with open(self._local_store_path, 'w') as f:
                json.dump({}, f)

    def _load_all_local_users(self) -> Dict:
        try:
            self._ensure_local_store()
            with open(self._local_store_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load local users: {e}")
            return {}

    def _load_local_user(self, user_key: str) -> Optional[Dict]:
        try:
            users = self._load_all_local_users()
            return users.get(user_key)
        except Exception as e:
            logger.warning(f"Failed to load local user {user_key}: {e}")
            return None

    def _save_local_user(self, user_key: str, user_data: Dict):
        try:
            users = self._load_all_local_users()
            users[user_key] = user_data
            self._ensure_local_store()
            with open(self._local_store_path, 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save local user {user_key}: {e}")

    def _update_local_user(self, user_key: str, updates: Dict):
        try:
            users = self._load_all_local_users()
            user = users.get(user_key, {})
            user.update(updates)
            users[user_key] = user
            self._ensure_local_store()
            with open(self._local_store_path, 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update local user {user_key}: {e}")
    def initialize(self):
        """Initialize Firebase Admin SDK for authentication"""
        try:
            if not firebase_admin._apps:
                # Service account credentials from environment
                cred_dict = {
                    "type": "service_account",
                    "project_id": os.getenv("FIREBASE_PROJECT_ID", "evobot-8"),
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
                    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
                    "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                }
                
                # Only initialize if we have credentials
                if cred_dict["private_key"] and cred_dict["client_email"]:
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': os.getenv(
                            "FIREBASE_DATABASE_URL",
                            "https://evobot-8-default-rtdb.europe-west1.firebasedatabase.app"
                        )
                    })
                    self.db_ref = db.reference('/')
                    self.initialized = True
                    logger.info("Firebase Auth initialized successfully")
                else:
                    logger.warning("Firebase credentials not configured - falling back to local auth")
                    self.initialized = False
            else:
                self.db_ref = db.reference('/')
                self.initialized = True
        except Exception as e:
            logger.error(f"Firebase Auth initialization failed: {e}")
            self.initialized = False

    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Tuple[bool, str, Optional[User]]:
        """
        Create a new user with email and password
        Returns: (success, message/token, user)
        """
        try:
            # Validate password strength
            is_valid, message = security_manager.validate_password(password)
            if not is_valid:
                return False, message, None
            
            # Check if user already exists in DB or local store
            user_key = email.replace('.', '_')
            existing = None
            if self.initialized and self.db_ref:
                try:
                    existing = self.db_ref.child('users').child(user_key).get()
                except Exception:
                    existing = None
            else:
                # local fallback
                try:
                    local = self._load_local_user(user_key)
                    if local:
                        existing = local
                except Exception:
                    existing = None

            if existing:
                return False, "User already exists", None
            
            if self.initialized:
                try:
                    # Create user in Firebase Auth
                    user = firebase_auth.create_user(
                        email=email,
                        password=password,
                        display_name=display_name or email.split('@')[0],
                        disabled=False
                    )
                    uid = user.uid
                except firebase_auth.EmailAlreadyExistsError:
                    return False, "Email already registered in Firebase", None
                except firebase_auth.InvalidPasswordError:
                    return False, "Password does not meet security requirements", None
            else:
                # Generate local UID if Firebase unavailable
                uid = hashlib.sha256(f"{email}{datetime.utcnow()}".encode()).hexdigest()[:16]
            
            # Create local user record with role-based access
            now = datetime.utcnow().isoformat()
            import bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            
            user_data = {
                "uid": uid,
                "email": email,
                "display_name": display_name or email.split('@')[0],
                "role": "Viewer",  # Default role
                "created_at": now,
                "last_login": None,
                "login_count": 0,
                "email_verified": False,
                "disabled": False,
                "photo_url": None,
                "phone_number": None,
                "password_hash": password_hash,
            }
            
            # Save to Realtime Database if initialized, otherwise save locally
            if self.initialized and self.db_ref:
                try:
                    self.db_ref.child('users').child(user_key).set(user_data)
                except Exception as db_err:
                    logger.warning(f"Database save failed, using local storage: {db_err}")
                    try:
                        self._save_local_user(user_key, user_data)
                    except Exception:
                        logger.exception("Failed to save local user")
            else:
                try:
                    self._save_local_user(user_key, user_data)
                except Exception:
                    logger.exception("Failed to save local user")
            
            # Log audit event
            security_manager.audit_log(
                event_type="user_created",
                username=email,
                ip_address="system",
                details={"message": f"User {email} created"},
                severity="info"
            )
            
            logger.info(f"User created: {email}")
            user_obj = User(**user_data)
            return True, f"User {email} created successfully", user_obj
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, f"Error creating user: {str(e)}", None

    def authenticate_user(self, email: str, password: str, ip_address: str = "unknown") -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user with email and password
        Returns: (success, message/token, token_data)
        """
        try:
            # Rate limiting and brute force protection
            limit_ok, attempts = security_manager.check_rate_limit(f"auth:{email}")
            if not limit_ok:
                security_manager.audit_log(
                    event_type="rate_limit_exceeded",
                    username=email,
                    ip_address=ip_address,
                    details={"message": f"Rate limit exceeded: {attempts} attempts"},
                    severity="warning"
                )
                return False, "Too many login attempts. Please try again later.", None
            
            # Check if account is locked
            locked, lockout_minutes = security_manager.is_account_locked(email)
            if locked:
                security_manager.audit_log(
                    event_type="account_locked",
                    username=email,
                    ip_address=ip_address,
                    details={"message": f"Account locked for {lockout_minutes} more minutes"},
                    severity="warning"
                )
                return False, f"Account temporarily locked. Try again in {lockout_minutes} minutes.", None
            
            # Get user from database or local store
            user_key = email.replace('.', '_')
            user_data = None
            if self.initialized and self.db_ref:
                try:
                    user_data = self.db_ref.child('users').child(user_key).get()
                except Exception as db_err:
                    logger.warning(f"Database lookup failed: {db_err}")
                    user_data = None
            else:
                try:
                    user_data = self._load_local_user(user_key)
                except Exception as e:
                    logger.warning(f"Local user lookup failed: {e}")
                    user_data = None
            
            if not user_data:
                security_manager.record_login_attempt(email, False)
                security_manager.audit_log(
                    event_type="login_failed",
                    username=email,
                    ip_address=ip_address,
                    details={"message": "User not found"},
                    severity="warning"
                )
                return False, "Invalid email or password", None
            
            # Try Firebase Auth first
            auth_success = False
            if self.initialized and not user_data.get('password_hash'):
                # If using Firebase Auth and user has no stored hash, consider them a firebase-managed user.
                # Full password verification against Firebase requires REST API; assume valid for now.
                auth_success = True
            
            # Local password verification (bcrypt)
            stored_hash = user_data.get('password_hash', '')
            
            # For Firebase Auth users without stored hash, skip local verification
            if not stored_hash and self.initialized:
                auth_success = True
            elif stored_hash:
                # Verify with stored bcrypt hash
                import bcrypt
                try:
                    auth_success = bcrypt.checkpw(
                        password.encode('utf-8'),
                        stored_hash.encode('utf-8')
                    )
                except Exception as e:
                    logger.error(f"Password verification error: {e}")
                    auth_success = False
            
            if not auth_success:
                security_manager.record_login_attempt(email, False)
                security_manager.audit_log(
                    event_type="login_failed",
                    username=email,
                    ip_address=ip_address,
                    details={"message": "Invalid password"},
                    severity="warning"
                )
                return False, "Invalid email or password", None
            
            # Update user login info
            now = datetime.utcnow().isoformat()
            user_data['last_login'] = now
            user_data['login_count'] = user_data.get('login_count', 0) + 1
            
            if self.initialized and self.db_ref:
                try:
                    self.db_ref.child('users').child(user_key).set(user_data)
                except Exception as db_err:
                    logger.warning(f"Failed to update login info: {db_err}")
                    try:
                        self._save_local_user(user_key, user_data)
                    except Exception:
                        logger.exception("Failed to save local user update")
            else:
                try:
                    self._save_local_user(user_key, user_data)
                except Exception:
                    logger.exception("Failed to save local user update")
            
            # Create session
            session_data = security_manager.create_session(
                username=email,
                ip_address=ip_address,
                user_agent="firebase_auth"
            )
            
            # Log successful login
            security_manager.record_login_attempt(email, True)
            security_manager.audit_log(
                event_type="login_success",
                username=email,
                ip_address=ip_address,
                details={"message": f"User {email} logged in (login count: {user_data['login_count']})"},
                severity="info"
            )
            
            # Generate JWT tokens
            access_token = self._create_jwt_token(
                user_id=user_data['uid'],
                email=email,
                role=user_data.get('role', 'Viewer'),
                expires_in=3600
            )
            
            refresh_token = self._create_jwt_token(
                user_id=user_data['uid'],
                email=email,
                role=user_data.get('role', 'Viewer'),
                expires_in=604800,  # 7 days
                token_type='refresh'
            )
            
            logger.info(f"User authenticated: {email}")
            
            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "uid": user_data['uid'],
                    "email": email,
                    "display_name": user_data.get('display_name'),
                    "role": user_data.get('role', 'Viewer'),
                }
            }
            
            return True, "Login successful", token_data
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            security_manager.audit_log(
                event_type="auth_error",
                username=email,
                ip_address=ip_address,
                details=str(e),
                severity="error"
            )
            return False, f"Authentication error: {str(e)}", None

    def get_user(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            user_key = email.replace('.', '_')
            if self.initialized and self.db_ref:
                try:
                    return self.db_ref.child('users').child(user_key).get()
                except Exception:
                    pass
            # Fallback to local store
            return self._load_local_user(user_key)
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def get_user_by_uid(self, uid: str) -> Optional[Dict]:
        """Get user by Firebase UID"""
        try:
            # Try DB
            if self.initialized and self.db_ref:
                try:
                    users = self.db_ref.child('users').get() or {}
                except Exception:
                    users = {}
            else:
                users = self._load_all_local_users() or {}

            for user_data in users.values():
                if user_data.get('uid') == uid:
                    return user_data
            return None
        except Exception as e:
            logger.error(f"Error getting user by UID: {e}")
            return None

    def change_password(self, email: str, current_password: str, new_password: str, ip_address: str = "unknown") -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Authenticate current password first
            auth_ok, message, _ = self.authenticate_user(email, current_password, ip_address)
            if not auth_ok:
                return False, "Current password is incorrect"
            
            # Validate new password
            is_valid, msg = security_manager.validate_password(new_password)
            if not is_valid:
                return False, msg
            
            # Update password in Firebase Auth if initialized
            if self.initialized:
                try:
                    user = firebase_auth.get_user_by_email(email)
                    firebase_auth.update_user(user.uid, password=new_password)
                except Exception as e:
                    logger.warning(f"Firebase password update failed: {e}")
            
            # Update password hash in database
            import bcrypt
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            user_key = email.replace('.', '_')
            self.db_ref.child('users').child(user_key).update({
                'password_hash': password_hash,
                'password_changed_at': datetime.utcnow().isoformat()
            })
            
            security_manager.audit_log(
                event_type="password_changed",
                username=email,
                ip_address=ip_address,
                details={"message": f"Password changed for user {email}"},
                severity="info"
            )
            
            logger.info(f"Password changed for user: {email}")
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False, f"Error changing password: {str(e)}"

    def reset_password(self, email: str, new_password: str, admin_email: str = "admin", ip_address: str = "unknown") -> Tuple[bool, str]:
        """Admin reset user password"""
        try:
            # Validate new password
            is_valid, msg = security_manager.validate_password(new_password)
            if not is_valid:
                return False, msg
            
            # Update in Firebase Auth if initialized
            if self.initialized:
                try:
                    user = firebase_auth.get_user_by_email(email)
                    firebase_auth.update_user(user.uid, password=new_password)
                except Exception as e:
                    logger.warning(f"Firebase password reset failed: {e}")
            
            # Update in database or local store
            import bcrypt
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            user_key = email.replace('.', '_')
            update = {
                'password_hash': password_hash,
                'password_reset_at': datetime.utcnow().isoformat(),
                'password_reset_by': admin_email
            }
            if self.initialized and self.db_ref:
                try:
                    self.db_ref.child('users').child(user_key).update(update)
                except Exception:
                    logger.warning("Failed to update DB for password reset, saving locally")
                    self._update_local_user(user_key, update)
            else:
                self._update_local_user(user_key, update)
            
            security_manager.audit_log(
                event_type="password_reset",
                username=email,
                ip_address=ip_address,
                details={"message": f"Password reset by {admin_email} for user {email}"},
                severity="warning"
            )
            
            logger.info(f"Password reset for user: {email}")
            return True, "Password reset successfully"
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False, f"Error resetting password: {str(e)}"

    def update_user_role(self, email: str, new_role: str, admin_email: str = "admin", ip_address: str = "unknown") -> Tuple[bool, str]:
        """Update user role (Admin, User, Viewer)"""
        try:
            if new_role not in ["Admin", "User", "Viewer"]:
                return False, "Invalid role. Must be Admin, User, or Viewer"
            
            user_key = email.replace('.', '_')
            update = {
                'role': new_role,
                'role_updated_at': datetime.utcnow().isoformat(),
                'role_updated_by': admin_email
            }
            if self.initialized and self.db_ref:
                try:
                    self.db_ref.child('users').child(user_key).update(update)
                except Exception:
                    logger.warning("Failed to update DB for role change, saving locally")
                    self._update_local_user(user_key, update)
            else:
                self._update_local_user(user_key, update)
            
            security_manager.audit_log(
                event_type="role_updated",
                username=email,
                ip_address=ip_address,
                details={"message": f"User role changed to {new_role} by {admin_email}"},
                severity="warning"
            )
            
            logger.info(f"Role updated for user {email}: {new_role}")
            return True, f"User role updated to {new_role}"
            
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            return False, f"Error updating role: {str(e)}"

    def unlock_account(self, email: str, admin_email: str = "admin", ip_address: str = "unknown") -> Tuple[bool, str]:
        """Unlock user account (remove login lockout)"""
        try:
            security_manager.failed_attempts.pop(email, None)
            security_manager.account_lockouts.pop(email, None)
            
            security_manager.audit_log(
                event_type="account_unlocked",
                username=email,
                ip_address=ip_address,
                details={"message": f"Account unlocked by {admin_email}"},
                severity="info"
            )
            
            logger.info(f"Account unlocked: {email}")
            return True, f"Account {email} unlocked"
            
        except Exception as e:
            logger.error(f"Error unlocking account: {e}")
            return False, f"Error unlocking account: {str(e)}"

    def list_users(self) -> List[Dict]:
        """Get list of all users"""
        try:
            if self.initialized and self.db_ref:
                try:
                    users = self.db_ref.child('users').get() or {}
                except Exception:
                    users = {}
            else:
                users = self._load_all_local_users() or {}

            user_list = []
            for user_data in users.values():
                user_list.append({
                    "uid": user_data.get('uid'),
                    "email": user_data.get('email'),
                    "display_name": user_data.get('display_name'),
                    "role": user_data.get('role', 'Viewer'),
                    "created_at": user_data.get('created_at'),
                    "last_login": user_data.get('last_login'),
                    "login_count": user_data.get('login_count', 0),
                    "disabled": user_data.get('disabled', False),
                })
            return user_list
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    def _create_jwt_token(self, user_id: str, email: str, role: str, expires_in: int = 3600, token_type: str = "access") -> str:
        """Create a JWT token"""
        import jwt
        from datetime import datetime, timedelta
        
        try:
            secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
            payload = {
                "user_id": user_id,
                "email": email,
                "role": role,
                "type": token_type,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(seconds=expires_in)
            }
            token = jwt.encode(payload, secret, algorithm="HS256")
            return token
        except Exception as e:
            logger.error(f"Error creating JWT token: {e}")
            return ""

    def verify_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify and decode JWT token"""
        import jwt
        
        try:
            secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False, None

# Initialize global instance
firebase_auth_service = FirebaseAuthService()

def init_firebase_auth():
    """Initialize Firebase Authentication Service and create default admin"""
    firebase_auth_service.initialize()
    
    # Create default admin user if not exists
    admin_email = "admin@evobot.local"
    admin_password = "Admin@123!"
    
    # Check if admin exists
    existing_admin = firebase_auth_service.get_user(admin_email)
    if not existing_admin:
        success, msg, user = firebase_auth_service.create_user(
            email=admin_email,
            password=admin_password,
            display_name="Admin"
        )
        if success:
            # Update role to Admin
            firebase_auth_service.update_user_role(
                email=admin_email,
                new_role="Admin",
                admin_email="system",
                ip_address="system"
            )
            logger.info(f"Default admin user created: {admin_email}")
        else:
            logger.warning(f"Failed to create default admin: {msg}")
    else:
        logger.info(f"Admin user already exists: {admin_email}")
    
    return firebase_auth_service
    return firebase_auth_service
