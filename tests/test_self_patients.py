from sqlmodel import Session, select
from database import DoctorPatientLink, Role, UserProfile
from auth import hash_password
from conftest import authenticate_user


def test_doctor_creates_patient_and_auto_binds(client, test_db_session: Session, doctor_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()

    payload = {
        "email": "newpatient@example.com",
        "password": "patient_secure_pass",
        "full_name": "Automatically Assigned Patient",
        "role": Role.PATIENT,
    }

    response = client.post("/self/patients", json=payload, headers=doctor_headers)
    assert response.status_code == 201

    created_id = response.json()["data"]["user_id"]

    # 1. Assert user exists in database with Role.PATIENT
    created_user = test_db_session.get(UserProfile, created_id)
    assert created_user is not None
    assert created_user.email == "newpatient@example.com"
    assert created_user.role == Role.PATIENT

    # 2. Assert DoctorPatientLink was automatically created in the same transaction
    link = test_db_session.exec(
        select(DoctorPatientLink).where(
            DoctorPatientLink.doctor_id == doctor.id,
            DoctorPatientLink.patient_id == created_id,
        )
    ).first()
    assert link is not None


def test_get_my_patients_isolation(client, test_db_session: Session, doctor_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    # Link seeded patient to the logged-in doctor
    test_db_session.add(DoctorPatientLink(doctor_id=doctor.id, patient_id=patient.id))
    test_db_session.commit()

    # Logged-in doctor should see the patient
    res1 = client.get("/self/patients", headers=doctor_headers)
    assert res1.status_code == 200
    assert len(res1.json()["data"]) == 1
    assert res1.json()["data"][0]["id"] == patient.id

    # Create and authenticate a second doctor
    other_doctor = UserProfile(
        email="doctor2@example.com",
        full_name="Second Doctor",
        role=Role.DOCTOR,
        hashed_password=hash_password("doc2_pass"),
    )
    test_db_session.add(other_doctor)
    test_db_session.commit()

    other_doctor_headers = authenticate_user(client, "doctor2@example.com", "doc2_pass")

    # Second doctor should see an empty list (tenant isolation)
    res2 = client.get("/self/patients", headers=other_doctor_headers)
    assert res2.status_code == 200
    assert len(res2.json()["data"]) == 0


def test_get_my_patients_filter_by_id(client, test_db_session: Session, doctor_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    test_db_session.add(DoctorPatientLink(doctor_id=doctor.id, patient_id=patient.id))
    test_db_session.commit()

    # Match ID
    res_match = client.get(f"/self/patients?patient_id={patient.id}", headers=doctor_headers)
    assert res_match.status_code == 200
    assert len(res_match.json()["data"]) == 1

    # Unmatched ID
    res_no_match = client.get("/self/patients?patient_id=9999", headers=doctor_headers)
    assert res_no_match.status_code == 200
    assert len(res_no_match.json()["data"]) == 0