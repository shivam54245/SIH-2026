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
@router.get("/myaccount/reminders")
def get_reminders(reminder_id: int = None, is_completed: bool = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.PATIENT}))):

    query = select(ReminderProfile).where(ReminderProfile.user_id == current_user.id)

    # Filters
    if reminder_id:
        query = query.where(ReminderProfile.id == reminder_id)

    if is_completed != None:
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


# Retrieves all game records for the calling patient. *(Filters: session_id, game_type, after_datetime)*
# PATIENT
@router.get("/myaccount/games")
def get_game_sessions(game_session_id: int = None, game_type: str = None, after_datetime: datetime = None, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.PATIENT}))):
    query = select(GamedataProfile).where(GamedataProfile.user_id == current_user.id)
    
    # Filters
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
                "game_type":game_record.game_type,
                "game_data":game_record.game_data,
                "last_modified": game_record.last_modified
            }
            for game_record in game_sessions
        ],
        message="Game session info retrieved successfully",
        error=None,
    )


# endregion



# region POST_ENDPOINTS 


# Creates a new reminder for the calling patient. (Pooled Data)
# PATIENT
@router.post("/myaccount/reminders", status_code=status.HTTP_201_CREATED)
def add_new_reminder(payload: PooledUserReminderRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.PATIENT}))):

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


# Creates new game records for any specified user. *(Pooled Data)*
# PATIENT
@router.post("/myaccount/games", status_code=status.HTTP_201_CREATED)
def add_new_game_session(payload: PooledUserGameSessionRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.PATIENT}))):

    game_sessions = []
    for item in payload.game_session:
        game_record = GamedataProfile(user_id=current_user.id, game_type=item.game_type, game_data=item.game_data)
        game_sessions.append(game_record)
    
    session.add_all(game_sessions)
    session.commit()
    for game_record in game_sessions:
        session.refresh(game_record)

    return ApiResponse(
        success=True,
        data={"game_session_ids": [g.id for g in game_sessions]},
        message="Game sessions added successfully",
        error=None,
    )


# endregion


