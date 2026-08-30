from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import create_db_and_tables
from src.routes.auth import RegisterRequest, register_user, router as auth_router
from src.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Dementia Care", lifespan=lifespan)
app.include_router(health_router)
app.include_router(auth_router)

__all__ = ["app", "RegisterRequest", "register_user"]
