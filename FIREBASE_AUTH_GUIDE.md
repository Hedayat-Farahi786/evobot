# Firebase Authentication Implementation

## Overview

EvoBot now uses **enterprise-grade Firebase Authentication** integrated with the FastAPI dashboard. This provides:

- **Email/Password Authentication** - Secure user registration and login
- **Firebase Admin SDK** - Server-side authentication management
- **JWT Tokens** - Access tokens (1 hour) and refresh tokens (7 days)
- **Role-Based Access Control** - Admin, User, Viewer roles
- **Account Lockout Protection** - 5 failed attempts trigger 30-min lockout
- **Rate Limiting** - 100 requests/60 seconds per IP
- **Audit Logging** - Complete audit trail in JSON format
- **Session Tracking** - IP address and user agent logging
- **Firebase Realtime Database** - User data persistence

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EvoBot Dashboard (FastAPI)                   │
├─────────────────────────────────────────────────────────────────┤
│  Login Endpoint  │  Admin Endpoints  │  Security Endpoints      │
├────────────────┬──────────────────┬─────────────────────────────┤
│ FirebaseAuthService (core/firebase_auth.py)                     │
│  - User creation & registration                                 │
│  - Email/password authentication                                │
│  - Token management (JWT)                                       │
│  - Password reset & change                                      │
│  - Role management                                              │
├─────────────────────────────────────────────────────────────────┤
│             Firebase Authentication & Database                  │
│  - Firebase Auth (email/password users)                         │
│  - Realtime Database (user profiles, roles)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Configure Environment Variables

Add to `.env`:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=evobot-8
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@evobot-8.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789012345678901
FIREBASE_DATABASE_URL=https://evobot-8-default-rtdb.europe-west1.firebasedatabase.app

# JWT Secret
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Security Settings
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=30
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### 2. Get Firebase Service Account Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project `evobot-8`
3. Navigate to **Project Settings** (gear icon)
4. Go to **Service Accounts** tab
5. Click **Generate New Private Key**
6. Download JSON file
7. Extract the credentials and add to `.env`

### 3. Install Requirements

```bash
pip install firebase-admin PyJWT bcrypt
```

Or use provided scripts:
```bash
pip install -r requirements_firebase.txt
```

## API Endpoints

### Authentication Endpoints

#### 1. Sign Up (Register)
```bash
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "display_name": "John Doe"
}

Response: 201 Created
{
  "message": "User user@example.com created successfully",
  "user": {
    "uid": "firebase-uid-123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "Viewer"
  }
}
```

