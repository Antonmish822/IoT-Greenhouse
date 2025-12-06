from .auth import router as auth_router
from .devices import router as devices_router
from .profile import router as profile_router

__all__ = ["auth_router", "devices_router", "profile_router"]