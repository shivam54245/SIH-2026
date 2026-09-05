from fastapi.testclient import TestClient


def test_extreme_url_path_length_exhaustion(client: TestClient, doctor_headers: dict):
    # Builds an 8KB padded path
    path_padding = "/".join(["subpath" for _ in range(300)])
    response = client.get(f"/myaccount/patients/{path_padding}/games", headers=doctor_headers)
    assert response.status_code < 500, f"Long path string crashed ASGI router: {response.text}"


def test_directory_traversal_character_sequence_in_route(client: TestClient, doctor_headers: dict):
    # Passes path traversal character strings into the URL
    traversal_path = "/myaccount/patients/..%2f..%2f..%2fetc/games"
    response = client.get(traversal_path, headers=doctor_headers)
    assert response.status_code < 500, f"Directory traversal pattern crashed route dispatcher: {response.text}"


def test_duplicate_query_parameter_pollution(client: TestClient, doctor_headers: dict):
    # Repeats the same query parameter key 50 times with contrasting values
    repeated_params = "&".join([f"patient_id={i}" for i in range(50)])
    response = client.get(f"/myaccount/patients/games?{repeated_params}", headers=doctor_headers)
    assert response.status_code < 500, f"Query parameter pollution threw 500: {response.text}"


def test_malformed_percent_encoding_in_query(client: TestClient, doctor_headers: dict):
    # Sends illegal %-tokens that break standard urllib unquote operations
    response = client.get("/myaccount/patients/games?patient_id=%ZZ%FF%GG", headers=doctor_headers)
    assert response.status_code < 500, f"Malformed percent-encoding caused server crash: {response.text}"


def test_rfc3986_reserved_character_matrix(client: TestClient, doctor_headers: dict):
    # Floods query parameter with all standard URI reserved characters
    reserved_chars = "!*'();:@&=+$,/?#[]"
    response = client.get(f"/myaccount/patients/games?patient_id={reserved_chars}", headers=doctor_headers)
    assert response.status_code < 500, f"Reserved URI characters triggered 500: {response.text}"


def test_unsupported_http_methods_on_all_game_routes(client: TestClient, patient_headers: dict):
    # Tests method dispatch errors across all game paths
    methods = ["DELETE", "PATCH", "HEAD", "OPTIONS"]
    for m in methods:
        res = client.request(m, "/myaccount/games", headers=patient_headers)
        assert res.status_code < 500, f"HTTP method {m} caused internal server error: {res.text}"


def test_query_parameter_key_length_overflow(client: TestClient, doctor_headers: dict):
    # Sends an oversized key name (10,000 characters)
    huge_key = "K" * 10000
    response = client.get(f"/myaccount/patients/games?{huge_key}=1", headers=doctor_headers)
    assert response.status_code < 500, f"Oversized query key threw 500: {response.text}"


def test_incompatible_primitive_casting_in_query(client: TestClient, doctor_headers: dict):
    # Sends an array-like representation string into single scalar integer parameter
    response = client.get("/myaccount/patients/games?patient_id=[1,2,3]", headers=doctor_headers)
    assert response.status_code < 500, f"Array string in scalar param threw 500: {response.text}"


def test_full_width_and_homoglyph_unicode_in_query(client: TestClient, doctor_headers: dict):
    # Passes full-width numbers and homoglyphs (e.g. １２３ instead of 123)
    full_width_id = "１２３４５"
    response = client.get(f"/myaccount/patients/games?patient_id={full_width_id}", headers=doctor_headers)
    assert response.status_code < 500, f"Full-width unicode number caused 500: {response.text}"


def test_rapid_pipelined_requests_on_single_client(client: TestClient, patient_headers: dict):
    # Fires 20 consecutive requests using the same connection context
    for i in range(20):
        res = client.get(f"/myaccount/games?cycle={i}", headers=patient_headers)
        assert res.status_code < 500, f"Pipelined cycle #{i} failed with 500"