"""
AI GENERATED:
    -> Contains the main script that initializes FastAPI
"""


from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from database import create_db_and_tables, ApiResponse, get_session, ErrorPayload
from pydantic import BaseModel, EmailStr, model_validator
from sqlmodel import Session, select
from userTypes import User, UserRole, DoctorProfile, PatientProfile, StageOfCare
from authenticator import hash_password



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Dementia Care", lifespan=lifespan)



# LANDING PAGE

@app.get("/")
def home():
    return {"status": "Database and Server are active!"}



# --- 1. SCHEMAS (What data the user sends to register) ---
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


# --- 2. REGISTRATION ROUTE ---
@app.post(
    "/api/auth/register",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED
)
def register_user(payload: RegisterRequest, session: Session = Depends(get_session)):
    # Check if email is already registered
    existing_user = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Email is already registered"}
        )

    assigned_doctor_profile_id = None

    # Validate role-specific checks before creating the user.
    if payload.role == UserRole.PATIENT:
        if payload.assigned_doctor_id is not None:
            doctor_profile = session.exec(
                select(DoctorProfile).where(DoctorProfile.user_id == payload.assigned_doctor_id)
            ).first()
            if not doctor_profile:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail={"code": "ASSIGNED_DOCTOR_NOT_FOUND", "message": "Check the assigned doctor ID"}
                )
            assigned_doctor_profile_id = doctor_profile.id

    # 1. Create and save the base User account
    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # 2. Automatically create the matching profile based on role
    if payload.role == UserRole.DOCTOR:
        doctor_profile = DoctorProfile(
            user_id=new_user.id,
            full_name=payload.full_name,
            specialization=payload.specialization,
        )
        session.add(doctor_profile)
    elif payload.role == UserRole.PATIENT:
        patient_profile = PatientProfile(
            user_id=new_user.id,
            full_name=payload.full_name,
            stage_of_care=payload.stage_of_care,
            assigned_doctor_id=assigned_doctor_profile_id,
        )
        session.add(patient_profile)

    session.commit()

    return ApiResponse(
        success=True,
        data={"user_id": new_user.id, "email": new_user.email, "role": new_user.role},
        message="Account created successfully",
        error=None
    )