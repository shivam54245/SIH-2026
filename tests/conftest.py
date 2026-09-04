import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.auth import hash_password
from src.database import Role, UserProfile, get_session
from main import app

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="function")
def test_db_session():
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        users = [
            UserProfile(
                email="admin@example.com",
                full_name="System Admin",
                role=Role.ADMIN,
                hashed_password=hash_password("admin_pass"),
            ),
            UserProfile(
                email="doctor@example.com",
                full_name="Assigned Doctor",
                role=Role.DOCTOR,
                hashed_password=hash_password("doctor_pass"),
            ),
            UserProfile(
                email="patient@example.com",
                full_name="Assigned Patient",
                role=Role.PATIENT,
                hashed_password=hash_password("patient_pass"),
            ),
        ]
        session.add_all(users)
        session.commit()
        yield session

    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def client(test_db_session: Session):
    def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authenticate_user(client: TestClient, email: str, password: str) -> dict:
    res = client.post("/myaccount", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client: TestClient):
    return authenticate_user(client, "admin@example.com", "admin_pass")


@pytest.fixture(scope="function")
def doctor_headers(client: TestClient):
    return authenticate_user(client, "doctor@example.com", "doctor_pass")


@pytest.fixture(scope="function")
def patient_headers(client: TestClient):
    return authenticate_user(client, "patient@example.com", "patient_pass")