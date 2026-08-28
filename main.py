"""
AI GENERATED:
    -> Contains the main script that initializes FastAPI
"""


from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables
import models

# TODO: Understand this bit.
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Cognitive Dementia Care Platform", lifespan=lifespan)


# LANDING PAGE

@app.get("/")
def home():
    return {"status": "Database and Server are active!"}