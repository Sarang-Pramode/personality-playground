"""Auth request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, description="Email or username")
    password: str = Field(min_length=1)


class StatusUpdateRequest(BaseModel):
    status: Literal["approved", "denied", "revoked", "pending"]
