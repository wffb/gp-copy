from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
	email: EmailStr
	password: str


class RegisterRequest(BaseModel):
	email: EmailStr
	first_name: str = Field(..., min_length=1)
	last_name: str = Field(..., min_length=1)
	password: str = Field(..., min_length=1)
	display_name: str = Field(..., min_length=1)


class VerifyEmailRequest(BaseModel):
	token: str


class ResendEmailVerificationRequest(BaseModel):
	email: EmailStr
	password: str
