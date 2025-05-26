from pydantic import BaseModel, field_validator, ConfigDict, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v
    
    @field_validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    model_config = ConfigDict(extra='ignore')
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
