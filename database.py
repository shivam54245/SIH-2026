"""
AI GENERATED:
    -> Contains unchanging core functionalites common to almost every database
"""


from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine, Session


# 1. STANDARDIZED API RESPONSE ENVELOPES
T = TypeVar("T")

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str

class ErrorPayload(BaseModel):
    code: str
    details: Optional[List[ErrorDetail]] = None

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str
    error: Optional[ErrorPayload] = None



# 2. SQLITE CONNECTION & ENGINE INITIALIZATION
sqlite_file_name = "dementiaCare.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url, 
    echo=False, 
    connect_args={"check_same_thread": False}
)


# 3. SCHEMA INITIALIZATION & SESSION DEPENDENCY
def create_db_and_tables():
    """Scans all registered SQLModel classes and builds SQLite tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """FastAPI dependency that yields an isolated transaction session per request."""
    with Session(engine) as session:
        yield session