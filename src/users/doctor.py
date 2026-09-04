from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select

from src.auth import *
from src.database import *
from src.models import *

router = APIRouter(tags=["Doctor"])

# region GET_ENDPOINTS 


# Lists all patients actively assigned under the calling doctor. (Filters: patient_id)
# DOCTOR
@router.get("/self/patients")
def get_my_patients_info_requires_doctor(patient_id: int = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

    # Base query: join link table with UserProfile where the doctor is current_user
    query = (select(UserProfile).join(DoctorPatientLink, DoctorPatientLink.patient_id == UserProfile.id)
        .where(DoctorPatientLink.doctor_id == current_user.id))

    # filter
    if patient_id is not None:
        query = query.where(UserProfile.id == patient_id)

    patients = session.exec(query).all()

    return ApiResponse(
        success=True,
        data=[
        {
            "id": p.id,
            "full_name": p.full_name,
            "email": p.email,
            "role": p.role
        }
        for p in patients
    ],
        message="Assigned patients retrieved successfully",
        error=None,
    )


# Retrieves all scheduled reminders for a specific patient assigned under the calling doctor. (Filters: reminder_id)
# DOCTOR
@router.get("/self/patients/{patient_id}/reminders")
def get_my_patient_ke_reminders_requires_doctor(patient_id: int, reminder_id: int = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

    # 1. Verify doctor-patient care relationship
    link = session.exec(
        select(DoctorPatientLink).where(
            DoctorPatientLink.doctor_id == current_user.id,
            DoctorPatientLink.patient_id == patient_id,
        )
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PATIENT_NOT_ASSIGNED",
                "message": f"Patient with ID {patient_id} is not assigned to you or does not exist.",
            },
        )

    query = select(ReminderProfile).where(ReminderProfile.user_id == patient_id)

    # filters
    if reminder_id:
        query = query.where(ReminderProfile.id == reminder_id)

    reminders = session.exec(query).all()
    
    return ApiResponse(
        success=True,
        data=[
        {
            "id": r.id,
            "patient_id": r.user_id,
            "message": r.message,
            "time": r.time.isoformat() if hasattr(r.time, "isoformat") else str(r.time),
            "is_completed": r.is_completed,
            "last_modified": r.last_modified
        }
        for r in reminders
    ],
        message="Patient reminders retrieved successfully",
        error=None,
    )


# endregion




# region POST_ENDPOINTS


# Creates a new patient profile and automatically binds their care assignment to the calling doctor.
# DOCTOR
@router.post("/self/patients", status_code=status.HTTP_201_CREATED)
def add_my_new_patient_requires_doctor(payload: RegisterRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

    # Check if email already exists
    existing_user = session.exec(select(UserProfile).where(UserProfile.email == payload.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Email is already registered"})

    # Create user account
    new_user = UserProfile( email=payload.email, hashed_password=hash_password(payload.password),
                           full_name=payload.full_name, role=Role.PATIENT)
    session.add(new_user)
    session.flush()

    new_link = DoctorPatientLink(doctor_id=current_user.id, patient_id=new_user.id)
    session.add(new_link)
    session.commit()
    session.refresh(new_user)
    return ApiResponse(success=True, data={"user_id": new_user.id, "email": new_user.email},
                       message="User account created successfully", error=None)


# Schedules a new reminder for a specific patient under the doctor's supervision. (Pooled Data)
# DOCTOR
@router.post("/self/patients/{patient_id}/reminders", status_code=status.HTTP_201_CREATED)
def add_my_patient_ka_new_reminder_requires_doctor(patient_id: int, payload: PooledUserReminderRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

    # 1. Verify doctor-patient care relationship
    link = session.exec(
        select(DoctorPatientLink).where(
            DoctorPatientLink.doctor_id == current_user.id,
            DoctorPatientLink.patient_id == patient_id,
        )
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PATIENT_NOT_ASSIGNED",
                "message": f"Patient with ID {patient_id} is not assigned to you or does not exist.",
            },
        )

    reminders = []
    for item in payload.reminder:
        reminder = ReminderProfile(user_id=patient_id, time=item.time, message=item.message, is_completed=item.is_completed)
        reminders.append(reminder)

    session.add_all(reminders)
    session.commit()
    for reminder in reminders:
        session.refresh(reminder)

    return ApiResponse(
        success=True,
        data={"reminder_ids": [r.id for r in reminders]},
        message="Reminders added successfully",
        error=None,
    )



# endregion