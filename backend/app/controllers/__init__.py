from .auth import router as auth_router
from .automation import router as automation_router
from .devices import router as devices_router
from .profile import router as profile_router
from .telemetry import router as telemetry_router

__all__ = [
    "auth_router",
    "automation_router",
    "devices_router",
    "profile_router",
    "telemetry_router",
]