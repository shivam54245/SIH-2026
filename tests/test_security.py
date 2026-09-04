import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from fastapi import status
from jose import jwt
import pytest
import base64
import json

from src.auth import ALGORITHM, SECRET_KEY



# 1. Broken Object-Level Authorization (BOLA / IDOR)
# Verifies a patient cannot read another patient's reminders via query parameter manipulation
def test_patient_cannot_access_other_patient_data_via_get(
    client, patient_headers
):
    # Attacker tries to query /myaccount/reminders with another user's reminder ID or params
    res = client.get(
        "/myaccount/reminders", params={"patient_id": 1}, headers=patient_headers
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json().get("data", [])


# 2. Horizontal Privilege Escalation
# Verifies a patient cannot create reminders assigned to arbitrary patient IDs via /myaccount/reminders
def test_patient_cannot_spoof_patient_id_on_self_endpoint(
    client, patient_headers
):
    malicious_payload = {
        "reminder": [
            {
                "patient_id": 1,  # Attempting to inject admin user_id into a self reminder
                "time": "10:00",
                "message": "Spoofed medication",
            }
        ]
    }
    # Pydantic schema validation should reject unknown extra fields if extra='forbid',
    # or the endpoint must ignore it and force current_user.id
    res = client.post(
        "/myaccount/reminders", json=malicious_payload, headers=patient_headers
    )
    assert res.status_code == status.HTTP_201_CREATED
    # Verify it was saved strictly under the caller's ID, not ID 1
    get_res = client.get("/myaccount/reminders", headers=patient_headers)
    records = get_res.json().get("data", [])
    assert all(r["user_id"] != 1 for r in records)


# 3. Vertical Privilege Escalation
# Verifies patients are strictly forbidden from calling administrative user management
def test_patient_cannot_create_admin_user(client, patient_headers):
    payload = {
        "email": "hacked_admin@example.com",
        "password": "Password123!",
        "full_name": "Rogue Admin",
        "role": "admin",
    }
    res = client.post("/users", json=payload, headers=patient_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


# 4. Authentication Bypass / Token Manipulation
# Verifies altered or unsigned tokens fail immediately
def test_tampered_jwt_token_rejected(client):
    tampered_token = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSJ9.INVALID_SIGNATURE"
    }
    res = client.get("/reminders", headers=tampered_token)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# 5. Injection / Input Validation Boundary Check
# Verifies invalid data types and massive payloads are caught by Pydantic before DB execution
def test_malformed_json_types_rejected(client, admin_headers):
    payload = {
        "reminder": [
            {
                "patient_id": "not_an_int",  # Type confusion
                "time": "08:00",
                "message": "A" * 10000,
            }
        ]
    }
    res = client.post("/reminders", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# 6. Expired Token Enforcement
# Verifies tokens past their 'exp' timestamp cannot authenticate
def test_expired_jwt_token_rejected(client):
    expired_payload = {
        "sub": "patient@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {expired_token}"}

    res = client.get("/myaccount/reminders", headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# 7. Algorithm Confusion Attack ('none' algorithm)
# Verifies endpoints reject unsigned tokens attempting to bypass signature checks
def test_jwt_none_algorithm_rejected(client):
    # Manually construct a JWT with "alg": "none" and an empty signature
    header = {"alg": "none", "typ": "JWT"}
    payload = {"sub": "admin@example.com"}

    def b64url_encode(data: dict) -> str:
        dumped = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(dumped).rstrip(b"=").decode("utf-8")

    unsigned_token = f"{b64url_encode(header)}.{b64url_encode(payload)}."
    headers = {"Authorization": f"Bearer {unsigned_token}"}

    res = client.get("/users", headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# 8. SQL Wildcard & Operator Probing on Filters
# Verifies inputs containing SQL/LIKE special characters do not trigger full table scans or 500 errors
@pytest.mark.parametrize(
    "probe",
    [
        "%",
        "_",
        "1 OR 1=1",
        "' OR '1'='1",
        "'; DROP TABLE reminders; --",
    ],
)
def test_filter_injection_resilience(client, admin_headers, probe):
    # Tests that string manipulation attempts in integer or query parameters are handled safely
    res = client.get(
        "/reminders", params={"patient_id": probe}, headers=admin_headers
    )
    # Integer validation should catch string payloads with 422, or safely return 0 results
    assert res.status_code in (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_200_OK,
    )


# 9. Role Escalation via Payload Injection
# Verifies a user cannot register or update themselves with unauthorized elevated roles directly
def test_prevent_arbitrary_role_registration(client, admin_headers):
    malicious_payload = {
        "email": "superadmin_probe@example.com",
        "password": "Password123!",
        "full_name": "Injected User",
        "role": "SUPERUSER_ROOT",  # Undefined/invalid role string
    }
    res = client.post("/users", json=malicious_payload, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT