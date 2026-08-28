"""
AI GENERATED:
    -> Contains classes that represents the database schema and relationships
"""

from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship


# AUTHENTICATION & ROLE IDENTITIES
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.PATIENT, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 1:1 Links to Role-Specific Profiles
    doctor_profile: Optional["DoctorProfile"] = Relationship(back_populates="user")
    patient_profile: Optional["PatientProfile"] = Relationship(back_populates="user")



# PROFILES & DOCTOR-PATIENT ASSIGNMENTS
class DoctorProfile(SQLModel, table=True):
    __tablename__ = "doctor_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    full_name: str
    specialization: Optional[str] = None

    user: Optional[User] = Relationship(back_populates="doctor_profile")
    patients: List["PatientProfile"] = Relationship(back_populates="assigned_doctor")

class PatientProfile(SQLModel, table=True):
    __tablename__ = "patient_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    assigned_doctor_id: Optional[int] = Field(default=None, foreign_key="doctor_profiles.id", index=True)
    full_name: str
    stage_of_care: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="patient_profile")
    assigned_doctor: Optional[DoctorProfile] = Relationship(back_populates="patients")
    game_sessions: List["GameSession"] = Relationship(back_populates="patient")
    reminders: List["PatientReminder"] = Relationship(back_populates="patient")



# DYNAMIC GAME REGISTRY & SESSION TRACKING
class GameType(SQLModel, table=True):
    __tablename__ = "game_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code_name: str = Field(unique=True, index=True) # e.g. "CARD_MATCH"
    display_title: str
    schema_config: str = Field(default="{}") # Expected metrics blueprint (JSON)
    is_active: bool = Field(default=True)

    sessions: List["GameSession"] = Relationship(back_populates="game_type")

class GameSession(SQLModel, table=True):
    __tablename__ = "game_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profiles.id", index=True)
    game_id: int = Field(foreign_key="game_types.id", index=True)
    session_data: str = Field(default="{}") # Raw polymorphic JSON metrics
    session_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    patient: Optional[PatientProfile] = Relationship(back_populates="game_sessions")
    game_type: Optional[GameType] = Relationship(back_populates="sessions")



# NOTIFICATIONS, REMINDERS & LOGS
class ReminderTemplate(SQLModel, table=True):
    __tablename__ = "reminder_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    task: str # Standard template task description
    default_time_slot: str # e.g., "09:00 AM"
    is_active: bool = Field(default=True)

class PatientReminder(SQLModel, table=True):
    __tablename__ = "patient_reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profiles.id", index=True)
    template_id: Optional[int] = Field(default=None, foreign_key="reminder_templates.id")
    custom_task_override: Optional[str] = None
    time_slot: str # e.g., "08:30 AM"

    patient: Optional[PatientProfile] = Relationship(back_populates="reminders")
    logs: List["ReminderLog"] = Relationship(back_populates="reminder")

class ReminderLog(SQLModel, table=True):
    __tablename__ = "reminder_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    reminder_id: int = Field(foreign_key="patient_reminders.id", index=True)
    log_date: date = Field(default_factory=date.today, index=True)
    is_done: bool = Field(default=False)

    reminder: Optional[PatientReminder] = Relationship(back_populates="logs")