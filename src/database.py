"""Shared database configuration and session dependency."""

import os
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel
from sqlalchemy import Engine, event
from sqlmodel import SQLModel, Session, create_engine

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorPayload(BaseModel):
    code: str
    details: Optional[List[ErrorDetail]] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str
    error: Optional[ErrorPayload] = None


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_QjanXo6OyEd2@ep-plain-paper-azfuivch-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass


def create_db_and_tables():
    """Create all database tables for SQLModel models."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session for each request."""
    with Session(engine) as session:
        yield session
