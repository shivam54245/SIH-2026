from fastapi.testclient import TestClient


def test_fixed_varchar_column_length_overflow(client: TestClient):
    # Role column in schema is VARCHAR(7) (e.g., 'PATIENT'). Inject 20,000 characters.
    payload = {
        "email": "overflow_role@example.com",
        "password": "valid_password_123",
        "full_name": "Test Boundary",
        "role": "P" * 20000
    }
    response = client.post("/myaccount/register", json=payload)
    if response.status_code == 404:
        # Fallback to direct user creation if route is under /users
        response = client.post("/users", json=payload)
    assert response.status_code < 500, f"Server threw 500 on VARCHAR(7) overflow: {response.text}"


def test_reminder_time_nanosecond_precision_spam(client: TestClient, patient_headers: dict):
    # Feeds excessive fractional seconds into standard HH:MM time column
    payload = {
        "reminder": [
            {
                "message": "Microsecond spam",
                "time": "12:00:00.1234567890123456789",
                "is_completed": False
            }
        ]
    }
    response = client.post("/myaccount/reminders", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Time precision spam broke parser: {response.text}"


def test_empty_string_array_permutations(client: TestClient, patient_headers: dict):
    # Passes lists containing empty strings instead of model objects
    payload = {"game_session": ["", "   ", "\t\n"]}
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"String array in pooled endpoint crashed server: {response.text}"


def test_schema_cross_contamination_injection(client: TestClient, patient_headers: dict):
    # Sends ReminderRequest fields into GameSessionRequest endpoint
    payload = {
        "game_session": [
            {
                "message": "Invalid Reminder payload here",
                "time": "12:00",
                "is_completed": True
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Cross-schema payload caused 500: {response.text}"


def test_extreme_combining_diacritics_normalization(client: TestClient, patient_headers: dict):
    # Uses intense unicode combining characters (Zalgo) in mandatory string fields
    toxic_unicode = "C̷͔͑̐l̵̩̅i̴͕̓ǹ̷̰i̵̲͌c̶͚͋" * 150
    payload = {
        "game_session": [
            {
                "game_type": toxic_unicode,
                "game_data": "{}"
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Combining diacritics crashed server: {response.text}"


def test_boolean_truthy_fuzz_matrices(client: TestClient, patient_headers: dict):
    # Fuzzes boolean fields with invalid non-boolean types
    fuzz_values = ["yes", "no", 2, -1, "TRUE", "F", [], {}]
    for val in fuzz_values:
        payload = {
            "reminder": [
                {
                    "message": "Boolean check",
                    "time": "10:00",
                    "is_completed": val
                }
            ]
        }
        res = client.post("/myaccount/reminders", json=payload, headers=patient_headers)
        assert res.status_code < 500, f"Boolean fuzz '{val}' caused server crash: {res.text}"


def test_missing_root_key_with_valid_child_data(client: TestClient, patient_headers: dict):
    # Submits the raw list of dictionaries without the 'game_session' wrapper key
    payload = [
        {"game_type": "memory", "game_data": "{}"},
        {"game_type": "spatial", "game_data": "{}"}
    ]
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Missing wrapper key caused unhandled 500: {response.text}"


def test_null_value_injection_in_required_non_nullable_fields(client: TestClient, patient_headers: dict):
    # Explicitly passes nulls to non-nullable database columns
    payload = {
        "game_session": [
            {
                "game_type": None,
                "game_data": None
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Explicit nulls triggered internal 500: {response.text}"


def test_arbitrary_nested_objects_in_string_columns(client: TestClient, patient_headers: dict):
    # Injects deep object trees where standard primitive strings are expected
    payload = {
        "game_session": [
            {
                "game_type": {"deep": {"structure": [1, 2, 3]}},
                "game_data": {"nested_key": {"another_level": True}}
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Object-for-string mismatch caused 500: {response.text}"


def test_duplicate_primary_key_collision_in_pooled_request(client: TestClient, admin_headers: dict):
    # Tries to force multiple conflicting manual ID insertions inside a single batch
    payload = {
        "game_session": [
            {"id": 99999, "patient_id": 1, "game_type": "dup_1", "game_data": "{}"},
            {"id": 99999, "patient_id": 1, "game_type": "dup_2", "game_data": "{}"}
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Batch PK collision caused unhandled 500: {response.text}"