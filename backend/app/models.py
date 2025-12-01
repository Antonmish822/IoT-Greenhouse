from typing import Optional

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column_kwargs={"unique": True}, index=True, nullable=False)
    full_name: str = Field(default="")
    hashed_password: str
    is_active: bool = Field(default=True)