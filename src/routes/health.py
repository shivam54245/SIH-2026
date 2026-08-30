from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def home():
    return {"status": "Database and Server are active!"}
