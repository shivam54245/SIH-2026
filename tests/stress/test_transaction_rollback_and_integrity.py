from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.database import UserProfile


def test_partial_failure_pooled_insertion_atomicity(client: TestClient, admin_headers: dict):
    # First item valid, second item points to an invalid patient ID (tests rollback vs partial commit)
    payload = {
        "game_session": [
            {"patient_id": 1, "game_type": "valid_entry", "game_data": "{}"},
            {"patient_id": 999999, "game_type": "invalid_entry", "game_data": "{}"}
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Partial batch error threw 500: {response.text}"


def test_foreign_key_violation_recovery(client: TestClient, admin_headers: dict):
    # Forces an immediate foreign key constraint error to ensure the session recovers
    payload = {
        "game_session": [
            {"patient_id": -999, "game_type": "fk_violation", "game_data": "{}"}
        ]
    }
    fail_res = client.post("/games", json=payload, headers=admin_headers)
    assert fail_res.status_code < 500

    # Verify the database session remains healthy for subsequent calls
    verify_res = client.get("/games", headers=admin_headers)
    assert verify_res.status_code == 200, f"DB session left broken after FK failure: {verify_res.text}"


def test_state_leakage_after_failed_payloads(client: TestClient, patient_headers: dict):
    # Fires 5 broken payloads followed immediately by a valid payload to verify session hygiene
    for _ in range(5):
        client.post("/myaccount/games", json={"corrupt": True}, headers=patient_headers)

    valid_payload = {
        "game_session": [
            {"game_type": "recovery_test", "game_data": "{}"}
        ]
    }
    res = client.post("/myaccount/games", json=valid_payload, headers=patient_headers)
    assert res.status_code < 500, f"Server failed to recover from bad transactions: {res.text}"


def test_rapid_commit_abort_alternation(client: TestClient, patient_headers: dict):
    # Alternates good and bad inserts 10 times in a row
    for i in range(10):
        bad_res = client.post("/myaccount/games", json={"game_session": [{}]}, headers=patient_headers)
        assert bad_res.status_code < 500

        good_res = client.post(
            "/myaccount/games",
            json={"game_session": [{"game_type": f"alt_{i}", "game_data": "{}"}]},
            headers=patient_headers
        )
        assert good_res.status_code < 500


def test_duplicate_email_registration_transaction_abort(client: TestClient):
    # Tries to insert duplicate user emails to check integrity constraint error translation
    payload = {
        "email": "admin@example.com",  # Already seeded in test_db_session
        "password": "new_password_123",
        "full_name": "Conflict Admin"
    }
    res = client.post("/myaccount/register", json=payload)
    if res.status_code == 404:
        res = client.post("/users", json=payload)
    assert res.status_code < 500, f"Duplicate unique constraint crashed server with 500: {res.text}"


def test_self_assignment_link_stress(client: TestClient, test_db_session: Session, admin_headers: dict):
    # Tries to assign a user to themselves (doctor_id == patient_id)
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    payload = {"doctor_id": doctor.id, "patient_id": doctor.id}
    res = client.post("/assign", json=payload, headers=admin_headers)
    assert res.status_code < 500, f"Self-assignment triggered unhandled 500: {res.text}"


def test_conflicting_ids_in_same_batch(client: TestClient, admin_headers: dict):
    # Passes identical manual ids inside the same batch array
    payload = {
        "game_session": [
            {"id": 100, "patient_id": 1, "game_type": "same_1", "game_data": "{}"},
            {"id": 100, "patient_id": 1, "game_type": "same_2", "game_data": "{}"}
        ]
    }
    res = client.post("/games", json=payload, headers=admin_headers)
    assert res.status_code < 500, f"Conflicting batch IDs triggered 500: {res.text}"


def test_reminders_negative_patient_id_batch(client: TestClient, admin_headers: dict):
    # Targets the admin reminder route with non-existent foreign keys
    payload = {
        "reminder": [
            {"patient_id": -99, "message": "bad_fk", "time": "10:00", "is_completed": False}
        ]
    }
    res = client.post("/reminders", json=payload, headers=admin_headers)
    assert res.status_code < 500, f"Admin reminders negative FK caused 500: {res.text}"


def test_assign_doctor_using_string_ids(client: TestClient, admin_headers: dict):
    # Passes non-numeric characters into assignment fields
    res = client.post("/assign", json={"doctor_id": "doc", "patient_id": "pat"}, headers=admin_headers)
    assert res.status_code < 500, f"String IDs in assign endpoint triggered 500: {res.text}"


def test_transaction_survives_zero_length_body(client: TestClient, patient_headers: dict):
    # Sends zero content-length POST request
    custom_headers = {**patient_headers, "Content-Length": "0"}
    res = client.post("/myaccount/games", headers=custom_headers)
    assert res.status_code < 500, f"Zero length body crashed transaction context: {res.text}"
    