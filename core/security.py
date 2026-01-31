"""
Advanced Security Module for EvoBot Trading System
Provides comprehensive security features including:
- Rate limiting
- Session management
- Audit logging
- Password policies
- IP-based security
"""
import os
import json
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set, Tuple
from collections import defaultdict
import threading
import logging

logger = logging.getLogger("evobot.security")

# Security configuration
SECURITY_CONFIG = {
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30,
    "session_timeout_minutes": 60 * 24,  # 24 hours
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digit": True,
    "password_require_special": True,
    "rate_limit_requests": 500,
    "rate_limit_window_seconds": 60,
    "csrf_token_expiry_minutes": 60,
}


class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._login_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._locked_accounts: Dict[str, datetime] = {}
        self._active_sessions: Dict[str, dict] = {}
        self._blacklisted_tokens: Set[str] = set()
        self._rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self._csrf_tokens: Dict[str, dict] = {}
        self._audit_log: List[dict] = []
        self._data_file = "data/security_data.json"
        self._audit_file = "logs/audit.log"
        self._load_data()
    
    def _load_data(self):
        """Load persisted security data"""
        try:
            if os.path.exists(self._data_file):
                with open(self._data_file, 'r') as f:
                    data = json.load(f)
                    self._locked_accounts = {
                        k: datetime.fromisoformat(v) 
                        for k, v in data.get("locked_accounts", {}).items()
                    }
                    self._blacklisted_tokens = set(data.get("blacklisted_tokens", []))
        except Exception as e:
            logger.error(f"Failed to load security data: {e}")
    
    def _save_data(self):
        """Persist security data"""
        try:
            os.makedirs(os.path.dirname(self._data_file), exist_ok=True)
            data = {
                "locked_accounts": {
                    k: v.isoformat() 
                    for k, v in self._locked_accounts.items()
                },
                "blacklisted_tokens": list(self._blacklisted_tokens)[-1000:]  # Keep last 1000
            }
            with open(self._data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save security data: {e}")
    
    def audit_log(self, event_type: str, username: str = None, ip_address: str = None, 
                  details: dict = None, severity: str = "info"):
        """Log security events"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "username": username,
            "ip_address": ip_address,
            "details": details or {},
            "severity": severity
        }
        
        with self._lock:
            self._audit_log.append(event)
            # Keep only last 10000 events in memory
            if len(self._audit_log) > 10000:
                self._audit_log = self._audit_log[-10000:]
        
        # Write to audit file
        try:
            os.makedirs(os.path.dirname(self._audit_file), exist_ok=True)
            with open(self._audit_file, 'a') as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
        
        # Log critical events
        if severity in ["warning", "critical"]:
            logger.warning(f"Security Event [{severity}]: {event_type} - {details}")
    
    def get_audit_logs(self, limit: int = 100, event_type: str = None, 
                       username: str = None) -> List[dict]:
        """Get recent audit logs with optional filtering"""
        logs = self._audit_log.copy()
        
        if event_type:
            logs = [l for l in logs if l["event_type"] == event_type]
        if username:
            logs = [l for l in logs if l["username"] == username]
        
        return logs[-limit:]
    
    # Password Policy
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password against security policy"""
        config = SECURITY_CONFIG
        
        if len(password) < config["password_min_length"]:
            return False, f"Password must be at least {config['password_min_length']} characters"
        
        if config["password_require_uppercase"] and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if config["password_require_lowercase"] and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if config["password_require_digit"] and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if config["password_require_special"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password meets requirements"
    
    # Login Attempt Tracking
    def record_login_attempt(self, username: str, success: bool, ip_address: str = None):
        """Record login attempt and handle lockouts"""
        with self._lock:
            now = datetime.utcnow()
            
            if success:
                # Clear failed attempts on successful login
                self._login_attempts[username] = []
                if username in self._locked_accounts:
                    del self._locked_accounts[username]
                self.audit_log("login_success", username, ip_address)
            else:
                self._login_attempts[username].append(now)
                # Keep only recent attempts
                cutoff = now - timedelta(minutes=30)
                self._login_attempts[username] = [
                    t for t in self._login_attempts[username] if t > cutoff
                ]
                
                # Check for lockout
                if len(self._login_attempts[username]) >= SECURITY_CONFIG["max_login_attempts"]:
                    self._locked_accounts[username] = now + timedelta(
                        minutes=SECURITY_CONFIG["lockout_duration_minutes"]
                    )
                    self.audit_log(
                        "account_locked", username, ip_address,
                        {"reason": "too_many_failed_attempts"},
                        severity="warning"
                    )
                else:
                    self.audit_log(
                        "login_failed", username, ip_address,
                        {"attempts": len(self._login_attempts[username])}
                    )
            
            self._save_data()
    
    def is_account_locked(self, username: str) -> Tuple[bool, Optional[int]]:
        """Check if account is locked and return remaining lockout time"""
        with self._lock:
            if username not in self._locked_accounts:
                return False, None
            
            lockout_until = self._locked_accounts[username]
            now = datetime.utcnow()
            
            if now >= lockout_until:
                del self._locked_accounts[username]
                self._save_data()
                return False, None
            
            remaining = int((lockout_until - now).total_seconds())
            return True, remaining
    
    def get_failed_attempts(self, username: str) -> int:
        """Get number of recent failed login attempts"""
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=30)
            attempts = [t for t in self._login_attempts.get(username, []) if t > cutoff]
            return len(attempts)
    
    # Session Management
    def create_session(self, username: str, token: str = None, ip_address: str = None, 
                       user_agent: str = None) -> dict:
        """Create a new session"""
        session_id = secrets.token_hex(16)
        now = datetime.utcnow()
        
        session = {
            "session_id": session_id,
            "username": username,
            "token_hash": hashlib.sha256(token.encode()).hexdigest() if token else None,
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "is_active": True
        }
        
        with self._lock:
            self._active_sessions[session_id] = session
        
        self.audit_log("session_created", username, ip_address, {"session_id": session_id})
        return session

    # Backwards-compatible public accessors for external modules
    @property
    def failed_attempts(self) -> Dict[str, List[datetime]]:
        return self._login_attempts

    @property
    def account_lockouts(self) -> Dict[str, datetime]:
        return self._locked_accounts

    @property
    def active_sessions(self) -> Dict[str, dict]:
        return self._active_sessions
    
    def get_user_sessions(self, username: str) -> List[dict]:
        """Get all active sessions for a user"""
        with self._lock:
            return [
                {k: v for k, v in s.items() if k != "token_hash"}
                for s in self._active_sessions.values()
                if s["username"] == username and s["is_active"]
            ]
    
    def invalidate_session(self, session_id: str, username: str = None):
        """Invalidate a specific session"""
        with self._lock:
            if session_id in self._active_sessions:
                session = self._active_sessions[session_id]
                session["is_active"] = False
                self.audit_log(
                    "session_invalidated", 
                    username or session["username"],
                    details={"session_id": session_id}
                )
    
    def invalidate_all_sessions(self, username: str):
        """Invalidate all sessions for a user"""
        with self._lock:
            for session in self._active_sessions.values():
                if session["username"] == username:
                    session["is_active"] = False
        
        self.audit_log("all_sessions_invalidated", username)
    
    def update_session_activity(self, session_id: str):
        """Update last activity timestamp for session"""
        with self._lock:
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    # Token Blacklisting
    def blacklist_token(self, token: str, username: str = None):
        """Add token to blacklist"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self._lock:
            self._blacklisted_tokens.add(token_hash)
            self._save_data()
        
        self.audit_log("token_blacklisted", username)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in self._blacklisted_tokens
    
    # Rate Limiting
    def check_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """Check if request is within rate limits
        Returns (allowed, remaining_requests)
        """
        with self._lock:
            now = datetime.utcnow()
            window = timedelta(seconds=SECURITY_CONFIG["rate_limit_window_seconds"])
            cutoff = now - window
            
            # Clean old entries
            self._rate_limits[identifier] = [
                t for t in self._rate_limits[identifier] if t > cutoff
            ]
            
            current_count = len(self._rate_limits[identifier])
            max_requests = SECURITY_CONFIG["rate_limit_requests"]
            
            if current_count >= max_requests:
                return False, 0
            
            self._rate_limits[identifier].append(now)
            return True, max_requests - current_count - 1
    
    # CSRF Protection
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        token = secrets.token_hex(32)
        expiry = datetime.utcnow() + timedelta(
            minutes=SECURITY_CONFIG["csrf_token_expiry_minutes"]
        )
        
        with self._lock:
            self._csrf_tokens[token] = {
                "session_id": session_id,
                "expiry": expiry.isoformat()
            }
        
        return token
    
    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        with self._lock:
            if token not in self._csrf_tokens:
                return False
            
            data = self._csrf_tokens[token]
            expiry = datetime.fromisoformat(data["expiry"])
            
            if datetime.utcnow() > expiry:
                del self._csrf_tokens[token]
                return False
            
            if data["session_id"] != session_id:
                return False
            
            return True
    
    # Security Statistics
    def get_security_stats(self) -> dict:
        """Get security statistics for admin dashboard"""
        with self._lock:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            
            recent_logs = [
                l for l in self._audit_log 
                if datetime.fromisoformat(l["timestamp"]) > last_24h
            ]
            
            return {
                "active_sessions": len([
                    s for s in self._active_sessions.values() if s["is_active"]
                ]),
                "locked_accounts": len(self._locked_accounts),
                "blacklisted_tokens": len(self._blacklisted_tokens),
                "login_attempts_24h": len([
                    l for l in recent_logs if l["event_type"] in ["login_success", "login_failed"]
                ]),
                "failed_logins_24h": len([
                    l for l in recent_logs if l["event_type"] == "login_failed"
                ]),
                "security_events_24h": len([
                    l for l in recent_logs if l["severity"] in ["warning", "critical"]
                ])
            }
    
    def unlock_account(self, username: str, admin_username: str = None):
        """Manually unlock a locked account"""
        with self._lock:
            if username in self._locked_accounts:
                del self._locked_accounts[username]
            self._login_attempts[username] = []
            self._save_data()
        
        self.audit_log(
            "account_unlocked", username,
            details={"unlocked_by": admin_username},
            severity="info"
        )


# Global security manager instance
security_manager = SecurityManager()
