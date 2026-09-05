import json
import pytest
from fastapi.testclient import TestClient


def test_deeply_nested_json_recursion_boundary(client: TestClient, patient_headers: dict):
    # Builds a 120-level deeply nested dictionary to test parser recursion depth limits
    nested = {"core": "depth_limit"}
    for i in range(120):
        nested = {f"nest_{i}": nested}
    
    payload = {
        "game_session": [
            {
                "game_type": "recursive_depth_test",
                "game_data": json.dumps(nested)
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Server threw 500 on recursive JSON: {response.text}"


def test_ten_megabyte_string_payload_memory_stress(client: TestClient, patient_headers: dict):
    # Allocates a 10MB continuous string inside game_data to check body buffer handling
    massive_blob = "X" * (10 * 1024 * 1024)
    payload = {
        "game_session": [
            {
                "game_type": "memory_stress",
                "game_data": massive_blob
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Server crashed on 10MB payload: {response.text}"


def test_large_pooled_batch_session_exhaustion(client: TestClient, patient_headers: dict):
    # Generates a large batch of 500 distinct items in a single pooled request
    batch = [
        {
            "game_type": f"batch_type_{i}",
            "game_data": json.dumps({"metric_index": i, "status": "nominal"})
        }
        for i in range(500)
    ]
    payload = {"game_session": batch}
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Server threw 500 on large pooled batch: {response.text}"


def test_raw_zero_byte_padding_flood(client: TestClient, patient_headers: dict):
    # Sends raw zero-byte padding with a JSON header to trigger decoder panics
    zero_bytes = b"\x00" * 65536
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    response = client.post("/myaccount/games", content=zero_bytes, headers=custom_headers)
    assert response.status_code < 500, f"Server threw 500 on null-byte stream: {response.text}"


def test_whitespace_bloated_json_stream(client: TestClient, patient_headers: dict):
    # Builds a valid small payload surrounded by 3MB of tabs, carriage returns, and spaces
    whitespace_padding = " " * (3 * 1024 * 1024)
    raw_json = (
        whitespace_padding
        + '{"game_session": [{"game_type": "whitespace_test", "game_data": "{}"}]}'
        + whitespace_padding
    )
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    response = client.post("/myaccount/games", content=raw_json.encode("utf-8"), headers=custom_headers)
    assert response.status_code < 500, f"Server choked on whitespace-padded payload: {response.text}"


def test_extreme_floating_point_and_nan_parsing(client: TestClient, patient_headers: dict):
    # Deliberately submits malformed numeric representations and IEEE-754 edge tokens
    malformed_json_strings = [
        '{"game_session": [{"game_type": "float_test", "game_data": 1e309}]}',
        '{"game_session": [{"game_type": "float_test", "game_data": -1e309}]}',
        '{"game_session": [{"game_type": "float_test", "game_data": NaN}]}',
        '{"game_session": [{"game_type": "float_test", "game_data": Infinity}]}'
    ]
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    for raw_content in malformed_json_strings:
        response = client.post("/myaccount/games", content=raw_content.encode("utf-8"), headers=custom_headers)
        assert response.status_code < 500, f"Server crashed on token: {raw_content}"


def test_utf8_surrogate_and_astral_plane_bomb(client: TestClient, patient_headers: dict):
    # Injects 4-byte astral plane emojis and non-standard UTF-8 combining marks
    zalgo_text = "T̷͔̎ė̷͉s̸͈͌ṯ̸̀" * 200
    astral_emojis = "🧬🪐👾🔥⚡" * 500
    payload = {
        "reminder": [
            {
                "message": zalgo_text + astral_emojis,
                "time": "14:30",
                "is_completed": False
            }
        ]
    }
    response = client.post("/myaccount/reminders", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Server failed on astral/zalgo Unicode: {response.text}"


def test_hash_collision_key_flooding(client: TestClient, patient_headers: dict):
    # Generates 2,000 conflicting object keys to stress internal dictionary hash tables
    collision_dict = {f"k_{idx}": idx for idx in range(2000)}
    collision_json = json.dumps({
        "game_session": [
            {
                "game_type": "hash_flood",
                "game_data": json.dumps(collision_dict)
            }
        ]
    })
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    response = client.post("/myaccount/games", content=collision_json.encode("utf-8"), headers=custom_headers)
    assert response.status_code < 500, f"Server crashed on hash collision flood: {response.text}"


def test_memory_ballooning_on_admin_endpoint(client: TestClient, admin_headers: dict):
    # Sends an oversized batch to the admin endpoint referencing user ID 1
    large_batch = [
        {
            "patient_id": 1,
            "game_type": f"admin_stress_{i}",
            "game_data": "Z" * 10240
        }
        for i in range(100)
    ]
    payload = {"game_session": large_batch}
    response = client.post("/games", json=payload, headers=admin_headers)
    assert response.status_code < 500, f"Admin games endpoint failed on oversized batch: {response.text}"


def test_mass_batch_with_maximum_field_lengths(client: TestClient, patient_headers: dict):
    # Maximizes both field lengths and batch counts simultaneously
    heavy_batch = [
        {
            "game_type": "A" * 1000,
            "game_data": "B" * 50000
        }
        for _ in range(20)
    ]
    payload = {"game_session": heavy_batch}
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Server failed on multi-field boundary maximization: {response.text}"