#### 2. Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "uid": "firebase-uid-123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "Viewer"
  }
}
```

#### 3. Refresh Token
```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response: 200 OK
{
  "access_token": "new-access-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. Get Current User
```bash
GET /api/auth/me
Authorization: Bearer <access_token>

Response: 200 OK
{
  "uid": "firebase-uid-123",
  "email": "user@example.com",
  "display_name": "John Doe",
  "role": "Viewer",
  "created_at": "2024-01-28T10:30:00",
  "last_login": "2024-01-28T14:45:00",
  "login_count": 5
}
```

#### 5. Change Password
```bash
POST /api/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}

Response: 200 OK
{
  "message": "Password changed successfully"
}
```

#### 6. Logout
```bash
POST /api/auth/logout
Authorization: Bearer <access_token>

Response: 200 OK
{
  "message": "Logged out successfully"
}
```

### Admin Endpoints

#### 1. List All Users
```bash
GET /api/admin/users
Authorization: Bearer <admin_token>

Response: 200 OK
{
  "users": [
    {
      "uid": "firebase-uid-123",
      "email": "user@example.com",
      "display_name": "John Doe",
      "role": "User",
      "created_at": "2024-01-28T10:30:00",
      "last_login": "2024-01-28T14:45:00",
      "login_count": 5,
      "disabled": false
    }
  ]
}
```

#### 2. Create User (Admin)
```bash
POST /api/admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "TempPass123!",
  "display_name": "New User"
}

Response: 201 Created
{
  "message": "User newuser@example.com created successfully",
  "user": {
    "uid": "firebase-uid-456",
    "email": "newuser@example.com",
    "display_name": "New User",
    "role": "Viewer"
  }
}
```

#### 3. Reset User Password
```bash
POST /api/admin/users/{email}/reset-password
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "user@example.com",
  "new_password": "ResetPass123!"
}

Response: 200 OK
{
  "message": "Password reset successfully"
}
```

#### 4. Update User Role
```bash
POST /api/admin/users/{email}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "Admin"  // Admin, User, or Viewer
}

Response: 200 OK
{
  "message": "User role updated to Admin"
}
```

#### 5. Unlock Account
```bash
POST /api/admin/users/{email}/unlock
Authorization: Bearer <admin_token>

Response: 200 OK
{
  "message": "Account user@example.com unlocked"
}
```

#### 6. Security Statistics
```bash
GET /api/admin/security/stats
Authorization: Bearer <admin_token>

Response: 200 OK
{
  "users": 5,
  "failed_attempts": 2,
  "locked_accounts": 0,
  "active_sessions": 3,
  "timestamp": "2024-01-28T15:00:00"
}
```

#### 7. Audit Logs
```bash
GET /api/admin/security/audit?skip=0&limit=100
Authorization: Bearer <admin_token>

Response: 200 OK
{
  "logs": [
    {
      "event": "login_success",
      "username": "user@example.com",
      "ip_address": "192.168.1.100",
      "timestamp": "2024-01-28T14:45:00",
      "details": "User user@example.com logged in",
      "severity": "info"
    }
  ],
  "total": 342
}
```

## Password Policy

Passwords must meet these requirements:
- **Minimum 8 characters**
- **At least one uppercase letter** (A-Z)
- **At least one lowercase letter** (a-z)
- **At least one digit** (0-9)
- **At least one special character** (!@#$%^&*)

Example valid passwords:
- `SecurePass123!`
- `EvoBot@2024`
- `Trading#Bot456`

## Security Features

### Account Lockout
- **5 failed login attempts** trigger automatic account lockout
- **30-minute lockout period** (configurable)
- Admin can manually unlock accounts
- Lockout counter resets after successful login

### Rate Limiting
- **100 requests per 60 seconds** per IP address
- Prevents brute force attacks
- Applies to all endpoints except static files
- Returns `429 Too Many Requests` when limit exceeded

### Session Management
- **IP address tracking** - Sessions tied to specific IP
- **User agent logging** - Browser/client identification
- **Login timestamps** - Creation and last activity times
- **Session invalidation** - Automatic cleanup on logout

### Audit Logging
All security events logged to `logs/audit.log`:
```json
{
  "event": "login_success",
  "username": "user@example.com",
  "ip_address": "192.168.1.100",
  "timestamp": "2024-01-28T14:45:00.123456",
  "details": "User user@example.com logged in (login count: 5)",
  "severity": "info"
}
```

Event types:
- `user_created` - New user registered
- `login_success` - Successful authentication
- `login_failed` - Failed authentication attempt
- `password_changed` - Password updated by user
- `password_reset` - Password reset by admin
- `role_updated` - User role changed
- `account_unlocked` - Account unlocking
- `rate_limit_exceeded` - Rate limit triggered
- `auth_error` - Authentication system error

### Token Security
- **Access tokens**: 1-hour validity (3600 seconds)
- **Refresh tokens**: 7-day validity (604800 seconds)
- **JWT signing**: HS256 algorithm with secret key
- **Token claims**:
  - `user_id` - Firebase UID
  - `email` - User email
  - `role` - User role
  - `type` - access or refresh
  - `iat` - Issued at
  - `exp` - Expiration time

## Role-Based Access Control

### Admin Role
- Create, read, update, delete users
- Change user passwords and roles
- View security statistics
- Access audit logs
- Configure bot settings
- Full dashboard access

### User Role
- View own profile
- Change own password
- Access trading dashboard
- Create/modify trades
- View account statistics

### Viewer Role
- View own profile
- View account statistics (read-only)
- View trading history (read-only)
- Cannot modify any settings

## Database Schema

### Firebase Realtime Database

```
evobot-8/
├── users/
│   └── user_email/
│       ├── uid: string (Firebase UID)
│       ├── email: string
│       ├── display_name: string
│       ├── role: string (Admin|User|Viewer)
│       ├── created_at: ISO8601
│       ├── last_login: ISO8601
│       ├── login_count: number
│       ├── email_verified: boolean
│       ├── disabled: boolean
│       ├── photo_url: string
│       ├── phone_number: string
│       ├── password_hash: string (bcrypt)
│       ├── password_changed_at: ISO8601
│       ├── password_reset_at: ISO8601
│       └── password_reset_by: string
├── status/
│   ├── bot_running: boolean
│   ├── mt5_connected: boolean
│   ├── telegram_connected: boolean
│   └── timestamp: ISO8601
├── account/
│   ├── balance: number
│   ├── equity: number
│   ├── margin: number
│   ├── profit: number
│   └── timestamp: ISO8601
└── trades/
    └── trade_id/
        ├── symbol: string
        ├── direction: string
        ├── entry_price: number
        ├── status: string
        └── ...
```

## Troubleshooting

### "Firebase credentials not configured"
- Check `.env` file has all Firebase settings
- Verify `FIREBASE_PRIVATE_KEY` format (should include \n characters)
- Ensure service account JSON is valid

### "Invalid or expired token"
- Access tokens expire after 1 hour
- Use refresh token to get new access token
- Check token is in `Authorization: Bearer <token>` format

### "Account locked"
- Account has 5+ failed login attempts
- Wait 30 minutes or contact admin to unlock
- Check audit logs for failed attempts

### "Too many requests"
- Rate limit: 100 requests per 60 seconds
- Wait 60 seconds before retrying
- For automated testing, space requests appropriately

## Example: Complete Login Flow

```python
import requests

BASE_URL = "http://localhost:8080"

# 1. Sign up (optional)
signup = requests.post(f"{BASE_URL}/api/auth/signup", json={
    "email": "trader@example.com",
    "password": "TradingBot123!",
    "display_name": "Trader"
})
print(f"Signup: {signup.json()}")

# 2. Login
login = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "trader@example.com",
    "password": "TradingBot123!"
})
tokens = login.json()
access_token = tokens["access_token"]
print(f"Logged in: {access_token}")

# 3. Get current user
headers = {"Authorization": f"Bearer {access_token}"}
me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
print(f"Current user: {me.json()}")

# 4. Change password
requests.post(f"{BASE_URL}/api/auth/change-password", 
    headers=headers,
    json={
        "current_password": "TradingBot123!",
        "new_password": "NewTradingBot123!"
    }
)
print("Password changed")

# 5. Logout
requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
print("Logged out")
```

## Production Checklist

- [ ] Set strong `JWT_SECRET_KEY` in `.env`
- [ ] Configure Firebase database security rules
- [ ] Enable HTTPS for production
- [ ] Set CORS origins appropriately
- [ ] Regular audit log reviews
- [ ] Monitor rate limit violations
- [ ] Backup user database regularly
- [ ] Test password reset flow
- [ ] Configure email notifications (optional)
- [ ] Set up log rotation for audit.log
- [ ] Test admin password reset functionality
- [ ] Document password reset procedures

## Support

For issues or questions:
1. Check audit logs: `logs/audit.log`
2. Review error messages in dashboard logs
3. Verify Firebase project configuration
4. Test endpoints with curl or Postman
