from fastapi import Request, HTTPException
import logging
from core.firebase_auth import firebase_auth_service
from core.security import security_manager

logger = logging.getLogger("evobot.dashboard.deps")

def get_client_ip(request: Request) -> str:
    """Get client IP from request"""
    if x_forwarded := request.headers.get("X-Forwarded-For"):
        return x_forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

async def get_current_user(request: Request):
    """Dependency: Get current user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    token = auth_header.split(" ")[1]
    is_valid, payload = firebase_auth_service.verify_jwt_token(token)
    
    if not is_valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = firebase_auth_service.get_user_by_uid(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_admin_user(request: Request):
    """Dependency: Get current user and verify admin role"""
    user = await get_current_user(request)
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
