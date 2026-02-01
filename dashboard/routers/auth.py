from fastapi import APIRouter, Request, HTTPException, Depends
from dashboard.schemas import (
    SignupRequest, LoginRequest, PasswordChangeRequest
)
from dashboard.deps import get_client_ip, get_current_user
from core.firebase_auth import firebase_auth_service
from core.security import security_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup")
async def signup(request_data: SignupRequest, request: Request):
    """Register new user with Firebase"""
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

@router.post("/login")
async def login(credentials: LoginRequest, request: Request):
    """Login endpoint with Firebase authentication"""
    client_ip = get_client_ip(request)
    
    success, message, token_data = firebase_auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password,
        ip_address=client_ip
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return token_data

@router.post("/refresh")
async def refresh_token(refresh_token: str, request: Request):
    """Refresh access token"""
    is_valid, payload = firebase_auth_service.verify_jwt_token(refresh_token)
    
    if not is_valid or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = firebase_auth_service.get_user_by_uid(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new access token
    access_token = firebase_auth_service._create_jwt_token(
        user_id=user["uid"],
        email=user["email"],
        role=user.get("role", "Viewer"),
        expires_in=3600
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }

@router.post("/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout and invalidate token"""
    auth_header = request.headers.get("Authorization")
    if auth_header:
        security_manager.audit_log(
            "logout",
            current_user.get("email"),
            get_client_ip(request),
            details="User logged out",
            severity="info"
        )
    
    return {"message": "Logged out successfully"}

@router.post("/change-password")
async def change_password_endpoint(
    data: PasswordChangeRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Change current user's password"""
    success, message = firebase_auth_service.change_password(
        email=current_user["email"],
        current_password=data.current_password,
        new_password=data.new_password,
        ip_address=get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "uid": current_user.get("uid"),
        "email": current_user.get("email"),
        "display_name": current_user.get("display_name"),
        "role": current_user.get("role", "Viewer"),
        "created_at": current_user.get("created_at"),
        "last_login": current_user.get("last_login"),
        "login_count": current_user.get("login_count", 0)
    }
