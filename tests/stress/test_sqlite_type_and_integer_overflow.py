from fastapi.testclient import TestClient


def test_signed_64bit_integer_max_limit(client: TestClient, admin_headers: dict):
    # Tests the exact positive boundary of a signed 64-bit integer (2^63 - 1)
    max_int64 = 9223372036854775807
    payload = {
        "game_session": [
            {
                "patient_id": max_int64,
                "game_type": "int64_max",
                "game_data": "{}"
            }
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Server threw 500 on signed int64 max: {response.text}"


def test_signed_64bit_integer_overflow(client: TestClient, admin_headers: dict):
    # Exceeds signed 64-bit integer capacity by 1 (2^63) to force C-level overflow
    overflow_int64 = 9223372036854775808
    payload = {
        "game_session": [
            {
                "patient_id": overflow_int64,
                "game_type": "int64_overflow",
                "game_data": "{}"
            }
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Server threw 500 on int64 overflow: {response.text}"


def test_unsigned_64bit_integer_boundary_failure(client: TestClient, admin_headers: dict):
    # Hits maximum unsigned 64-bit limit (2^64 - 1)
    uint64_max = 18446744073709551615
    payload = {
        "game_session": [
            {
                "patient_id": uint64_max,
                "game_type": "uint64_max",
                "game_data": "{}"
            }
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Server crashed on uint64 max: {response.text}"


def test_arbitrary_precision_thousand_digit_integer(client: TestClient, doctor_headers: dict):
    # Sends a 1000-digit numeric string to patient_id query param to exhaust big-int decoders
    massive_int_str = "9" * 1000
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": massive_int_str},
        headers=doctor_headers
    )
    assert response.status_code < 500, f"BigInt string caused 500: {response.text}"


def test_ieee754_extreme_float_underflow_in_id(client: TestClient, doctor_headers: dict):
    # Passes smallest positive non-zero subnormal float representation (5e-324)
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": "5e-324"},
        headers=doctor_headers
    )
    assert response.status_code < 500, f"Float underflow caused server crash: {response.text}"


def test_subnormal_scientific_notation_bypass(client: TestClient, admin_headers: dict):
    # Submits exponential notation as a number where an integer is expected
    payload = {
        "game_session": [
            {
                "patient_id": 1e50,
                "game_type": "sci_notation",
                "game_data": "{}"
            }
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Scientific notation payload threw 500: {response.text}"


def test_sqlite_negative_zero_handling(client: TestClient, doctor_headers: dict):
    # Queries using negative zero string representation (-0)
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": "-0"},
        headers=doctor_headers
    )
    assert response.status_code < 500, f"Negative zero caused crash: {response.text}"


def test_mixed_type_numeric_array_in_pooled_batch(client: TestClient, admin_headers: dict):
    # Injects string integers, hex representations, and floats inside a single batch
    payload = {
        "game_session": [
            {"patient_id": "1", "game_type": "str_int", "game_data": "{}"},
            {"patient_id": 0x1A, "game_type": "hex_int", "game_data": "{}"},
            {"patient_id": 2.0, "game_type": "float_int", "game_data": "{}"}
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Mixed numeric batch triggered 500: {response.text}"


def test_extreme_negative_signed_integer_underflow(client: TestClient, admin_headers: dict):
    # Checks lowest bounds of signed 64-bit integer (-2^63) and below (-2^63 - 1)
    min_int64 = -9223372036854775808
    payload = {
        "game_session": [
            {
                "patient_id": min_int64 - 1,
                "game_type": "int64_underflow",
                "game_data": "{}"
            }
        ]
    }
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Negative int64 underflow threw 500: {response.text}"


def test_extreme_year_datetime_boundary_simulation(client: TestClient, patient_headers: dict):
    # Attempts time formats representing year 9999 and year 0000 boundary conditions
    payload = {
        "reminder": [
            {
                "message": "Far Future Alarm",
                "time": "9999-12-31 23:59:59",
                "is_completed": False
            },
            {
                "message": "Past Origin Alarm",
                "time": "0000-01-01 00:00:00",
                "is_completed": False
            }
        ]
    }
    response = client.post("/myaccount/reminders", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Extreme datetime string caused 500: {response.text}"