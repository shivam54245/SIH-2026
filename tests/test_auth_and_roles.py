import pytest
from sqlmodel import Session, select
from src.database import UserProfile


def test_endpoints_reject_unauthenticated_requests(client):
    # Missing Bearer token entirely
    assert client.get("/myaccount").status_code in (401, 403)
    assert client.post("/myaccount/patients", json={}).status_code in (401, 403)
    assert client.get("/myaccount/patients/reminders").status_code in (401, 403)
    assert client.post("/myaccount/patients/reminders", json={}).status_code in (401, 403)
    assert client.post("/assign", json={}).status_code in (401, 403)


def test_patients_cannot_access_doctor_endpoints(client, patient_headers):
    # Patient attempting doctor operations
    res_get_patients = client.get("/myaccount/patients", headers=patient_headers)
    assert res_get_patients.status_code == 403

    res_post_patient = client.post(
        "/myaccount/patients",
        json={"email": "fake@test.com", "password": "pass", "full_name": "Fake"},
        headers=patient_headers,
    )
    assert res_post_patient.status_code == 403

    res_reminders = client.get("/myaccount/patients/reminders", params={"patient_id": 1}, headers=patient_headers)
    assert res_reminders.status_code == 403


def test_admin_cannot_access_doctor_self_endpoints(client, admin_headers):
    # Admins are not doctors; self-tenant endpoints should reject them
    res_patients = client.get("/myaccount/patients", headers=admin_headers)
    assert res_patients.status_code == 403