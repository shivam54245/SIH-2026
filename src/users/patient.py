from fastapi import APIRouter, status, Depends
from sqlmodel import Session, select
from datetime import datetime

from src.auth import *
from src.database import *
from src.models import *

router = APIRouter(tags=["Patient"])

# region GET_ENDPOINTS 


# Retrieves all reminders for the calling patient. (Filters: reminder_id, is_completed, after_datetime)
# PATIENT
@router.get("/self/reminders")
def get_my_reminders_info_requires_patient(reminder_id: int = None, is_completed: bool = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.PATIENT}))):

    query = select(ReminderProfile).where(ReminderProfile.user_id == current_user.id)

    # Filters
    if reminder_id:
        query = query.where(ReminderProfile.id == reminder_id)

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


# Creates a new reminder for the calling patient. (Pooled Data)
# PATIENT
@router.post("/self/reminders", status_code=status.HTTP_201_CREATED)
def add_my_new_reminder_requires_patient(payload: PooledUserReminderRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.PATIENT}))):
    reminders = []
    for item in payload.reminder:
        reminder = ReminderProfile(user_id=current_user.id, time=item.time, message=item.message, is_completed=item.is_completed)
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


