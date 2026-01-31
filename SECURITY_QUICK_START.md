# 🔐 EvoBot Security Quick Start Guide

## What's New in v2.0.0

Your EvoBot trading system now includes **enterprise-grade security** features:

### ✅ Implemented Features

- **Secure JWT Authentication** - Token-based login with refresh tokens
- **Password Policy Enforcement** - Strong password requirements
- **Account Lockout Protection** - Automatic lockout after 5 failed attempts
- **Session Management** - Track and manage active sessions
- **Audit Logging** - Comprehensive security event tracking
- **Rate Limiting** - DDoS protection and abuse prevention
- **Role-Based Access Control** - Admin, User, and Viewer roles
- **Admin Dashboard** - Full security management interface
- **Token Blacklisting** - Invalidate tokens on logout
- **Persistent User Storage** - User data saved across restarts

---

## 🚀 Getting Started

### Step 1: Start the Dashboard

```bash
cd /home/ubuntu/personal/evobot
python3 start_dashboard.py
```

Dashboard will be available at: `http://localhost:8080`

### Step 2: Login with Default Admin

- **URL**: `http://localhost:8080/login`
- **Username**: `admin`
- **Password**: `Admin@123!` (or value of `ADMIN_PASSWORD` env var)

⚠️ **IMPORTANT**: Change this password immediately after first login!

### Step 3: Change Admin Password

1. After logging in, go to Dashboard
2. Click on your username (top right)
3. Select "Change Password"
4. Enter current password: `Admin@123!`
5. Enter new secure password
6. Click "Update Password"

### Step 4: Access Admin Panel

- **URL**: `http://localhost:8080/admin`
- Only admin users can access

---

## 👥 Managing Users

### Create New User (Admin Only)

1. Go to `/admin`
2. Click "Add User" button
3. Fill in the form:
   - **Username**: 3-20 characters, alphanumeric only
   - **Email**: Valid email address
   - **Password**: Must meet policy requirements
   - **Role**: Select from Viewer, User, or Admin
4. Click "Create"

### Password Requirements

