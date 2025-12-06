from fastapi import FastAPI

from .config import Settings
from .controllers.auth import router as auth_router
from .controllers.devices import router as devices_router
from .controllers.profile import router as profile_router
from .controllers.telemetry import router as telemetry_router
from .database import init_db

settings = Settings()
app = FastAPI(title=settings.app_name)

app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(profile_router)
app.include_router(telemetry_router)


@app.on_event("startup")
def on_startup():
    init_db()