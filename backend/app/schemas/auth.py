
from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "readonly"
    center_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    center_id: Optional[str] = None
    is_active: bool
    class Config:
        from_attributes = True
