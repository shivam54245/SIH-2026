
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends
from sqlmodel import Session, select
from datetime import datetime

from auth import *
from database import *
from models import *


# APPLICATION SETUP

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="NER Chetna", lifespan=lifespan)




# region GET_ENDPOINTS 


# Health check endpoint to verify server status.
# PUBLIC
@app.get("/")
def health_and_setup():
    # add admin user if not exists
    with Session(engine) as session:
        default_admin = select(UserProfile).where(UserProfile.email == "user@example.com")
        existing_user = session.exec(default_admin).first()

        if not existing_user:
            new_user = UserProfile(email="user@example.com", hashed_password=hash_password("string"), full_name="string", role=Role.ADMIN)
            session.add(new_user)
            session.commit()
            session .refresh(new_user)

    return "Welcome to the Dementia Care API!"


# Retrieves account details for the current user.
# ADMIN, DOCTOR or PATIENT
@app.get("/self")
def get_my_account_info(current_user: UserProfile = Depends(require_roles({Role.ADMIN, Role.DOCTOR, Role.PATIENT}))):
    return ApiResponse(
        success=True,
        data={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "last_modified": current_user.last_modified
        },
        message="User info retrieved successfully",
        error=None,
    )


# Retrieves a list of all registered users. (Filters: user_id, role, after_datetime)
# ADMIN
@app.get("/users")
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
@app.get("/reminders")
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


# Retrieves all reminders for the calling patient. (Filters: reminder_id, is_completed, after_datetime)
# PATIENT
@app.get("/self/reminders")
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


# Lists all patients actively assigned under the calling doctor. (Filters: patient_id)
# DOCTOR
@app.get("/self/patients")
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
@app.get("/self/patients/{patient_id}/reminders")
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


# Creates an active session key for your account.
# PUBLIC
@app.post("/login", response_model=TokenResponse)
def login_via_email_and_password(payload: LoginRequest, session: Session = Depends(get_session)):
    # Query user by email
    user = session.exec(
        select(UserProfile).where(UserProfile.email == payload.email)
    ).first()

    # Validate user existence and password
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password",
            },
        )

    # Generate token with email as the subject claim
    token = create_access_token(data={"sub": user.email})

    return TokenResponse(access_token=token)


# Creates a new user profile.
# ADMIN
@app.post("/users", status_code=status.HTTP_201_CREATED)
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
@app.post("/reminders", status_code=status.HTTP_201_CREATED)
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


# Binds the care of the patient under the doctor's supervision
# ADMIN, DOCTOR
@app.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_patient_to_doctor_requires_admin_or_self_doctor(payload: AssignDoctorRequest, session: Session = Depends(get_session), current_user: UserProfile = Depends(require_roles({Role.ADMIN, Role.DOCTOR}))):

    # 1. Authorization: If caller is a DOCTOR, they can only assign patients to themselves
    if (
        current_user.role == Role.DOCTOR
        and current_user.id != payload.doctor_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors can only assign patients to their own care",
        )

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


# Creates a new reminder for the calling patient. (Pooled Data)
# PATIENT
@app.post("/self/reminders", status_code=status.HTTP_201_CREATED)
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


# Creates a new patient profile and automatically binds their care assignment to the calling doctor.
# DOCTOR
@app.post("/self/patients", status_code=status.HTTP_201_CREATED)
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
@app.post("/self/patients/{patient_id}/reminders", status_code=status.HTTP_201_CREATED)
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


