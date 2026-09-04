from fastapi import status


def test_login_success(client):
    res = client.post(
        "/myaccount", json={"email": "admin@example.com", "password": "admin_pass"}
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


def test_login_invalid_password(client):
    res = client.post(
        "/myaccount",
        json={"email": "admin@example.com", "password": "wrong_password"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_unregistered_email(client):
    res = client.post(
        "/myaccount",
        json={"email": "nobody@example.com", "password": "any_password"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_missing_fields(client):
    res = client.post("/myaccount", json={"email": "admin@example.com"})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT