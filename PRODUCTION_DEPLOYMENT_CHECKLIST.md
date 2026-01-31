# 🚀 EvoBot Security - Production Deployment Checklist

## Pre-Deployment (Development/Staging)

### Security Testing

- [ ] Test login with correct password
- [ ] Test login with wrong password 5 times (should lock)
- [ ] Test password policy enforcement
  - [ ] Reject password without uppercase
  - [ ] Reject password without lowercase
  - [ ] Reject password without digit
  - [ ] Reject password without special character
  - [ ] Reject password < 8 characters
- [ ] Test account unlock
- [ ] Test rate limiting (100 requests in 60 seconds)
- [ ] Test token expiry (24 hours)
- [ ] Test token refresh
- [ ] Test logout (token blacklisting)
- [ ] Test audit log recording
- [ ] Test audit log filtering
- [ ] Test admin user creation
- [ ] Test admin password reset
- [ ] Test role-based access control
- [ ] Test all admin endpoints
- [ ] Verify secure file permissions
- [ ] Verify audit logs are created

### Functional Testing

- [ ] Login works
- [ ] Change password works
- [ ] Create user works
- [ ] Delete user works
- [ ] Disable/enable user works
- [ ] Reset password works
- [ ] Unlock account works
- [ ] View sessions works
- [ ] Admin panel loads
- [ ] Dashboard loads
- [ ] All pages accessible with valid token
- [ ] All pages blocked without valid token

### Integration Testing

- [ ] Works with dashboard
- [ ] Works with all existing features
- [ ] No breaking changes to trading
- [ ] No breaking changes to signals
- [ ] Firebase integration still works
- [ ] Telegram integration still works
- [ ] MT5 integration still works

---

## Pre-Production Configuration

### Secrets & Keys

- [ ] Generate new `JWT_SECRET_KEY`
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Set `JWT_SECRET_KEY` in environment
- [ ] Change `ADMIN_PASSWORD` to strong password
- [ ] Remove or secure `.secret_key` file
- [ ] Verify key is not in git history
- [ ] Verify key is not in code
- [ ] Create `.env` file with secure values
- [ ] Verify `.env` is in `.gitignore`
- [ ] Remove example files from production
  - [ ] Delete `.env.security.example`
  - [ ] Keep only production `.env`

### Network & HTTPS

- [ ] Enable HTTPS/TLS
- [ ] Install valid SSL certificate
- [ ] Redirect HTTP to HTTPS
- [ ] Configure CORS origins (not `*`)
  ```bash
  CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
  ```
- [ ] Set `TRUSTED_HOSTS` appropriately
- [ ] Enable HSTS header
- [ ] Disable SSLv3, TLSv1.0, TLSv1.1
- [ ] Use TLS 1.2+ only

### API Security

- [ ] Set `ENABLE_API_DOCS=false`
  - Hide Swagger UI in production
- [ ] Configure rate limiting appropriately
- [ ] Adjust `RATE_LIMIT_REQUESTS` if needed
- [ ] Adjust `RATE_LIMIT_WINDOW_SECONDS` if needed
- [ ] Set `LOG_LEVEL=WARNING` or higher
- [ ] Verify logging is not too verbose
- [ ] Test with production-like load

### Database & Storage

- [ ] Verify `data/users.json` permissions (0o600)
- [ ] Verify `data/.secret_key` permissions (0o600)
- [ ] Verify `logs/` directory exists
- [ ] Verify `logs/` directory permissions
- [ ] Set up log rotation for `audit.log`
- [ ] Set up backup of `users.json`
- [ ] Set up backup of `security_data.json`
- [ ] Verify backup retention policy

### Admin User

- [ ] Change default admin password immediately
- [ ] Create backup admin account
- [ ] Test backup admin account
- [ ] Document admin credentials securely
- [ ] Store credentials in secure password manager
- [ ] Restrict admin access to trusted networks (optional)

### Monitoring & Alerting

- [ ] Set up log monitoring
- [ ] Set up alert for failed login spikes
- [ ] Set up alert for account lockouts
- [ ] Set up alert for rate limit violations
- [ ] Set up alert for unusual IP addresses
- [ ] Monitor disk space for audit logs
- [ ] Set up health check endpoint
- [ ] Monitor API response times
- [ ] Monitor error rates

