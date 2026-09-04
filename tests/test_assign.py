from sqlmodel import Session, select
from src.database import DoctorPatientLink, Role, UserProfile
from src.auth import hash_password


def test_admin_can_assign_patient_to_doctor(client, test_db_session: Session, admin_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    payload = {"doctor_id": doctor.id, "patient_id": patient.id}
    response = client.post("/assign", json=payload, headers=admin_headers)

    assert response.status_code == 201
    assert response.json()["success"] is True

    # Verify link exists in DB
    link = test_db_session.exec(
        select(DoctorPatientLink).where(
            DoctorPatientLink.doctor_id == doctor.id,
            DoctorPatientLink.patient_id == patient.id,
        )
    ).first()
    assert link is not None


def test_doctor_cannot_self_assign_patient(client, test_db_session: Session, doctor_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    payload = {"doctor_id": doctor.id, "patient_id": patient.id}
    response = client.post("/assign", json=payload, headers=doctor_headers)

    assert response.status_code == 403


def test_doctor_cannot_assign_patient_to_another_doctor(client, test_db_session: Session, doctor_headers):
    # Create another doctor in the session
    second_doctor = UserProfile(
        email="doctor2@example.com",
        full_name="Other Doctor",
        role=Role.DOCTOR,
        hashed_password=hash_password("doc2_pass"),
    )
    test_db_session.add(second_doctor)
    test_db_session.commit()
    test_db_session.refresh(second_doctor)

    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    # Logged-in doctor tries to assign patient to second_doctor
    payload = {"doctor_id": second_doctor.id, "patient_id": patient.id}
    response = client.post("/assign", json=payload, headers=doctor_headers)

    assert response.status_code == 403


def test_patient_cannot_access_assign(client, test_db_session: Session, patient_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    payload = {"doctor_id": doctor.id, "patient_id": patient.id}
    response = client.post("/assign", json=payload, headers=patient_headers)

    assert response.status_code == 403