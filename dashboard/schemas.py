from pydantic import BaseModel
from typing import Optional, Dict

# Config Models
class ConfigUpdate(BaseModel):
    default_lot_size: Optional[float] = None
    max_spread_pips: Optional[float] = None
    max_daily_drawdown: Optional[float] = None
    max_open_trades: Optional[int] = None
    symbol_max_spreads: Optional[Dict[str, float]] = None

# Trade Models
class SignalTestRequest(BaseModel):
    message: str

class TradeAction(BaseModel):
    trade_id: str
    action: str  # close, modify_sl, modify_tp

# Auth Models
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str

class UserRoleUpdateRequest(BaseModel):
    role: str  # Admin, User, Viewer

# Telegram Setup Models
class TelegramSetupRequest(BaseModel):
    phone: str

class TelegramVerifyRequest(BaseModel):
    code: str

class TelegramPasswordRequest(BaseModel):
    password: str
