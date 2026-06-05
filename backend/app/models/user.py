from datetime import datetime
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional


class User(Document):
    username: str = Field(..., description="用户名", unique=True, index=True)
    password_hash: str = Field(..., description="密码哈希")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"
        indexes = [
            [("username", 1)],
        ]


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class TokenData(BaseModel):
    username: Optional[str] = None
