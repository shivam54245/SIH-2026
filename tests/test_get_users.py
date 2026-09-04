from fastapi import status


def test_get_users_unauthorized(client):
    res = client.get("/users")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_users_forbidden_for_patient(client, patient_headers):
    res = client.get("/users", headers=patient_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_get_users_admin_returns_all(client, admin_headers):
    res = client.get("/users", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    users = body.get("data", body) if isinstance(body, dict) else body
    assert isinstance(users, list)
    assert len(users) >= 3


def test_get_users_filter_by_role(client, admin_headers):
    res = client.get(
        "/users", params={"role": "PATIENT"}, headers=admin_headers
    )
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    users = body.get("data", body) if isinstance(body, dict) else body
    assert len(users) >= 1
    assert all(u["role"] == "PATIENT" for u in users)


def test_get_users_filter_by_user_id(client, admin_headers):
    base = client.get("/users", headers=admin_headers)
    all_users = (
        base.json().get("data", base.json())
        if isinstance(base.json(), dict)
        else base.json()
    )
    target_id = all_users[0].get("id") or all_users[0].get("user_id")

    res = client.get(
        "/users", params={"user_id": target_id}, headers=admin_headers
    )
    assert res.status_code == status.HTTP_200_OK
    users = (
        res.json().get("data", res.json())
        if isinstance(res.json(), dict)
        else res.json()
    )
    assert len(users) == 1
    returned_id = users[0].get("id") or users[0].get("user_id")
    assert returned_id == target_id