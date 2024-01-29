from pydantic import BaseModel, EmailStr
from typing import Optional


class Registration(BaseModel):
    name: str
    login: str
    password: str
    email: Optional[EmailStr] = None


class GuestLogin(BaseModel):
    name: str


class UpdateName(BaseModel):
    new_name: str


class Message(BaseModel):
    text: str
    room: str


class Typing(BaseModel):
    room: str
