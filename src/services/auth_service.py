from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.database import ApiResponse
from src.models.user_models import DoctorProfile, PatientProfile, User, UserRole
from src.utils.authenticator import hash_password, verify_password


def create_user_account(payload: "RegisterRequest", session: Session):
    existing_user = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Email is already registered"},
        )

    assigned_doctor_profile_id = None

    if payload.role == UserRole.PATIENT and payload.assigned_doctor_id is not None:
        doctor_profile = session.exec(
            select(DoctorProfile).where(DoctorProfile.user_id == payload.assigned_doctor_id)
        ).first()
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "ASSIGNED_DOCTOR_NOT_FOUND", "message": "Check the assigned doctor ID"},
            )
        assigned_doctor_profile_id = doctor_profile.id

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

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
        error=None,
    )


def login_user_account(user_id: int, password: str, session: Session):
    user = session.get(User, user_id)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "User ID or password is incorrect"},
        )

    return ApiResponse(
        success=True,
        data={"user_id": user.id, "email": user.email, "role": user.role},
        message="Login successful",
        error=None,
    )
