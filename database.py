
from typing import Generic, List, Optional, TypeVar
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy import Engine, event
from sqlmodel import SQLModel, Session, Field, create_engine
from sqlalchemy import text, UniqueConstraint

T = TypeVar("T")



# ENUMS

class Role(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            for role in cls:
                if role.value.lower() == normalized_value:
                    return role
        return None


# USER TABLES

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    role: Role = Field(default=Role.PATIENT, nullable=False)

    # Automatic UTC timestamping
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={
            # Handles default generation at the SQL server level
            "server_default": text("CURRENT_TIMESTAMP"),
            # Updates timestamp on UPDATE queries in SQLAlchemy/Postgres
            "onupdate": lambda: datetime.now(timezone.utc),
        }
    )


class ReminderProfile(SQLModel, table=True):
    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user_accounts.id", nullable=False)
    message: str = Field(nullable=False)
    time: str = Field(nullable=False)
    is_completed: bool = Field(default=False, nullable=False)

    # Automatic UTC timestamping
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={
            # Handles default generation at the SQL server level
            "server_default": text("CURRENT_TIMESTAMP"),
            # Updates timestamp on UPDATE queries in SQLAlchemy/Postgres
            "onupdate": lambda: datetime.now(timezone.utc),
        }
    )


class GamedataProfile(SQLModel, table=True):
    __tablename__ = "game_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user_accounts.id", nullable=False)
    game_type: str = Field(nullable=False)
    game_data: str = Field(nullable=False)

    # Automatic UTC timestamping
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={
            # Handles default generation at the SQL server level
            "server_default": text("CURRENT_TIMESTAMP"),
            # Updates timestamp on UPDATE queries in SQLAlchemy/Postgres
            "onupdate": lambda: datetime.now(timezone.utc),
        }
    )


class DoctorPatientLink(SQLModel, table=True):
    __tablename__ = "doctor_patient_links"
    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "patient_id", name="uq_doctor_patient_pair"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(
        foreign_key="user_accounts.id", nullable=False, index=True
    )
    patient_id: int = Field(
        foreign_key="user_accounts.id", nullable=False, index=True
    )
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )





# MODELS

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




# DATABASE SETUP

sqlite_file_name = "NER Chetna.db"

engine = create_engine(
    f"sqlite:///{sqlite_file_name}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()