All passwords must have:
- ✅ Minimum 8 characters
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one lowercase letter (a-z)
- ✅ At least one digit (0-9)
- ✅ At least one special character (!@#$%^&*)

**Examples**:
- ✅ `SecurePass@123`
- ✅ `Trading#2024Bot`
- ❌ `password123` (missing uppercase & special)

### Manage User Roles

From Admin Panel, you can:

1. **View Users**: See all users with creation date, last login, failed attempts
2. **Disable/Enable**: Toggle user access on/off
3. **Change Role**: Click role badge to change admin/user/viewer
4. **Reset Password**: Click "Reset PW" to force password change
5. **Unlock Account**: Unlock accounts locked by failed attempts
6. **Delete User**: Permanently remove user (cannot delete admin user)

---

## 🔑 Understanding Roles

### 👑 Admin Role
- **Full system access**
- Can create, edit, delete users
- Can assign roles
- Can view audit logs
- Can reset user passwords
- Can unlock locked accounts

### 👤 User Role
- Can view and execute trades
- Can view dashboard
- Can change own password
- Cannot manage other users
- Cannot access admin panel

### 👁️ Viewer Role
- Read-only access
- Can view trades and dashboard
- Cannot execute trades
- Cannot manage settings
- Cannot access admin panel

---

## 📊 Security Dashboard

### Admin Security Panel Features

1. **Security Statistics** (Top Cards):
   - Total Users
   - Active Users
   - Admin Count
   - Active Sessions
   - Locked Accounts
   - Failed Logins (24h)

2. **User Management Table**:
   - Username, Email, Role, Status
   - Creation date and last login
   - Failed login attempts counter
   - Quick action buttons

3. **Audit Log**:
   - Real-time security events
   - Filter by event type, username, or IP
   - Severity levels (INFO, WARNING, CRITICAL)
   - Event details in JSON format

---

## 🔐 Security Features Explained

### Account Lockout

**When it happens**:
- User fails 5 login attempts within 30 minutes

**What happens**:
- Account automatically locks for 30 minutes
- User sees: "Account locked. Try again in X seconds"
- Login attempts are blocked during lockout

**How to unlock**:
- Wait 30 minutes for automatic unlock, OR
- Admin clicks "Unlock" button in user table

### Session Management

**What tracks**:
- Login time
- Last activity
- User IP address
- Browser information
- Session status

**View your sessions**:
```bash
GET /api/auth/sessions
Authorization: Bearer <your_token>
```

**Auto-logout**:
- Sessions expire after 24 hours of inactivity (configurable)
- You must login again after expiry

### Audit Logging

**Every event logged**:
- Login attempts (success/failure)
- Password changes
- User creation/deletion
- Role changes
- Account locks/unlocks
- Admin actions
- API errors

**Access logs**:
1. Go to Admin Panel
2. Scroll to "Security Audit Log" section
3. Search and filter events
4. Click timestamp for details

**Log files**:
- Location: `/home/ubuntu/personal/evobot/logs/audit.log`
- Format: JSON, one event per line
- Retention: All events (can be trimmed manually)

### Rate Limiting

**What it does**:
- Limits API requests: 100 per 60 seconds per IP
- Protects against DDoS and brute force attacks
- Returns HTTP 429 (Too Many Requests)

**If rate limited**:
- Wait 60 seconds and retry
- Check `X-RateLimit-Remaining` header
- Respect `Retry-After` header

---

## 🛠️ API Endpoints

### Authentication Endpoints

```bash
# Login
POST /api/auth/login
{"username": "admin", "password": "Admin@123!"}

# Refresh Token
POST /api/auth/refresh
{"refresh_token": "..."}

# Logout
POST /api/auth/logout
Authorization: Bearer <token>

# Get Current User
GET /api/auth/me
Authorization: Bearer <token>

# Change Password
POST /api/auth/change-password
Authorization: Bearer <token>
{"current_password": "...", "new_password": "..."}

# View Sessions
GET /api/auth/sessions
Authorization: Bearer <token>
```

### Admin Endpoints

```bash
# Get All Users
GET /api/admin/users
Authorization: Bearer <admin_token>

# Create User
POST /api/admin/users
Authorization: Bearer <admin_token>

# Toggle User Status
PUT /api/admin/users/{username}/toggle
Authorization: Bearer <admin_token>

# Reset User Password
POST /api/admin/users/{username}/reset-password
Authorization: Bearer <admin_token>

# Unlock Account
POST /api/admin/users/{username}/unlock
Authorization: Bearer <admin_token>

# Change User Role
PUT /api/admin/users/{username}/role
Authorization: Bearer <admin_token>
{"role": "user"}

# Delete User
DELETE /api/admin/users/{username}
Authorization: Bearer <admin_token>

# Get Audit Logs
GET /api/admin/security/audit?limit=100
Authorization: Bearer <admin_token>

# Get Security Stats
GET /api/admin/security/stats
Authorization: Bearer <admin_token>

# Get Available Roles
GET /api/admin/roles
Authorization: Bearer <admin_token>
```

---

## 🔒 Best Practices

### For All Users

1. **Login Safely**
   - Use strong, unique passwords
   - Never share your password
   - Logout when not in use

2. **Token Security**
   - Keep tokens confidential
   - Don't expose in logs or shared screens
   - Always use HTTPS (never HTTP)

3. **Monitor Activity**
   - Check your sessions regularly
   - Review failed login attempts in audit log
   - Report suspicious activity to admin

### For Administrators

1. **Regular Audits**
   - Review audit log weekly
   - Check for unusual login patterns
   - Monitor account creations
   - Track permission changes

2. **Access Control**
   - Give minimum necessary permissions
   - Remove unused accounts
   - Disable accounts for inactive users
   - Keep admin count minimal

3. **Password Management**
   - Change default passwords immediately
   - Reset compromised passwords quickly
   - Enforce strong password policy
   - Never share credentials

4. **Monitoring**
   - Watch for rate limit violations
   - Monitor active sessions
   - Alert on critical events
   - Check failed login trends

---

## 📚 Documentation

For complete security documentation, see: `SECURITY.md`

Includes:
- Detailed feature explanations
- API request/response examples
- Troubleshooting guide
- Compliance information
- Environment configuration

---

## ⚡ Common Tasks

### Change Your Own Password

```
1. Login to Dashboard
2. Click username (top right)
3. "Change Password"
4. Enter current and new password
5. Click "Update"
```

### Admin: Reset User Password

```
1. Go to Admin Panel (/admin)
2. Find user in table
3. Click "Reset PW"
4. Enter new password
5. Click "Reset"
6. Notify user of new temporary password
```

### Admin: Unlock User Account

```
1. Go to Admin Panel
2. Look for "🔒 Locked" status
3. Click "Unlock" button
4. User can login again
```

### Admin: View Failed Logins

```
1. Go to Admin Panel
2. Scroll to "Security Audit Log"
3. Search for: "login_failed"
4. See failed attempts and details
```

### Admin: Change User Role

```
1. Go to Admin Panel
2. Click on user's role badge (colored)
3. Select new role from dropdown
4. Click "Update"
```

---

## 🆘 Troubleshooting

### "Account locked due to too many failed attempts"
- **Solution**: Wait 30 minutes OR ask admin to unlock

### "Password must contain uppercase letter"
- **Solution**: Add uppercase letter to password and try again

### "Token expired"
- **Solution**: Login again or refresh token at `/api/auth/refresh`

### "Too many requests" (429 error)
- **Solution**: Wait 60 seconds, then retry

### Can't access admin panel as admin user
- **Solution**: Verify user has "admin" role in user table

### Lost admin password
- **Solution**: Check default in `.env` file or reset in database

---

## 📞 Support

For security issues or questions:

1. **Check the docs**: `SECURITY.md` for detailed info
2. **View logs**: `logs/audit.log` for event details
3. **Admin panel**: `/admin` for visual management
4. **API docs**: `http://localhost:8080/api/docs` (if enabled)

---

## 🎯 Next Steps

1. ✅ Change default admin password
2. ✅ Create accounts for team members with appropriate roles
3. ✅ Review audit logs for unusual activity
4. ✅ Configure environment variables in production
5. ✅ Enable HTTPS on production server
6. ✅ Set up monitoring and alerting
7. ✅ Document your security policies
8. ✅ Train team members on password safety

---

**Version**: 2.0.0  
**Last Updated**: January 28, 2024  
**Status**: Production Ready  
**Maintenance**: Keep audit logs, update passwords, review activity regularly
