from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from datetime import datetime

from auth import *
from database import *
from models import *


router = APIRouter()

# region GET_ENDPOINTS 


# Retrieves a list of all registered users. (Filters: user_id, role, after_datetime)
# ADMIN
@router.get("/users")
def get_all_users_info_requires_admin(user_id: int = None, role: Role = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

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
def get_all_reminders_info_requires_admin(reminder_id: int = None, patient_id: int = None, is_completed: bool = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

    query = select(ReminderProfile)

    # Filters

    if reminder_id:
        query = query.where(ReminderProfile.id == reminder_id)

    if patient_id:
        query = query.where(ReminderProfile.user_id == patient_id)

    if after_datetime:
        query = query.where(ReminderProfile.last_modified >= after_datetime)

    if is_completed != None:
        query = query.where(ReminderProfile.is_completed == is_completed)

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


# endregion



# region POST_ENDPOINTS


# Creates a new user profile.
# ADMIN
@router.post("/users", status_code=status.HTTP_201_CREATED)
def add_new_user_requires_admin(payload: RegisterRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):

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


# Creates a reminder record for any specified user. (Pooled Data)
# ADMIN
@router.post("/reminders", status_code=status.HTTP_201_CREATED)
def add_new_reminder_requires_admin(payload: PooledReminderRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN}))):
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




# endregion