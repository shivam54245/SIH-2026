from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.database import GamedataProfile, UserProfile


def test_admin_can_post_game_for_patient(
    client: TestClient, test_db_session: Session, admin_headers: dict
):
    patient = test_db_session.exec(
        select(UserProfile).where(UserProfile.email == "patient@example.com")
    ).first()

    payload = {
        "game_session": [
            {
                "patient_id": patient.id,
                "game_type": "cognitive_flexibility",
                "game_data": '{"completed_levels": 5}',
            }
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code == 201

    res_json = response.json()
    assert res_json["success"] is True

    # Verify via GET /games
    get_res = client.get("/games", headers=admin_headers)
    assert get_res.status_code == 200
    all_games = get_res.json()["data"]
    assert any(
        g.get("game_type") == "cognitive_flexibility"
        and (g.get("user_id") == patient.id or g.get("patient_id") == patient.id)
        for g in all_games
    )


def test_admin_post_game_rejects_nonexistent_patient(
    client: TestClient, admin_headers: dict
):
    payload = {
        "patient_id": 999999,
        "game_type": "invalid_user_test",
        "game_data": "{}",
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code in (400, 404, 422)


def test_admin_can_read_all_system_games(
    client: TestClient, admin_headers: dict, patient_headers: dict
):
    payload = {
        "game_session": [
            {
                "game_type": "patient_action",
                "game_data": "{}",
            }
        ]
    }
    post_res = client.post(
        "/myaccount/games",
        json=payload,
        headers=patient_headers,
    )
    assert post_res.status_code == 201, f"Failed to seed game: {post_res.json()}"

    response = client.get("/games", headers=admin_headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    all_games = res_json["data"]
    assert isinstance(all_games, list)
    assert any(item.get("game_type") == "patient_action" for item in all_games)


def test_doctor_forbidden_from_admin_games_endpoints(
    client: TestClient, doctor_headers: dict
):
    assert client.get("/games", headers=doctor_headers).status_code == 403
    assert (
        client.post(
            "/games",
            json={"patient_id": 1, "game_type": "test", "game_data": "{}"},
            headers=doctor_headers,
        ).status_code
        == 403
    )


def test_patient_forbidden_from_admin_games_endpoints(
    client: TestClient, patient_headers: dict
):
    assert client.get("/games", headers=patient_headers).status_code == 403
    assert (
        client.post(
            "/games",
            json={"patient_id": 1, "game_type": "test", "game_data": "{}"},
            headers=patient_headers,
        ).status_code
        == 403
    )


def test_admin_games_rejects_unauthenticated_request(client: TestClient):
    assert client.get("/games").status_code in (401, 403)
    assert client.post("/games", json={}).status_code in (401, 403)