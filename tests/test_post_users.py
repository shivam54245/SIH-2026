from fastapi import status


def test_post_users_unauthorized(client):
    res = client.post(
        "/users",
        json={
            "email": "new@example.com",
            "password": "pass",
            "full_name": "New",
            "role": "PATIENT",
        },
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_post_users_forbidden_for_patient(client, patient_headers):
    res = client.post(
        "/users",
        json={
            "email": "new@example.com",
            "password": "pass",
            "full_name": "New",
            "role": "PATIENT",
        },
        headers=patient_headers,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_post_users_admin_success_and_verifiable_via_get(client, admin_headers):
    payload = {
        "email": "unique_patient@example.com",
        "password": "Password123!",
        "full_name": "Unique Patient",
        "role": "PATIENT",
    }
    create_res = client.post("/users", json=payload, headers=admin_headers)
    assert create_res.status_code == status.HTTP_201_CREATED

    get_res = client.get(
        "/users", params={"role": "PATIENT"}, headers=admin_headers
    )
    users = get_res.json().get("data", get_res.json())
    assert any(u["email"] == payload["email"] for u in users)


def test_post_users_duplicate_email_conflict(client, admin_headers):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Duplicate User",
        "role": "PATIENT",
    }
    res1 = client.post("/users", json=payload, headers=admin_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/users", json=payload, headers=admin_headers)
    assert res2.status_code == status.HTTP_409_CONFLICT