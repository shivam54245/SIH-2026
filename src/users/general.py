from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select

from src.auth import *
from src.database import *
from src.models import *


router = APIRouter(tags=["General"])


# region GET_ENDPOINTS 


# Health check endpoint to verify server status.
# PUBLIC
@router.get("/")
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
@router.get("/self")
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



# endregion



# region POST_ENDPOINTS


# Creates an active session key for your account.
# PUBLIC
@router.post("/login", response_model=TokenResponse)
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



# endregion


