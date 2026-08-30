from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, model_validator
from sqlmodel import Session

from src.database import get_session
from src.models.user_models import StageOfCare, UserRole
from src.services.auth_service import create_user_account

router = APIRouter(prefix="/api/auth")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.PATIENT
    full_name: str
    specialization: str | None = None
    stage_of_care: StageOfCare | None = None
    assigned_doctor_id: int | None = None

    @model_validator(mode="after")
    def validate_stage_of_care(self):
        if self.role == UserRole.PATIENT and self.stage_of_care is None:
            raise ValueError("stage_of_care is required for patients")
        return self


@router.post("/register")
def register_user(payload: RegisterRequest, session: Session = Depends(get_session)):
    return create_user_account(payload, session)
