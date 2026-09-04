from fastapi import status


def test_get_reminders_unauthorized(client):
    res = client.get("/reminders")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_reminders_forbidden_for_patient(client, patient_headers):
    res = client.get("/reminders", headers=patient_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_get_reminders_admin_filter_by_patient_id(client, admin_headers):
    # 1. Create a second patient so another valid patient exists
    user_res = client.post(
        "/users",
        json={
            "email": "patient2@example.com",
            "password": "Password123!",
            "full_name": "Second Patient",
            "role": "patient",
        },
        headers=admin_headers,
    )
    assert user_res.status_code == status.HTTP_201_CREATED
    patient2_id = user_res.json()["data"]["user_id"]

    # 2. Seed one reminder for patient 3 and one for the second patient
    seed_payload = {
        "reminder": [
            {"patient_id": 3, "time": "08:00", "message": "Morning Dose"},
            {
                "patient_id": patient2_id,
                "time": "12:00",
                "message": "Afternoon Dose",
            },
        ]
    }
    post_res = client.post(
        "/reminders", json=seed_payload, headers=admin_headers
    )
    assert post_res.status_code == status.HTTP_201_CREATED

    # 3. Filtering by patient 3 now matches exactly 1 reminder
    res = client.get(
        "/reminders", params={"patient_id": 3}, headers=admin_headers
    )
    assert res.status_code == status.HTTP_200_OK
    reminders = res.json().get("data", res.json())
    assert len(reminders) == 1
    assert reminders[0]["user_id"] == 3