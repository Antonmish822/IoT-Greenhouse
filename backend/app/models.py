from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON
from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column_kwargs={"unique": True}, index=True, nullable=False)
    full_name: str = Field(default="")
    hashed_password: str
    is_active: bool = Field(default=True)


class Greenhouse(SQLModel, table=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    greenhouse_metadata: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column("greenhouse_metadata", JSON)
    )
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Device(SQLModel, table=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    serial_number: str = Field(
        sa_column_kwargs={"unique": True}, index=True, nullable=False
    )
    is_active: bool = Field(default=True)
    last_seen: Optional[datetime] = Field(default=None)
    device_metadata: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column("metadata", JSON)
    )
    greenhouse_id: Optional[int] = Field(default=None, foreign_key="greenhouse.id")
    user_id: int = Field(foreign_key="user.id")


class AutomationSetting(SQLModel, table=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    greenhouse_id: int = Field(foreign_key="greenhouse.id", index=True)
    auto_mode: bool = Field(default=False)
    target_temperature: float = Field(default=25.0)
    hysteresis: float = Field(default=2.0)
    last_action: Optional[str] = Field(default=None)
    last_action_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RefreshToken(SQLModel, table=True):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, nullable=False)
    user_id: int = Field(foreign_key="user.id")
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
