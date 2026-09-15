from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=150)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = Field(default="tourist", pattern="^(tourist|business)$")


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
