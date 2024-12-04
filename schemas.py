from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password1: str = Field(..., min_length=8, max_length=16)
    password2: str
    first_name: str = None
    last_name: str = None

    @validator("password2")
    def passwords_match(cls, v, values):
        if 'password1' in values and v != values['password1']:
            raise ValueError("Passwords do not match")
        return v

    @validator("password1")
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char in "!@#$%^&*()_+-=" for char in v):
            raise ValueError("Password must contain at least one special character")
        return v
    
class UserResponse(BaseModel):
    username: str
    email: str
    first_name: str = None
    last_name: str = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class BookCreate(BaseModel):
    title: str
    author : str
    price : float

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    price: Optional[float] = None

class PostCreate(BaseModel):
    title: str
    content : str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content : Optional[str] = None

class ProfileCreate(BaseModel):
    bio: str = Field("I love programming")
    location: str = Field('San Francisco')
    birthdate: date = Field('1990-02-10')
    

class ProfileUpdate(BaseModel):
    bio: Optional[str] = Field(None, example="Updated bio")
    location: Optional[str] = Field(None, example="San Francisco")
    birthdate: Optional[date] = Field(None, example="1990-02-10")