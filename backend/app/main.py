import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .controllers.auth import router as auth_router
from .controllers.automation import router as automation_router
from .controllers.devices import router as devices_router
from .controllers.greenhouses import router as greenhouses_router
from .controllers.profile import router as profile_router
from .controllers.telemetry import router as telemetry_router
from .controllers.rpc import router as rpc_router
from .database import init_db
from .services.automation import start_automation_loop

settings = Settings()
app = FastAPI(title=settings.app_name)

allowed_origins = [
    "http://localhost:8001",
    "http://localhost:8010",
    "http://127.0.0.1:8000",
]
if settings.frontend_allowed_origin:
    selected_origins = [
        origin.strip()
        for origin in settings.frontend_allowed_origin.split(",")
        if origin.strip()
    ]
    if selected_origins:
        allowed_origins = selected_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(automation_router)
app.include_router(devices_router)
app.include_router(greenhouses_router)
app.include_router(profile_router)
app.include_router(telemetry_router)
app.include_router(rpc_router)


@app.on_event("startup")
async def on_startup():
    init_db()
    asyncio.create_task(start_automation_loop(settings.automation_interval_seconds))