---

## Deployment

### Infrastructure

- [ ] Production server running Linux
- [ ] Python 3.8+ installed
- [ ] Required packages installed
- [ ] Firewall configured
- [ ] Ports open only to necessary IPs
- [ ] SSH hardened (key-based auth only)
- [ ] sudo configured for admin users
- [ ] SELinux/AppArmor configured (optional)

### Application Deployment

- [ ] Code checked into secure git repository
- [ ] Only tagged versions deployed
- [ ] Build process tested
- [ ] Dependencies installed in venv
- [ ] Application tested before production
- [ ] Rollback procedure documented
- [ ] Update procedure documented

### Service Configuration

- [ ] FastAPI running behind reverse proxy (nginx/Apache)
- [ ] Uvicorn configured for production
- [ ] Worker processes configured
- [ ] Supervisor/systemd service created
- [ ] Auto-restart on failure configured
- [ ] Process monitoring enabled
- [ ] Log rotation configured

### First Production Startup

- [ ] Verify all environment variables set
- [ ] Verify database files created
- [ ] Verify audit logs created
- [ ] Test login with admin account
- [ ] Change admin password
- [ ] Create test user
- [ ] Test all endpoints
- [ ] Verify audit log entries created
- [ ] Check for errors in logs
- [ ] Monitor for 1 hour

---

## Post-Deployment

### Verification (First Day)

- [ ] All users can login successfully
- [ ] All permissions working correctly
- [ ] Admin panel accessible
- [ ] Audit logs recording events
- [ ] No error spikes in logs
- [ ] Performance acceptable
- [ ] Database backups working
- [ ] SSL certificate valid
- [ ] HTTPS enforced

### Security Hardening (First Week)

- [ ] Review failed login attempts
- [ ] Check for suspicious IPs
- [ ] Monitor user creation
- [ ] Review role assignments
- [ ] Check audit logs for anomalies
- [ ] Test disaster recovery
- [ ] Test backup restoration
- [ ] Update documentation
- [ ] Train team on security features

### Regular Maintenance

**Daily**
- [ ] Check error logs
- [ ] Check audit logs for anomalies
- [ ] Monitor failed login attempts
- [ ] Check active sessions

**Weekly**
- [ ] Review audit logs
- [ ] Verify backups are working
- [ ] Check disk usage
- [ ] Monitor performance metrics
- [ ] Check for security updates

**Monthly**
- [ ] Security audit
- [ ] Performance review
- [ ] Update security policies
- [ ] Review user access
- [ ] Disable inactive accounts
- [ ] Verify disaster recovery plan

**Quarterly**
- [ ] Full security assessment
- [ ] Penetration testing (optional)
- [ ] Disaster recovery drill
- [ ] Team security training
- [ ] Policy review and updates

---

## Monitoring Dashboard Items

Create a monitoring dashboard with:

- [ ] Failed login attempts (last 24h)
- [ ] Locked accounts count
- [ ] Active sessions count
- [ ] Rate limit violations (last 24h)
- [ ] Admin user count
- [ ] Total user count
- [ ] API error rate
- [ ] API response time
- [ ] Database file size
- [ ] Audit log file size
- [ ] SSL certificate expiry
- [ ] Backup status
- [ ] Disk usage
- [ ] Memory usage
- [ ] CPU usage

---

## Incident Response Procedures

### Suspected Security Breach

1. [ ] Immediately change all admin passwords
2. [ ] Review audit logs for unauthorized access
3. [ ] Check for unexpected user accounts
4. [ ] Review recent role changes
5. [ ] Check for token abuse
6. [ ] Invalidate all tokens
7. [ ] Contact affected users
8. [ ] Document incident details
9. [ ] Review logs for attack vector
10. [ ] Implement fixes to prevent recurrence

### Account Compromise

1. [ ] Reset user password
2. [ ] Unlock account if locked
3. [ ] Invalidate user sessions
4. [ ] Review user's audit log entries
5. [ ] Check for unauthorized actions
6. [ ] Notify user of incident
7. [ ] Require password change on next login
8. [ ] Monitor account for suspicious activity

### Brute Force Attack

