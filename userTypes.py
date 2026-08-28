"""
AI GENERATED:
    -> Contains classes that represents the database schema and relationships
"""

from typing import Optional, List
from datetime import date, datetime, time, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship


# AUTHENTICATION & ROLE IDENTITIES
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

    @classmethod
    # ENUM automatically calls _missing_ when a value is not found
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized_value = value.strip().upper()
            for role in cls:
                if role.value == normalized_value:
                    return role
        return None


class StageOfCare(str, Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            for stage in cls:
                if stage.value.lower() == normalized_value:
                    return stage
        return None


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.PATIENT, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 1:1 Links to Role-Specific Profiles (Cascade deletion if User is deleted)
    doctor_profile: Optional["DoctorProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    patient_profile: Optional["PatientProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# PROFILES & DOCTOR-PATIENT ASSIGNMENTS
class DoctorProfile(SQLModel, table=True):
    __tablename__ = "doctor_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        unique=True,
        index=True,
        ondelete="CASCADE"
    )
    full_name: str
    specialization: Optional[str] = None

    user: Optional[User] = Relationship(back_populates="doctor_profile")
    # Disassociating a doctor leaves patient records intact
    patients: List["PatientProfile"] = Relationship(back_populates="assigned_doctor")


class PatientProfile(SQLModel, table=True):
    __tablename__ = "patient_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        unique=True,
        index=True,
        ondelete="CASCADE"
    )
    assigned_doctor_id: Optional[int] = Field(
        default=None,
        foreign_key="doctor_profiles.id",
        index=True,
        ondelete="SET NULL"
    )
    full_name: str
    stage_of_care: StageOfCare
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: Optional[User] = Relationship(back_populates="patient_profile")
    assigned_doctor: Optional[DoctorProfile] = Relationship(back_populates="patients")
    
    # Cascade deletion: removing a patient removes their sessions and reminders
    game_sessions: List["GameSession"] = Relationship(
        back_populates="patient",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    reminders: List["PatientReminder"] = Relationship(
        back_populates="patient",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# DYNAMIC GAME REGISTRY & SESSION TRACKING
class GameType(SQLModel, table=True):
    __tablename__ = "game_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code_name: str = Field(unique=True, index=True)
    display_title: str
    schema_config: str = Field(default="{}")
    is_active: bool = Field(default=True)

    sessions: List["GameSession"] = Relationship(back_populates="game_type")


class GameSession(SQLModel, table=True):
    __tablename__ = "game_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(
        foreign_key="patient_profiles.id",
        index=True,
        ondelete="CASCADE"
    )
    game_id: int = Field(
        foreign_key="game_types.id",
        index=True,
        ondelete="RESTRICT"
    )
    session_data: str = Field(default="{}")
    session_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    patient: Optional[PatientProfile] = Relationship(back_populates="game_sessions")
    game_type: Optional[GameType] = Relationship(back_populates="sessions")


# NOTIFICATIONS, REMINDERS & LOGS
class ReminderTemplate(SQLModel, table=True):
    __tablename__ = "reminder_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    task: str
    default_time_slot: time
    is_active: bool = Field(default=True)


class PatientReminder(SQLModel, table=True):
    __tablename__ = "patient_reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(
        foreign_key="patient_profiles.id",
        index=True,
        ondelete="CASCADE"
    )
    template_id: Optional[int] = Field(
        default=None,
        foreign_key="reminder_templates.id",
        ondelete="SET NULL"
    )
    custom_task_override: Optional[str] = None
    time_slot: time

    patient: Optional[PatientProfile] = Relationship(back_populates="reminders")
    
    # Cascade deletion: deleting a reminder purges its logs
    logs: List["ReminderLog"] = Relationship(
        back_populates="reminder",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ReminderLog(SQLModel, table=True):
    __tablename__ = "reminder_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    reminder_id: int = Field(
        foreign_key="patient_reminders.id",
        index=True,
        ondelete="CASCADE"
    )
    log_date: date = Field(default_factory=date.today, index=True)
    is_done: bool = Field(default=False)

    reminder: Optional[PatientReminder] = Relationship(back_populates="logs")