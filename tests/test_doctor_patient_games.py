from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.database import DoctorPatientLink, UserProfile


def test_doctor_can_get_assigned_patient_games(
    client: TestClient,
    test_db_session: Session,
    doctor_headers: dict,
    patient_headers: dict,
):
    doctor = test_db_session.exec(
        select(UserProfile).where(UserProfile.email == "doctor@example.com")
    ).first()
    patient = test_db_session.exec(
        select(UserProfile).where(UserProfile.email == "patient@example.com")
    ).first()

    # Link doctor to patient
    test_db_session.add(DoctorPatientLink(doctor_id=doctor.id, patient_id=patient.id))
    test_db_session.commit()

    # Create record via patient self-service endpoint using pooled schema
    post_res = client.post(
        "/myaccount/games",
        json={
            "game_session": [
                {
                    "game_type": "spatial_reasoning",
                    "game_data": '{"accuracy": 92}',
                }
            ]
        },
        headers=patient_headers,
    )
    assert post_res.status_code == 201, f"Patient POST failed: {post_res.status_code} - {post_res.text}"

    # Doctor queries assigned patient
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": patient.id},
        headers=doctor_headers,
    )
    assert response.status_code == 200, f"Doctor GET failed: {response.status_code} - {response.text}"
    res_json = response.json()
    assert res_json["success"] is True

    items = res_json["data"]
    assert isinstance(items, list)
    assert any(item["game_type"] == "spatial_reasoning" for item in items)


def test_doctor_cannot_get_unassigned_patient_games(
    client: TestClient,
    test_db_session: Session,
    doctor_headers: dict,
    patient_headers: dict,
):
    patient = test_db_session.exec(
        select(UserProfile).where(UserProfile.email == "patient@example.com")
    ).first()

    post_res = client.post(
        "/myaccount/games",
        json={
            "game_session": [
                {"game_type": "private_data", "game_data": "{}"}
            ]
        },
        headers=patient_headers,
    )
    assert post_res.status_code == 201, f"Patient POST failed: {post_res.status_code} - {post_res.text}"

    # Attempt fetch without DoctorPatientLink record
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": patient.id},
        headers=doctor_headers,
    )
    assert response.status_code in (403, 404)


def test_doctor_queries_nonexistent_patient_id(
    client: TestClient, doctor_headers: dict
):
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": 999999},
        headers=doctor_headers,
    )
    assert response.status_code in (403, 404)


def test_patient_cannot_access_doctor_patient_games_endpoint(
    client: TestClient, patient_headers: dict
):
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": 1},
        headers=patient_headers,
    )
    assert response.status_code == 403


def test_doctor_patient_games_rejects_missing_param_or_auth(
    client: TestClient, doctor_headers: dict
):
    assert client.get("/myaccount/patients/games").status_code in (401, 403)

    # Missing patient_id query parameter triggers 404 or 422 depending on route definition
    response = client.get("/myaccount/patients/games", headers=doctor_headers)
    assert response.status_code in (404, 422)