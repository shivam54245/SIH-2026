from sqlmodel import Session, select
from src.database import DoctorPatientLink, ReminderProfile, Role, UserProfile
from src.auth import hash_password
from conftest import authenticate_user


def test_doctor_can_add_and_get_reminders_for_assigned_patient(client, test_db_session: Session, doctor_headers):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    # Assign patient to doctor
    test_db_session.add(DoctorPatientLink(doctor_id=doctor.id, patient_id=patient.id))
    test_db_session.commit()

    # Add pooled reminders
    payload = {
        "reminder": [
            {
                "message": "Take Metformin 500mg",
                "time": "2026-09-05T08:00:00",
                "is_completed": False,
            },
            {
                "message": "Check Blood Glucose",
                "time": "2026-09-05T12:00:00",
                "is_completed": False,
            },
        ]
    }

    create_res = client.post(f"/self/patients/{patient.id}/reminders", json=payload, headers=doctor_headers)
    assert create_res.status_code == 201

    # Fetch all reminders
    get_res = client.get(f"/self/patients/{patient.id}/reminders", headers=doctor_headers)
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 2

    # Fetch with specific reminder_id filter
    target_reminder_id = get_res.json()["data"][0]["id"]
    filter_res = client.get(
        f"/self/patients/{patient.id}/reminders?reminder_id={target_reminder_id}",
        headers=doctor_headers,
    )
    assert filter_res.status_code == 200
    assert len(filter_res.json()["data"]) == 1
    assert filter_res.json()["data"][0]["id"] == target_reminder_id


def test_doctor_cannot_add_reminders_to_unassigned_patient(client, test_db_session: Session, doctor_headers):
    # Unlinked patient from conftest
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    payload = {
        "reminder": [
            {
                "message": "Unauthorized Reminder",
                "time": "2026-09-05T08:00:00",
                "is_completed": False,
            }
        ]
    }

    response = client.post(f"/self/patients/{patient.id}/reminders", json=payload, headers=doctor_headers)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PATIENT_NOT_ASSIGNED"


def test_doctor_cannot_get_reminders_from_unassigned_patient(client, test_db_session: Session, doctor_headers):
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    # Reminders exist for patient, but doctor is not assigned
    test_db_session.add(
        ReminderProfile(
            user_id=patient.id,
            message="Independent Reminder",
            time="2026-09-05T08:00:00",
            is_completed=False,
        )
    )
    test_db_session.commit()

    response = client.get(f"/self/patients/{patient.id}/reminders", headers=doctor_headers)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PATIENT_NOT_ASSIGNED"