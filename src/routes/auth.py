from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, model_validator
from sqlmodel import Session

from src.database import get_session
from src.models.user_models import StageOfCare, UserRole
from src.services.auth_service import create_user_account, login_user_account

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


class LoginRequest(BaseModel):
    user_id: int
    password: str


@router.post("/register")
def register_user(payload: RegisterRequest, session: Session = Depends(get_session)):
    return create_user_account(payload, session)


@router.post("/login")
def login_user(payload: LoginRequest | dict, session: Session = Depends(get_session)):
    if isinstance(payload, dict):
        payload = LoginRequest(**payload)
    return login_user_account(payload.user_id, payload.password, session)


@router.post("/doctor/register")
def register_doctor(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
    actor_role: UserRole | None = None,
):
    if actor_role is None or actor_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Only admins can register doctors"},
        )
    payload.role = UserRole.DOCTOR
    return create_user_account(payload, session)


@router.post("/patient/register")
def register_patient(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
    actor_role: UserRole | None = None,
):
    if actor_role is None or actor_role not in {UserRole.ADMIN, UserRole.DOCTOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_OR_DOCTOR_REQUIRED",
                "message": "Only admins or doctors can register patients",
            },
        )
    payload.role = UserRole.PATIENT
    return create_user_account(payload, session)
