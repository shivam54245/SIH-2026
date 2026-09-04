from fastapi import status


def test_post_reminders_unauthorized(client):
    res = client.post(
        "/reminders",
        json={
            "reminder": [
                {"patient_id": 3, "time": "08:00", "message": "Admin reminder"}
            ]
        },
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_post_reminders_forbidden_for_patient(client, patient_headers):
    res = client.post(
        "/reminders",
        json={
            "reminder": [
                {"patient_id": 1, "time": "08:00", "message": "Admin reminder"}
            ]
        },
        headers=patient_headers,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_post_reminders_admin_success(client, admin_headers):
    # 1. Create patient 4 so the ID is valid
    user_res = client.post(
        "/users",
        json={
            "email": "patient4@example.com",
            "password": "Password123!",
            "full_name": "Patient Four",
            "role": "patient",
        },
        headers=admin_headers,
    )
    assert user_res.status_code == status.HTTP_201_CREATED
    patient4_id = user_res.json()["data"]["user_id"]

    # 2. Submit reminders with the valid patient IDs
    payload = {
        "reminder": [
            {"patient_id": 3, "time": "09:00", "message": "Morning medication"},
            {
                "patient_id": patient4_id,
                "time": "18:00",
                "message": "Evening checkup",
            },
        ]
    }
    res = client.post("/reminders", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_201_CREATED


def test_post_reminders_invalid_patient_id(client, admin_headers):
    payload = {
        "reminder": [
            {"patient_id": 99999, "time": "09:00", "message": "Ghost patient"}
        ]
    }
    res = client.post("/reminders", json=payload, headers=admin_headers)
    assert res.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_404_NOT_FOUND,
    )