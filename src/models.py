from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, EmailStr

from src.database import Role


T = TypeVar("T")


# Error Models

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorPayload(BaseModel):
    code: str
    details: Optional[List[ErrorDetail]] = None


# Response Models

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str
    error: Optional[ErrorPayload] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"



# Request Models

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[Role] = Role.PATIENT


class ReminderRequest(BaseModel):
    patient_id: int
    message: str
    time: str   #(HH:MM FORMAT)
    is_completed: Optional[bool] = False


class UserReminderRequest(BaseModel):
    message: str
    time: str
    is_completed: Optional[bool] = False


class GameSessionRequest(BaseModel):
    patient_id: int
    game_type: str
    game_data: str


class UserGameSessionRequest(BaseModel):
    game_type: str
    game_data: str


class AssignDoctorRequest(BaseModel):
    doctor_id: int
    patient_id: int


# Pooled Request Models for batch operations

class PooledReminderRequest(BaseModel):
    reminder: List[ReminderRequest]


class PooledUserReminderRequest(BaseModel):
    reminder: List[UserReminderRequest]


class PooledGameSessionRequest(BaseModel):
    game_session: List[GameSessionRequest]


class PooledUserGameSessionRequest(BaseModel):
    game_session: List[UserGameSessionRequest]

    
