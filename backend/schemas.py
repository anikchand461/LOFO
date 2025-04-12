from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Post schemas
class PostBase(BaseModel):
    title: str
    type: str  # 'lost' or 'found'
    description: str
    location: str
    contact: str
    image_url: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostOut(PostBase):
    id: int
    created_at: datetime
    user_id: Optional[int] = None

    class Config:
        from_attributes = True