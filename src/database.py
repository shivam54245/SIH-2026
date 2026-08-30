"""Shared database configuration and session dependency."""

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


sqlite_file_name = "dementiaCare.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    """Create all database tables for SQLModel models."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session for each request."""
    with Session(engine) as session:
        yield session


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
