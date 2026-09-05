import gzip
import json
from fastapi.testclient import TestClient


def test_circular_reference_string_simulation(client: TestClient, patient_headers: dict):
    # Tests deeply self-referential graph patterns serialized into text
    graph_node = {"name": "node_0"}
    curr = graph_node
    for i in range(1, 150):
        curr["child"] = {"name": f"node_{i}", "parent": curr["name"]}
        curr = curr["child"]
    curr["child"] = graph_node["name"]  # loop reference

    payload = {
        "game_session": [
            {
                "game_type": "graph_loop",
                "game_data": json.dumps(graph_node)
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Server choked on circular graph structure: {response.text}"


def test_escaped_character_and_invalid_backslash_sequences(client: TestClient, patient_headers: dict):
    # Injects invalid Unicode escapes and unescaped control chars into raw body
    bad_escape_body = b'{"game_session": [{"game_type": "escape_test", "game_data": "Invalid: \\uD800\\uZZZZ \\x00 \\a \\v \\c"}]}'
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    response = client.post("/myaccount/games", content=bad_escape_body, headers=custom_headers)
    assert response.status_code < 500, f"Server threw 500 on invalid escape sequences: {response.text}"


def test_non_printable_binary_stream_in_string_field(client: TestClient, patient_headers: dict):
    # Encodes non-printable low-ASCII control characters (0x01 to 0x1F except standard whitespace)
    non_printable = "".join(chr(i) for i in range(1, 32) if i not in (9, 10, 13))
    payload = {
        "game_session": [
            {
                "game_type": "low_ascii",
                "game_data": f"toxic_{non_printable}_payload"
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Non-printable binary stream caused 500: {response.text}"


def test_header_count_flooding(client: TestClient, patient_headers: dict):
    # Floods request with 300 arbitrary custom headers to test ASGI header map parsers
    junk_headers = {f"X-Stress-Header-{i}": f"stress_value_{i}" for i in range(300)}
    full_headers = {**patient_headers, **junk_headers}
    response = client.get("/myaccount/games", headers=full_headers)
    assert response.status_code < 500, f"Server crashed on header flood: {response.text}"


def test_oversized_url_encoded_query_strings(client: TestClient, doctor_headers: dict):
    # Sends a query param consisting of heavy percentage-encoded sequences
    toxic_param = "%20%27%22" * 1500
    response = client.get(
        "/myaccount/patients/games",
        params={"patient_id": toxic_param},
        headers=doctor_headers
    )
    assert response.status_code < 500, f"Percentage-encoded flood triggered 500: {response.text}"


def test_large_dataset_response_generation_stress(client: TestClient, patient_headers: dict):
    # Seeds 100 small items to test whether FastAPI serializer chokes generating response JSON
    seed_payload = {
        "game_session": [
            {"game_type": f"seed_{i}", "game_data": f'{{"idx": {i}}}'}
            for i in range(100)
        ]
    }
    post_res = client.post("/myaccount/games", json=seed_payload, headers=patient_headers)
    assert post_res.status_code < 500

    get_res = client.get("/myaccount/games", headers=patient_headers)
    assert get_res.status_code < 500, f"Failed generating response envelope: {get_res.text}"


def test_truncated_json_body_abrupt_eof(client: TestClient, patient_headers: dict):
    # Simulates network cutoff mid-payload
    truncated_raw = b'{"game_session": [{"game_type": "partial_transfer", "game_data": '
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    response = client.post("/myaccount/games", content=truncated_raw, headers=custom_headers)
    assert response.status_code < 500, f"Abrupt EOF triggered 500: {response.text}"


def test_ten_thousand_single_character_json_keys(client: TestClient, patient_headers: dict):
    # Forces JSON decoder to parse 5,000 distinct dictionary entries
    dense_dict = {f"k{i}": i for i in range(5000)}
    payload = {
        "game_session": [
            {
                "game_type": "dense_keys",
                "game_data": json.dumps(dense_dict)
            }
        ]
    }
    response = client.post("/myaccount/games", json=payload, headers=patient_headers)
    assert response.status_code < 500, f"Dense key object caused crash: {response.text}"


def test_content_type_mismatch_xml_content(client: TestClient, patient_headers: dict):
    # Mismatches header and content (XML payload sent under application/json)
    xml_data = b"<game_session><item><game_type>xml</game_type></item></game_session>"
    custom_headers = {**patient_headers, "Content-Type": "application/json"}
    response = client.post("/myaccount/games", content=xml_data, headers=custom_headers)
    assert response.status_code < 500, f"XML payload parsing caused 500: {response.text}"


def test_gzip_compression_bomb_handling(client: TestClient, patient_headers: dict):
    # Constructs a compressed body using gzip to test decompression safety
    uncompressed = json.dumps({"game_session": [{"game_type": "gzip", "game_data": "0" * 100000}]}).encode("utf-8")
    compressed = gzip.compress(uncompressed)
    custom_headers = {
        **patient_headers,
        "Content-Type": "application/json",
        "Content-Encoding": "gzip"
    }
    response = client.post("/myaccount/games", content=compressed, headers=custom_headers)
    assert response.status_code < 500, f"Decompression handling crashed server: {response.text}"