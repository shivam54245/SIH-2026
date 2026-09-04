from typing import List, Optional
from pydantic import BaseModel, EmailStr

from src.database import Role




class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


class AssignDoctorRequest(BaseModel):
    doctor_id: int
    patient_id: int


# Pooled request models for batch operations

class PooledReminderRequest(BaseModel):
    reminder: List[ReminderRequest]


class PooledUserReminderRequest(BaseModel):
    reminder: List[UserReminderRequest]


