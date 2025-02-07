from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from api.v1.models.common import PyObjectId


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    is_private: bool


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class User(UserBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    currently_playing: Optional[str] = None
    leadrboard: List[str] = Field(default_factory=list, max_length=5)
    following: List[PyObjectId] = Field(default_factory=list)
    followers: List[PyObjectId] = Field(default_factory=list)

    class Config:
        from_attributes = True
