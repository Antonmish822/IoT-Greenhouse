from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AutomationSettingBase(BaseModel):
    auto_mode: bool = Field(
        default=False,
        description="Флаг включения автоматического режима управления",
    )
    target_temperature: float = Field(
        default=25.0,
        ge=10.0,
        le=40.0,
        description="Желаемая температура в градусах Цельсия",
    )
    hysteresis: float = Field(
        default=2.0,
        ge=0.5,
        le=10.0,
        description="Минимальное расстояние между порогами открытия и закрытия",
    )


class AutomationSettingCreate(AutomationSettingBase):
    pass


class AutomationSettingUpdate(BaseModel):
    auto_mode: bool | None = Field(
        default=None,
        description="Флаг автоматического режима",
    )
    target_temperature: float | None = Field(
        default=None,
        ge=10.0,
        le=40.0,
        description="Желаемая температура для управления",
    )
    hysteresis: float | None = Field(
        default=None,
        ge=0.5,
        le=10.0,
        description="Минимальное расстояние между порогами",
    )


class AutomationSettingRead(AutomationSettingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    greenhouse_id: int
    last_action: str | None = Field(
        default=None,
        description="Последняя команда, отправленная в автоматическом режиме",
    )
    last_action_at: datetime | None = Field(
        default=None,
        description="Время последней автоматической команды",
    )
    updated_at: datetime