1. [ ] Check `audit.log` for source IP
2. [ ] Block IP at firewall level
3. [ ] Check rate limiter is working
4. [ ] Review failed login patterns
5. [ ] Identify targeted accounts
6. [ ] Reset passwords if compromised
7. [ ] Update security rules if needed

### Rate Limit Abuse

1. [ ] Identify abusive IP
2. [ ] Block IP if necessary
3. [ ] Analyze usage patterns
4. [ ] Adjust rate limits if needed
5. [ ] Check for legitimate heavy users
6. [ ] Whitelist trusted IPs if applicable

---

## Compliance Checklist

### Data Protection

- [ ] GDPR compliant (if applicable)
  - [ ] User consent for data storage
  - [ ] Right to be forgotten implemented
  - [ ] Data breach notification process
  - [ ] Privacy policy updated
- [ ] CCPA compliant (if applicable)
- [ ] Industry-specific regulations
  - [ ] Financial: PCI-DSS if handling payments
  - [ ] Healthcare: HIPAA if health data
  - [ ] Trading: Relevant regulations

### Security Standards

- [ ] NIST Cybersecurity Framework
- [ ] ISO 27001 applicable controls
- [ ] OWASP Top 10 mitigations
- [ ] CIS Benchmarks applied

### Documentation

- [ ] Security policy document
- [ ] Incident response procedure
- [ ] Disaster recovery plan
- [ ] Data retention policy
- [ ] Access control policy
- [ ] Password policy document
- [ ] Audit log retention policy
- [ ] Backup procedure documented

---

## Sign-Off Checklist

### Development Lead

- [ ] Code reviewed
- [ ] All tests passed
- [ ] Security requirements met
- [ ] Performance acceptable
- [ ] Documentation complete

### DevOps/Infrastructure

- [ ] Infrastructure ready
- [ ] Monitoring configured
- [ ] Backups verified
- [ ] Disaster recovery tested
- [ ] Performance baseline established

### Security Officer

- [ ] Security assessment passed
- [ ] Vulnerabilities remediated
- [ ] Audit logging verified
- [ ] Compliance confirmed
- [ ] Risk assessment complete

### Product Owner

- [ ] Business requirements met
- [ ] User experience acceptable
- [ ] Admin controls working
- [ ] Documentation adequate
- [ ] Training materials ready

### Final Approval

- [ ] Ready for production: _____ (Date)
- [ ] Approved by: _____ (Name/Title)
- [ ] Emergency contact: _____ (Phone)
- [ ] Rollback contact: _____ (Name/Phone)

---

## Contacts & Escalation

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Primary | _____ | _____ | _____ |
| Secondary | _____ | _____ | _____ |
| Backup | _____ | _____ | _____ |

### Escalation Path

1. **Level 1 (Support)**: First responder
2. **Level 2 (DevOps)**: Infrastructure issues
3. **Level 3 (Security)**: Security incidents
4. **Level 4 (Leadership)**: Major incidents

---

## Post-Deployment Success Metrics

### Week 1

- [ ] No security incidents
- [ ] All users successfully logging in
- [ ] Zero false positives on alerts
- [ ] Audit logs recording properly
- [ ] System availability > 99.9%
- [ ] API response time < 200ms median

### Month 1

- [ ] Team trained on security features
- [ ] Audit logs reviewed and analyzed
- [ ] Any issues resolved
- [ ] Performance stable
- [ ] No escalations needed
- [ ] Disaster recovery tested

### Ongoing

- [ ] Security posture improving
- [ ] Team proficiency increasing
- [ ] Audit logs clean (no false positives)
- [ ] Zero security breaches
- [ ] User satisfaction > 95%
- [ ] SLA compliance > 99.5%

---

## Notes & Additional Items

```
_____________________________________________________________

_____________________________________________________________

_____________________________________________________________

_____________________________________________________________

_____________________________________________________________
```

---

**Checklist Version**: 2.0.0  
**Last Updated**: January 28, 2024  
**Status**: Ready for Production  
**Completion Date**: _______________  
**Approved By**: _______________  

---

**Print & Fill**: This checklist can be printed and completed physically during deployment.

For digital tracking, use your organization's deployment tracking system.

Keep completed checklist for audit and compliance purposes.
