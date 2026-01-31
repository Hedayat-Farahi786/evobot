# Authentication Troubleshooting Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements_firebase.txt
```

### 2. Start Dashboard with Verification
```bash
python start_dashboard_secure.py
```

### 3. Test Authentication
```bash
python test_auth.py
```

## Common Issues & Solutions

### Issue 1: "bcrypt not installed"
**Solution:**
```bash
pip install bcrypt>=4.1.0
```

### Issue 2: "PyJWT not installed"
**Solution:**
```bash
pip install PyJWT>=2.8.0
```

### Issue 3: "Firebase Admin SDK not installed"
**Solution:**
```bash
pip install firebase-admin>=6.3.0
```

### Issue 4: Login returns 500 error
**Cause:** Missing dependencies or database initialization
**Solution:**
1. Check logs in `logs/system.log`
2. Ensure `data/` directory exists
3. Run: `python start_dashboard_secure.py`

### Issue 5: "Invalid email or password" for admin
**Cause:** Admin user not created or password mismatch
**Solution:**
```python
# Run this to recreate admin:
python -c "
from core.firebase_auth import init_firebase_auth
auth = init_firebase_auth()
print('Admin user initialized')
"
```

### Issue 6: Token validation fails
**Cause:** JWT secret key mismatch
**Solution:**
1. Set consistent JWT_SECRET_KEY in .env:
```bash
JWT_SECRET_KEY=your-secret-key-here
```
2. Restart dashboard

### Issue 7: CORS errors in browser
**Cause:** CORS not configured for your domain
**Solution:**
Add to .env:
```bash
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

## Manual Testing

### Test Login via curl
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@evobot.local","password":"Admin@123!"}'
```

### Test Signup via curl
```bash
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123!","display_name":"Test User"}'
```

### Test Protected Endpoint
```bash
# First get token from login
TOKEN="your-token-here"

curl -X GET http://localhost:8080/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Verification Checklist

- [ ] Dependencies installed (`pip list | grep -E "bcrypt|PyJWT|firebase-admin"`)
- [ ] `data/` directory exists
- [ ] `logs/` directory exists
- [ ] Dashboard starts without errors
- [ ] Login page loads at http://localhost:8080/login
- [ ] Can login with admin@evobot.local / Admin@123!
- [ ] Can create new user
- [ ] Protected endpoints require authentication
- [ ] Invalid credentials are rejected
- [ ] Weak passwords are rejected

## Security Notes

### Default Credentials
- **Email:** admin@evobot.local
- **Password:** Admin@123!
- ⚠️ **CHANGE IMMEDIATELY IN PRODUCTION**

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*)

### Rate Limiting
- 100 requests per 60 seconds per IP
- 5 failed login attempts = 30 minute lockout

### Session Management
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days
- Sessions tracked in memory and audit logs

## Production Deployment

### Before Going Live:

1. **Change JWT Secret:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Add to .env: JWT_SECRET_KEY=<generated-key>
```

2. **Change Admin Password:**
- Login as admin
- Go to profile settings
- Change password to strong unique password

3. **Configure CORS:**
```bash
CORS_ORIGINS=https://yourdomain.com
```

4. **Enable HTTPS:**
- Use reverse proxy (nginx/Apache)
- Install SSL certificate
- Redirect HTTP to HTTPS

5. **Set Environment:**
```bash
ENABLE_API_DOCS=false
LOG_LEVEL=WARNING
```

## Support

If issues persist:
1. Check `logs/system.log` for errors
2. Check `logs/audit.log` for authentication events
3. Run `python test_auth.py` for diagnostics
4. Verify all dependencies are installed
5. Ensure Python 3.8+ is being used

## File Locations

- **Login Page:** `dashboard/templates/login.html`
- **Auth Service:** `core/firebase_auth.py`
- **Security Manager:** `core/security.py`
- **Dashboard App:** `dashboard/app.py`
- **User Data:** `data/users_local.json`
- **Audit Logs:** `logs/audit.log`
