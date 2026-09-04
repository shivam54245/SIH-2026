
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.auth import *
from src.database import *
from src.models import *

from src.users.admin import router as admin_router
from src.users.doctor import router as doctor_router
from src.users.patient import router as patient_router
from src.users.general import router as general_router


# APPLICATION SETUP

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

tags_metadata = [
    {
        "name": "General",
        "description": "Public and common platform endpoints such as authentication, and health checks.",
    },
    {
        "name": "Admin",
        "description": "Administrative control endpoints for role assignment and platform-wide user management.",
    },
    {
        "name": "Doctor",
        "description": "Doctor operations for managing assigned patients, scheduling pooled reminders, and monitoring care.",
    },
    {
        "name": "Patient",
        "description": "Patient self-service endpoints for viewing personal profiles, schedules, and active reminders.",
    },
]

app = FastAPI(title="NER_Chetna", lifespan=lifespan, 
              openapi_tags=tags_metadata, swagger_ui_parameters={"operationsSorter": "method"})

app.include_router(admin_router)
app.include_router(doctor_router)
app.include_router(patient_router)
app.include_router(general_router)


