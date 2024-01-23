from pydantic import BaseModel


class Registration(BaseModel):
    name: str


class Message(BaseModel):
    text: str
    room: str


class Typing(BaseModel):
    room: str
