from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = ""
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: Optional[str] = ""


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None