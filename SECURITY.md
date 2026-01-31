# EvoBot Security Implementation Guide

## Overview

This document describes the comprehensive security features implemented in the EvoBot trading system. The backend provides enterprise-grade authentication, authorization, and audit logging capabilities.

## Table of Contents

1. [Authentication](#authentication)
2. [Authorization & Role-Based Access Control](#authorization--role-based-access-control)
3. [Password Security](#password-security)
4. [Account Lockout Protection](#account-lockout-protection)
5. [Session Management](#session-management)
6. [Audit Logging](#audit-logging)
7. [Rate Limiting](#rate-limiting)
8. [Admin Controls](#admin-controls)
9. [Security Best Practices](#security-best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Authentication

### JWT Token-Based Authentication

The system uses JWT (JSON Web Tokens) for stateless authentication:

- **Access Token**: Short-lived token (24 hours by default) for API requests
- **Refresh Token**: Long-lived token (7 days) for obtaining new access tokens
- **Token Expiry**: Configurable via `TOKEN_EXPIRE_MINUTES` environment variable

### Login Process

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "Password@123"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "username": "admin",
    "email": "admin@evobot.local",
    "role": "admin",
    "permissions": ["*"]
  }
}
```

### Token Refresh

```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Logout

```bash
POST /api/auth/logout
Authorization: Bearer <access_token>
```

Logging out blacklists your current token, preventing further API access with that token.

---

## Authorization & Role-Based Access Control

### Available Roles

#### 1. **Admin** (Level: 100)
- **Permissions**: All (`*`)
- **Capabilities**:
  - Full system access
  - User management (create, edit, delete)
  - Role assignment
  - Account unlocking
  - Password resets
  - View audit logs
  - Access security statistics

#### 2. **User** (Level: 50)
- **Permissions**: `trade:view`, `trade:execute`, `dashboard:view`, `settings:view`
- **Capabilities**:
  - View trades
  - Execute trading operations
  - View dashboard
  - View/change own settings

#### 3. **Viewer** (Level: 10)
- **Permissions**: `trade:view`, `dashboard:view`
- **Capabilities**:
  - View-only access to trades
  - View dashboard

### Protected Endpoints

All API endpoints requiring authentication use the standard JWT Bearer token:

```bash
Authorization: Bearer <access_token>
```

---

## Password Security

### Password Policy

All passwords must meet these requirements:

- ✅ **Minimum 8 characters** long
- ✅ **At least one uppercase letter** (A-Z)
- ✅ **At least one lowercase letter** (a-z)
- ✅ **At least one digit** (0-9)
- ✅ **At least one special character** (!@#$%^&*(),.?":{}|<>_-+=[]\/​)

### Strong Password Examples

✅ `SecurePass@123`
✅ `MyTrading!Bot2024`
✅ `Trading#4Ever`

❌ `password` (no uppercase, no special char, too simple)
❌ `Pass123` (no special character)
❌ `PASSWORD!` (no lowercase, no digit)

### Password Hashing

- Passwords are hashed using **bcrypt** with 12 salt rounds
- Original passwords are never stored or logged
- Comparison is performed securely to prevent timing attacks

### Changing Your Password

```bash
POST /api/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldPassword@123",
  "new_password": "NewPassword@456"
}
```

**Important**: Changing your password invalidates all other active sessions.

### Admin Password Reset

Admins can reset user passwords:

```bash
POST /api/admin/users/{username}/reset-password
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "new_password": "NewPassword@123"
}
```

---

## Account Lockout Protection

### Lockout Mechanism

- **Trigger**: 5 failed login attempts within 30 minutes
- **Duration**: 30 minutes (configurable)
- **Message**: User receives clear feedback on remaining lockout time
- **Admin Override**: Admins can manually unlock accounts

### Lockout States

```
Failed Attempt 1-4: "4 attempts remaining"
Failed Attempt 5: "Account locked for 30 minutes"
After Reset: Attempts counter resets to 0
```

### Manual Unlock

```bash
POST /api/admin/users/{username}/unlock
Authorization: Bearer <admin_token>
```

This endpoint:
- Resets failed login attempts to 0
- Clears any lockout timestamp
- Logs the unlock action to audit trail

---

## Session Management

### Session Tracking

Each login creates a session with:
- Unique session ID
- Login timestamp
- User IP address
- User agent (browser info)
- Active status

### View Your Sessions

```bash
GET /api/auth/sessions
Authorization: Bearer <access_token>

# Response
{
  "sessions": [
    {
      "session_id": "a1b2c3d4e5f6...",
      "username": "admin",
      "created_at": "2024-01-28T10:30:00",
      "last_activity": "2024-01-28T10:45:00",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "is_active": true
    }
  ]
}
```

### Token Blacklisting

When you logout, your token is added to a blacklist. This prevents:
- Token reuse after logout
- Unauthorized access with old tokens
- Session hijacking risks

---

## Audit Logging

### Logged Events

Every security-relevant event is logged:

| Event | Details |
|-------|---------|
| `login_success` | Successful login with username, IP |
| `login_failed` | Failed login attempt with reason |
| `account_locked` | Account locked due to failed attempts |
| `password_changed` | Password change with timestamp |
| `password_reset` | Admin password reset with actor |
| `logout` | Logout event |
| `session_created` | Session creation |
| `session_invalidated` | Session termination |
| `user_created` | New user created by admin |
| `user_deleted` | User deleted by admin |
| `user_status_changed` | Enable/disable user |
| `user_role_changed` | Role assignment changed |
| `token_blacklisted` | Token invalidated |
| `rate_limit_exceeded` | Rate limit violation |

### Access Audit Logs

**Admin Only:**

```bash
GET /api/admin/security/audit?limit=100&event_type=login_failed&username=admin
Authorization: Bearer <admin_token>

# Response
{
  "logs": [
    {
      "timestamp": "2024-01-28T10:15:30",
      "event_type": "login_failed",
      "username": "admin",
      "ip_address": "192.168.1.100",
      "severity": "warning",
      "details": {
        "attempts": 2,
        "reason": "invalid_password"
      }
    }
  ],
  "count": 1
}
```

### Audit Log Retention

- **In-Memory**: Last 10,000 events (current session)
- **Persistent**: All events written to `logs/audit.log`
- **Format**: JSON, one event per line
- **Location**: `/home/ubuntu/personal/evobot/logs/audit.log`

---

## Rate Limiting

### Rate Limit Policy

- **Default**: 100 requests per 60 seconds per IP
- **Applies To**: All non-static-file endpoints
- **Response**: HTTP 429 (Too Many Requests)

### Rate Limit Headers

```
X-RateLimit-Remaining: 42
Retry-After: 60
```

### Examples

✅ 100 API calls in 60 seconds = OK
❌ 101 API calls in 60 seconds = 429 error, retry after 60 seconds

---

## Admin Controls

### User Management Dashboard

Access at: `https://your-domain/admin`

**Requirements**: Admin role

### Available Actions

#### Create User
```bash
POST /api/admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass@123",
  "role": "viewer"
}
```

#### List All Users
```bash
GET /api/admin/users
Authorization: Bearer <admin_token>
```

#### Toggle User Status
```bash
PUT /api/admin/users/{username}/toggle
Authorization: Bearer <admin_token>
```

#### Update User Role
```bash
PUT /api/admin/users/{username}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "user"
}
```

#### Delete User
```bash
DELETE /api/admin/users/{username}
Authorization: Bearer <admin_token>
```

#### Reset User Password
```bash
POST /api/admin/users/{username}/reset-password
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "new_password": "NewPassword@123"
}
```

#### Unlock Locked Account
```bash
POST /api/admin/users/{username}/unlock
Authorization: Bearer <admin_token>
```

### Security Statistics

View real-time security metrics:

```bash
GET /api/admin/security/stats
Authorization: Bearer <admin_token>

# Response
{
  "active_sessions": 5,
  "locked_accounts": 2,
  "blacklisted_tokens": 127,
  "login_attempts_24h": 342,
  "failed_logins_24h": 12,
  "security_events_24h": 8
}
```

---

## Security Best Practices

### For Users

1. **Use Strong Passwords**
   - Follow password policy requirements
   - Use unique passwords for each account
   - Never share your password

2. **Protect Your Token**
   - Never expose tokens in logs or debug output
   - Store refresh tokens securely
   - Use HTTPS only (never HTTP)

3. **Regular Logout**
   - Logout when finished using the dashboard
   - Logout on shared/public computers
   - Logout before closing the browser

4. **Session Awareness**
   - Monitor your active sessions regularly
   - Logout from unknown devices
   - Report suspicious activity to admin

### For Administrators

1. **Regular Audits**
   - Review audit logs weekly
   - Monitor failed login attempts
   - Check for unusual account creation
   - Track role changes

2. **Account Management**
   - Disable unused accounts
   - Reset passwords for compromised accounts
   - Unlock legitimate locked accounts promptly
   - Assign minimum necessary roles

3. **Security Updates**
   - Keep the system updated
   - Review security policies regularly
   - Update secrets/keys periodically
   - Backup audit logs regularly

4. **Monitoring**
   - Watch rate limit violations
   - Track active sessions
   - Monitor for brute force attempts
   - Alert on critical events

### Environmental Security

1. **Secret Key Management**
   - Change JWT_SECRET_KEY in production
   - Store in secure environment variables
   - Don't commit secrets to git
   - Rotate keys periodically

2. **CORS Configuration**
   - Set specific allowed origins in production
   - Avoid allowing all origins (`*`)
   - Use environment variables

3. **HTTPS/TLS**
   - Always use HTTPS in production
   - Use valid SSL certificates
   - Enable HSTS headers
   - Disable SSL/TLS versions < 1.2

---

## Troubleshooting

### Account Locked

**Problem**: "Account locked due to too many failed attempts"

**Solution**:
1. Wait 30 minutes for automatic unlock, OR
2. Admin can manually unlock:
   ```bash
   POST /api/admin/users/{username}/unlock
   ```

### Token Expired

**Problem**: "Token expired" error

**Solution**:
1. Use refresh token:
   ```bash
   POST /api/auth/refresh
   ```
2. If no refresh token, login again

### Password Validation Failed

**Problem**: "Password must contain uppercase letter" etc.

**Solution**: Ensure password meets all requirements:
- ✅ 8+ characters
- ✅ Uppercase letter
- ✅ Lowercase letter
- ✅ Digit
- ✅ Special character

### Rate Limited

**Problem**: "Too many requests" / HTTP 429

**Solution**:
- Wait for rate limit window to reset (60 seconds)
- Check X-RateLimit-Remaining header
- Respect Retry-After header
- Optimize API calls to reduce frequency

### Audit Log Issues

**Problem**: Audit logs not visible in admin panel

**Solution**:
1. Verify admin role: `GET /api/auth/me`
2. Check audit log file exists: `cat logs/audit.log`
3. Verify file permissions: `ls -la logs/`
4. Restart dashboard if needed

---

## Compliance & Standards

### Implemented Standards

- **OWASP Top 10**: Protection against common vulnerabilities
- **JWT**: RFC 7519 compliant tokens
- **Bcrypt**: Industry-standard password hashing
- **Rate Limiting**: DDoS protection
- **Audit Logging**: Comprehensive event tracking

### Security Checklist

- [x] Secure password hashing (bcrypt-12)
- [x] JWT token authentication
- [x] Token refresh mechanism
- [x] Token blacklisting on logout
- [x] Account lockout protection
- [x] Session management
- [x] Rate limiting
- [x] Comprehensive audit logging
- [x] Role-based access control
- [x] Password policy enforcement
- [x] Admin controls
- [x] Security statistics dashboard

---

## Configuration

### Environment Variables

```bash
# Security
JWT_SECRET_KEY=your-secret-key-here
TOKEN_EXPIRE_MINUTES=1440  # 24 hours
ADMIN_PASSWORD=Admin@123!

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting (optional)
# Rate limit: 100 requests per 60 seconds per IP
```

### Security Config (core/security.py)

```python
SECURITY_CONFIG = {
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30,
    "session_timeout_minutes": 60 * 24,  # 24 hours
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digit": True,
    "password_require_special": True,
    "rate_limit_requests": 100,
    "rate_limit_window_seconds": 60,
}
```

---

## Support

For security issues or questions:

1. **Documentation**: Review this guide and inline comments
2. **Audit Logs**: Check `/logs/audit.log` for details
3. **Admin Panel**: Visit `/admin` to manage security settings
4. **Logging**: Check application logs for errors

---

**Last Updated**: January 28, 2024
**Version**: 2.0.0
**Status**: Production Ready
