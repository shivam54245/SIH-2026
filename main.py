
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IllegalStateChangeError, OperationalError, ResourceClosedError, SQLAlchemyError

from src.auth import *
from src.database import *
from src.models import *

from src.users.general import router as general_router
from src.users.admin import router as admin_router
from src.users.doctor import router as doctor_router
from src.users.patient import router as patient_router


# APPLICATION SETUP

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

tags_metadata = [
    {"name": "General",
     "description": "Public and common platform endpoints such as authentication, and health checks."},

    {"name": "Admin",
     "description": "Administrative control endpoints for role assignment and platform-wide user management."},
    {"name": "Doctor",
     "description": "Doctor operations for managing assigned patients, scheduling pooled reminders, and monitoring care."},

    {"name": "Patient",
     "description": "Patient self-service endpoints for viewing personal profiles, schedules, and active reminders."}
    ]


app = FastAPI(title="NER_Chetna", lifespan=lifespan, 
              openapi_tags=tags_metadata, swagger_ui_parameters={"operationsSorter": "method"})

app.include_router(general_router)
app.include_router(admin_router)
app.include_router(doctor_router)
app.include_router(patient_router)




# Patches after stress testing


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    # jsonable_encoder replaces inf / -inf / nan with None/null or compliant strings,
    # preventing json.dumps from crashing with ValueError
    sanitized_errors = jsonable_encoder(
        exc.errors(), custom_encoder={float: lambda f: str(f)}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": sanitized_errors},
    )


@app.exception_handler(OverflowError)
async def overflow_error_handler(request: Request, exc: OverflowError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Numeric value exceeds maximum integer bounds.",
            "error": {"code": "INTEGER_OVERFLOW", "details": None}
        },
    )


@app.exception_handler(DBAPIError)
async def dbapi_error_handler(request: Request, exc: DBAPIError):
    # Intercepts driver-level integer conversions that bubble through SQLAlchemy
    if isinstance(exc.orig, OverflowError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Database numeric parameter overflow.",
                "error": {"code": "DB_NUMERIC_OVERFLOW", "details": None}
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Internal database error."},
    )


@app.exception_handler(IllegalStateChangeError)
async def state_change_exception_handler(
    request: Request, exc: IllegalStateChangeError
):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "message": "Database session transaction concurrency error.",
            "error": {"code": "CONCURRENCY_CONFLICT", "details": None},
        },
    )


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    if "locked" in str(exc).lower():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "Database is temporarily busy. Please retry.",
                "error": {"code": "DB_LOCKED", "details": None},
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Internal database error."},
    )


@app.exception_handler(ResourceClosedError)
async def resource_closed_exception_handler(request: Request, exc: ResourceClosedError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "message": "Database transaction closed prematurely due to concurrent access.",
            "error": {"code": "TRANSACTION_CLOSED", "details": None}
        }
    )

@app.exception_handler(SQLAlchemyError)
async def generic_sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Database operation failed.",
            "error": {"code": "DATABASE_ERROR", "details": str(exc.__class__.__name__)}
        }
    )