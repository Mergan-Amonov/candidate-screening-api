from typing import Literal
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "recruiter"]


class UserLogin(BaseModel):
    email: EmailStr
    password: str
