from fastapi import APIRouter, Request, HTTPException, Depends
from dashboard.schemas import (
    TelegramSetupRequest, TelegramVerifyRequest, TelegramPasswordRequest
)
from dashboard.deps import get_client_ip
from core.telegram_auth import telegram_auth_service
from core.telegram_setup import telegram_setup_service
from core.security import security_manager

router = APIRouter(prefix="/api/auth/telegram", tags=["telegram"])

@router.get("/status")
async def telegram_auth_status():
    """Check if Telegram session is available for authentication"""
    is_valid, user_info = await telegram_auth_service.check_telegram_session()
    return {
        "has_session": is_valid,
        "user": user_info if is_valid else None
    }

@router.post("/login")
async def telegram_login(request: Request):
    """
    Authenticate using Telegram session.
    This uses the existing Telegram session to authenticate the user.
    """
    client_ip = get_client_ip(request)
    
    success, message, token_data = await telegram_auth_service.authenticate()
    
    if not success:
        security_manager.audit_log(
            "telegram_login_failed",
            ip_address=client_ip,
            details={"message": message},
            severity="warning"
        )
        raise HTTPException(status_code=401, detail=message)
    
    security_manager.audit_log(
        "telegram_login_success",
        token_data["user"]["username"] or str(token_data["user"]["id"]),
        ip_address=client_ip,
        details={"user_id": token_data["user"]["id"]},
        severity="info"
    )
    
    return token_data

@router.post("/refresh")
async def telegram_refresh_token(request: Request):
    """Refresh access token using refresh token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    refresh_token = auth_header.split(" ")[1]
    success, token_data = telegram_auth_service.refresh_access_token(refresh_token)
    
    if not success:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    return token_data

@router.post("/logout")
async def telegram_logout(request: Request):
    """Logout and invalidate session"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        is_valid, payload = telegram_auth_service.verify_token(token)
        if is_valid and payload:
            telegram_auth_service.invalidate_session(payload.get("user_id"))
            security_manager.audit_log(
                "telegram_logout",
                str(payload.get("user_id")),
                ip_address=get_client_ip(request),
                details="User logged out",
                severity="info"
            )
    
    return {"message": "Logged out successfully"}

@router.get("/me")
async def telegram_get_me(request: Request):
    """Get current Telegram user info from token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = telegram_auth_service.verify_token(token)
    
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = telegram_auth_service.get_user_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user.to_dict()

# ============================================
# Telegram Setup Routes (No Auth Required)
# ============================================

@router.post("/setup/request-code")
async def telegram_setup_request_code(data: TelegramSetupRequest, request: Request):
    """Request verification code for Telegram setup"""
    client_ip = get_client_ip(request)
    
    # Optional: Rate limit based on IP using existing mechanism
    allowed, remaining = security_manager.check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many attempts")
        
    success, message = await telegram_setup_service.request_code(data.phone)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"message": message}

@router.post("/setup/verify-code")
async def telegram_setup_verify_code(data: TelegramVerifyRequest):
    """Verify code and complete setup"""
    success, message, requires_password = await telegram_setup_service.verify_code(data.code)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    if requires_password:
        return {"status": "requires_password", "message": message}
    
    # If success and no password needed, cleanup setup service
    await telegram_setup_service.cleanup()
    
    # Auto-login the user
    auth_success, auth_msg, token_data = await telegram_auth_service.authenticate()
    if not auth_success:
         # Should not happen if setup just succeeded
         raise HTTPException(status_code=500, detail="Setup successful but auto-login failed")
         
    return {"status": "success", "message": "Setup complete", "auth": token_data}

@router.post("/setup/verify-password")
async def telegram_setup_verify_password(data: TelegramPasswordRequest):
    """Verify 2FA password"""
    success, message = await telegram_setup_service.verify_password(data.password)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    # Cleanup setup service
    await telegram_setup_service.cleanup()
    
    # Auto-login
    auth_success, auth_msg, token_data = await telegram_auth_service.authenticate()
    if not auth_success:
         raise HTTPException(status_code=500, detail="Setup successful but auto-login failed")
         
    return {"status": "success", "message": "Setup complete", "auth": token_data}

@router.post("/setup/reset")
async def telegram_setup_reset():
    """Reset Telegram setup state - use when setup gets stuck"""
    await telegram_setup_service.reset_setup()
    return {"message": "Setup reset successfully. You can try again."}

@router.post("/setup/resend-sms")
async def telegram_setup_resend_sms():
    """Resend verification code via SMS"""
    success, message = await telegram_setup_service.resend_code_sms()
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"message": message}
