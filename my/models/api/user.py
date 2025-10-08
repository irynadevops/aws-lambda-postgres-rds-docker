from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[UUID] = None
