from sqlmodel import Session, select
from database import Role, UserProfile


def test_assign_fails_when_doctor_does_not_exist(client, test_db_session: Session, admin_headers):
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    payload = {"doctor_id": 99999, "patient_id": patient.id}
    response = client.post("/assign", json=payload, headers=admin_headers)
    assert response.status_code == 404


def test_assign_fails_when_patient_does_not_exist(client, test_db_session: Session, admin_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()

    payload = {"doctor_id": doctor.id, "patient_id": 99999}
    response = client.post("/assign", json=payload, headers=admin_headers)
    assert response.status_code == 404


def test_assign_fails_if_roles_are_inverted(client, test_db_session: Session, admin_headers):
    # Attempting to assign doctor as the patient and patient as the doctor
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    payload = {"doctor_id": patient.id, "patient_id": doctor.id}
    response = client.post("/assign", json=payload, headers=admin_headers)
    
    # Must fail with either 404 Not Found or 422 Unprocessable based on your validator
    assert response.status_code in (404, 422)