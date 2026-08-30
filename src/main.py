from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import create_db_and_tables
from src.routes.auth import (
    LoginRequest,
    RegisterRequest,
    login_user,
    register_doctor,
    register_patient,
    register_user,
    router as auth_router,
)
from src.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Dementia Care", lifespan=lifespan)
app.include_router(health_router)
app.include_router(auth_router)

__all__ = [
    "app",
    "LoginRequest",
    "RegisterRequest",
    "login_user",
    "register_user",
    "register_doctor",
    "register_patient",
]
