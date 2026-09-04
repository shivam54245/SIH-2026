from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select

from src.auth import *
from src.database import *
from src.models import *

router = APIRouter(tags=["Doctor"])

# region GET_ENDPOINTS 


# Lists all patients actively assigned under the calling doctor. (Filters: patient_id)
# DOCTOR
@router.get("/myaccount/patients")
def get_patients(patient_id: int = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

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


# Retrieves all scheduled reminders for patients assigned under the calling doctor. (Filters: reminder_id)
# DOCTOR
@router.get("/myaccount/patients/reminders")
def get_patients_reminders(patient_id: int = None, reminder_id: int = None, is_completed: bool = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

    # 1. Fetch all assigned patient IDs for this doctor
    assigned_stmt = select(DoctorPatientLink.patient_id).where(
        DoctorPatientLink.doctor_id == current_user.id
    )
    assigned_patient_ids = session.exec(assigned_stmt).all()

    if not assigned_patient_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PATIENT_NOT_ASSIGNED",
                "message": "No patients are currently assigned to this doctor.",
            },
        )

    # 2. Scope verification: ensure requested patient_id belongs to this doctor
    if patient_id is not None:
        if patient_id not in assigned_patient_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCESS_DENIED",
                    "message": "You do not have permission to view this patient's records.",
                },
            )
        target_ids = [patient_id]
    else:
        target_ids = assigned_patient_ids

    # 3. Filter
    query = select(ReminderProfile).where(ReminderProfile.user_id.in_(target_ids))

    if reminder_id is not None:
        query = query.where(ReminderProfile.id == reminder_id)

    if after_datetime is not None:
        query = query.where(ReminderProfile.last_modified >= after_datetime)

    if is_completed is not None:
        query = query.where(ReminderProfile.is_completed == is_completed)

    reminders = session.exec(query).all()

    return ApiResponse(
        success=True,
        data=[
            {
                "id": r.id,
                "patient_id": r.user_id,
                "message": r.message,
                "time": r.last_modified,
                "is_completed": r.is_completed,
                "last_modified": r.last_modified,
            }
            for r in reminders
        ],
        message="Patient reminders retrieved successfully",
        error=None,
    )


# Retrieves all game records for a specific patient assigned under the calling doctor. *(Filters: session_id, game_type, after_datetime)*
# DOCTOR
@router.get("/myaccount/patients/games")
def get_patients_game_sessions(patient_id: int = None, session_id: int = None, game_type: str = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):
    return "Yet to be implemented."




# endregion




# region POST_ENDPOINTS


# Creates a new patient profile and automatically binds their care assignment to the calling doctor.
# DOCTOR
@router.post("/myaccount/patients", status_code=status.HTTP_201_CREATED)
def add_new_patient(payload: RegisterRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

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
@router.post("/myaccount/patients/reminders", status_code=status.HTTP_201_CREATED)
def add_patients_new_reminder(payload: PooledReminderRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.DOCTOR}))):

    reminders = []
    for item in payload.reminder:
        link = session.exec(
            select(DoctorPatientLink).where(
                DoctorPatientLink.doctor_id == current_user.id,
                DoctorPatientLink.patient_id == item.patient_id,
            )
        ).first()

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "PATIENT_NOT_ASSIGNED",
                    "message": f"Patient with ID {item.patient_id} is not assigned to you or does not exist.",
                },
            )

        reminder = ReminderProfile(user_id=item.patient_id, time=item.time, message=item.message, is_completed=item.is_completed)
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