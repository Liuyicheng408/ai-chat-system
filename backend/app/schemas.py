"""Pydantic 出入参。"""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer, field_validator


def _as_utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


UTCDateTime = Annotated[datetime, PlainSerializer(_as_utc_iso, return_type=str)]


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=512)  # RSA 密文
    nickname: str | None = Field(default=None, max_length=30)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str
    email: str | None = None
    avatar: str | None = None
    bio: str | None = None
    created_at: UTCDateTime | None = None

    model_config = {"from_attributes": True}


class ProfileIn(BaseModel):
    nickname: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)
    avatar: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=255)


class PasswordIn(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _len(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少 8 位")
        return v


class ConversationOut(BaseModel):
    id: int
    title: str
    model_id: str
    created_at: UTCDateTime | None = None
    updated_at: UTCDateTime | None = None

    model_config = {"from_attributes": True}


class ConversationIn(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    model_id: str | None = None


class ConversationPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    model_id: str | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model_id: str | None = None
    created_at: UTCDateTime | None = None

    model_config = {"from_attributes": True}


class ChatIn(BaseModel):
    conversation_id: int
    content: str = Field(min_length=1, max_length=20000)
    model_id: str | None = None
