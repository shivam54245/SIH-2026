from fastapi import status


def test_get_self_missing_token(client):
    res = client.get("/self")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_self_invalid_token(client):
    res = client.get("/self", headers={"Authorization": "Bearer bad_token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_self_admin(client, admin_headers):
    res = client.get("/self", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json().get("data", res.json())
    assert data["email"] == "admin@example.com"
    assert data["role"] == "ADMIN"


def test_get_self_patient(client, patient_headers):
    res = client.get("/self", headers=patient_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json().get("data", res.json())
    assert data["email"] == "patient@example.com"
    assert data["role"] == "PATIENT"