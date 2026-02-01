from fastapi import APIRouter, Request, HTTPException, Depends
from datetime import datetime
import json
from dashboard.schemas import (
    SignupRequest, PasswordResetRequest, UserRoleUpdateRequest
)
from dashboard.deps import get_admin_user, get_client_ip
from core.firebase_auth import firebase_auth_service
from core.security import security_manager

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users")
async def get_users(current_user: dict = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = firebase_auth_service.list_users()
    return {"users": users}

@router.post("/users")
async def create_user_admin(
    request_data: SignupRequest,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Create new user (admin only)"""
    success, message, user = firebase_auth_service.create_user(
        email=request_data.email,
        password=request_data.password,
        display_name=request_data.display_name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "user": {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        }
    }

@router.post("/users/{email}/reset-password")
async def reset_password_admin(
    email: str,
    data: PasswordResetRequest,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Admin reset user password"""
    success, message = firebase_auth_service.reset_password(
        email=email,
        new_password=data.new_password,
        admin_email=current_user.get("email"),
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@router.post("/users/{email}/role")
async def update_user_role(
    email: str,
    data: UserRoleUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Update user role (admin only)"""
    success, message = firebase_auth_service.update_user_role(
        email=email,
        new_role=data.role,
        admin_email=current_user.get("email"),
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@router.post("/users/{email}/unlock")
async def unlock_user_account(
    email: str,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Unlock user account (remove login lockout)"""
    success, message = firebase_auth_service.unlock_account(
        email=email,
        admin_email=current_user.get("email"),
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@router.get("/security/stats")
async def get_security_stats(current_user: dict = Depends(get_admin_user)):
    """Get security statistics"""
    return {
        "users": len(firebase_auth_service.list_users()),
        "failed_attempts": len(security_manager.failed_attempts),
        "locked_accounts": len(security_manager.account_lockouts),
        "active_sessions": len(security_manager.active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/security/audit")
async def get_audit_logs(skip: int = 0, limit: int = 100, current_user: dict = Depends(get_admin_user)):
    """Get audit logs"""
    try:
        with open("logs/audit.log", "r") as f:
            logs = []
            for line in f:
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except:
                    pass
            logs.reverse()
            return {"logs": logs[skip:skip+limit], "total": len(logs)}
    except FileNotFoundError:
        return {"logs": [], "total": 0}
