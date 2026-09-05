from fastapi.testclient import TestClient


def test_get_myaccount_games_empty_initially(
    client: TestClient, patient_headers: dict
):
    response = client.get("/myaccount/games", headers=patient_headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"] == []


def test_patient_can_post_game_data(
    client: TestClient, patient_headers: dict
):
    payload = {
        "game_session": [
            {
                "game_type": "memory_cards",
                "game_data": '{"score": 95, "duration_seconds": 120}',
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code == 201, f"POST failed: {response.status_code} - {response.text}"

    res_json = response.json()
    assert res_json["success"] is True

    # Verify persistence via GET /myaccount/games
    get_res = client.get("/myaccount/games", headers=patient_headers)
    assert get_res.status_code == 200
    res_data = get_res.json()
    assert res_data["success"] is True
    items = res_data["data"]
    assert any(item.get("game_type") == "memory_cards" for item in items)


def test_get_myaccount_games_returns_created_records(
    client: TestClient, patient_headers: dict
):
    payload = {
        "game_session": [
            {"game_type": "quiz_0", "game_data": '{"step": 0}'},
            {"game_type": "quiz_1", "game_data": '{"step": 1}'},
        ]
    }
    res = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert res.status_code == 201, f"Batch POST failed: {res.status_code} - {res.text}"

    response = client.get("/myaccount/games", headers=patient_headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    items = res_json["data"]
    types = [item.get("game_type") for item in items]
    assert "quiz_0" in types
    assert "quiz_1" in types


def test_post_myaccount_games_rejects_malformed_payload(
    client: TestClient, patient_headers: dict
):
    # Missing required 'game_session' array
    invalid_payload = {"game_data": '{"score": 10}'}
    response = client.post(
        "/myaccount/games", json=invalid_payload, headers=patient_headers
    )
    assert response.status_code == 422


def test_doctor_cannot_post_to_patient_myaccount_games(
    client: TestClient, doctor_headers: dict
):
    payload = {
        "game_session": [
            {"game_type": "reaction_test", "game_data": "{}"}
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=doctor_headers)
    assert response.status_code in (400, 403)


def test_myaccount_games_rejects_unauthenticated_request(client: TestClient):
    assert client.get("/myaccount/games").status_code in (401, 403)
    assert client.post("/myaccount/games", json={}).status_code in (401, 403)