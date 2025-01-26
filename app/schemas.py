# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True  # для Pydantic v2 замість orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ContactBase(BaseModel):
    name: str
    phone: str
    email: EmailStr

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class UpdateAvatar(BaseModel):
    avatar: str  # Base64 або URL залежно від реалізації
