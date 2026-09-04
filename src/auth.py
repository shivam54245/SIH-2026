
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Set
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session, select

from src.database import UserProfile, Role, get_session


# API TOKEN SYSTEM

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback_for_local_tests")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

pwd_context = PasswordHash.recommended()
security = HTTPBearer()

class TokenData(BaseModel):
    email: str
    role: Role

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[Session, Depends(get_session)], ) -> UserProfile:
    token = credentials.credentials


    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_CREDENTIALS", "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"}, )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = session.exec(select(UserProfile).where(UserProfile.email == email)).first()
    if user is None:
        raise credentials_exception
    return user

def require_roles(allowed_roles: Set[Role]):
    def role_checker(current_user: Annotated[UserProfile, Depends(get_current_user)]) -> UserProfile:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCESS_DENIED", "message": "Insufficient permissions to perform this action"},
            )
        return current_user
    return role_checker