from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Payload for authenticating existing users."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Access Token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload data."""
    sub: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
