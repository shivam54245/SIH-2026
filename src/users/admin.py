from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from datetime import datetime

from src.auth import *
from src.database import *
from src.models import *


router = APIRouter(tags=["Admin"])

# region GET_ENDPOINTS 


# Retrieves a list of all registered users. (Filters: user_id, role, after_datetime)
# ADMIN
@router.get("/users")
def get_all_users(user_id: int = None, role: Role = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

    query = select(UserProfile)

    # Filters
    if user_id:
        query = query.where(UserProfile.id == user_id)

    if role:
        query = query.where(UserProfile.role == role)

    if after_datetime:
        query = query.where(UserProfile.last_modified >= after_datetime)
    

    users = session.exec(query).all()

    return ApiResponse(
        success=True,
        data=[
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "last_modified": user.last_modified
            }
            for user in users
        ],
        message="User info retrieved successfully",
        error=None,
    )


# Retrieves a list of all reminders form all patients. (Filters: reminder_id, patient_id, is_completed, after_datetime)
# ADMIN
@router.get("/reminders")
def get_all_reminders(patient_id: int = None, reminder_id: int = None, is_completed: bool = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

    query = select(ReminderProfile)

    # Filters
    if patient_id:
        query = query.where(ReminderProfile.user_id == patient_id)

    if reminder_id:
        query = query.where(ReminderProfile.id == reminder_id)

    if is_completed is not None:
        query = query.where(ReminderProfile.is_completed == is_completed)

    if after_datetime:
        query = query.where(ReminderProfile.last_modified >= after_datetime)

    reminders = session.exec(query).all()

    return ApiResponse(
        success=True,
        data=[
            {
                "id": reminder.id,
                "user_id": reminder.user_id,
                "message": reminder.message,
                "time": reminder.time,
                "is_completed": reminder.is_completed,
                "last_modified": reminder.last_modified
                
            }
            for reminder in reminders
        ],
        message="Reminder info retrieved successfully",
        error=None,
    )


# Retrieves all game records for the calling patient. *(Filters: game_session_id, game_type, after_datetime)*
# ADMIN
@router.get("/games")
def get_all_game_sessions(patient_id: int = None, game_session_id: int = None, game_type: str = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

    query = select(GamedataProfile)
    
    # Filters
    if patient_id:
        query = query.where(GamedataProfile.user_id == patient_id)

    if game_session_id:
        query = query.where(GamedataProfile.id == game_session_id)

    if game_type:
        query = query.where(GamedataProfile.game_type == game_type)

    if after_datetime:
        query = query.where(GamedataProfile.last_modified >= after_datetime)

    game_sessions = session.exec(query).all()

    return ApiResponse(
        success=True,
        data=[
            {
                "id": game_record.id,
                "user_id": game_record.user_id,
                "game_type": game_record.game_type,
                "game_data": game_record.game_data,
                "last_modified": game_record.last_modified
                
            }
            for game_record in game_sessions
        ],
        message="Game session info retrieved successfully",
        error=None,
    )


# endregion



# region POST_ENDPOINTS


# Creates a new user profile.
# ADMIN
@router.post("/users", status_code=status.HTTP_201_CREATED)
def add_new_user(payload: RegisterRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

    # Check if email already exists
    existing_user = session.exec(select(UserProfile).where(UserProfile.email == payload.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email is already registered",
            },
        )

    # Create user account
    new_user = UserProfile(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return ApiResponse(
        success=True,
        data={"user_id": new_user.id, "email": new_user.email},
        message="User account created successfully",
        error=None,
    )
    

# Binds the care of the patient under the doctor's supervision
# ADMIN, DOCTOR
@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_patient_to_doctor(payload: AssignDoctorRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

    # 2. Validate Doctor existence and role
    doctor = session.get(UserProfile, payload.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {payload.doctor_id} not found or is not a doctor",
        )

    # 3. Validate Patient existence and role
    patient = session.get(UserProfile, payload.patient_id)
    if not patient or patient.role != Role.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {payload.patient_id} not found or is not a patient",
        )

    # 4. Check for duplicate assignment
    existing_link = session.exec(
        select(DoctorPatientLink).where(
            DoctorPatientLink.doctor_id == payload.doctor_id,
            DoctorPatientLink.patient_id == payload.patient_id,
        )
    ).first()

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This patient is already assigned to this doctor",
        )

    # 5. Persist link
    new_link = DoctorPatientLink(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
    )
    session.add(new_link)
    session.commit()
    session.refresh(new_link)

    return {
        "success": True,
        "message": "Patient successfully assigned to doctor",
        "data": {
            "link_id": new_link.id,
            "doctor_id": new_link.doctor_id,
            "patient_id": new_link.patient_id,
            "assigned_at": new_link.assigned_at.isoformat(),
        },
    }


# Creates a reminder record for any specified user. (Pooled Data)
# ADMIN
@router.post("/reminders", status_code=status.HTTP_201_CREATED)
def add_new_reminders_for_all_patients(payload: PooledReminderRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):
    reminders = []
    for item in payload.reminder:
        # Check if patient_id belongs to a patient
        patient = session.get(UserProfile, item.patient_id)
        if not patient or patient.role != Role.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PATIENT_ID",
                    "message": "User is not a patient or does not exist",
                },
            )

        reminder = ReminderProfile(user_id=item.patient_id, time=item.time,
                                   message=item.message, is_completed=item.is_completed)
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


# Creates new game records for any specified user. (Pooled Data)
# ADMIN
@router.post("/games", status_code=status.HTTP_201_CREATED)
def add_new_game_sessions_for_all_patients(payload: PooledGameSessionRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):
    
    game_sessions = []
    for item in payload.game_session:
        # Check if patient_id belongs to a patient
        patient = session.get(UserProfile, item.patient_id)
        if not patient or patient.role != Role.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PATIENT_ID",
                    "message": "User is not a patient or does not exist",
                },
            )

        game_data = GamedataProfile(user_id=item.patient_id, game_type=item.game_type, game_data=item.game_data)
        game_sessions.append(game_data)

    session.add_all(game_sessions)
    session.commit()
    for game_data in game_sessions:
        session.refresh(game_data)

    return ApiResponse(
        success=True,
        data={"game_session_ids": [g.id for g in game_sessions]},
        message="Game Session added successfully",
        error=None,
    )


# endregion