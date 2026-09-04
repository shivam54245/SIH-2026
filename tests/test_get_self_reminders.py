from fastapi import status


def test_get_self_reminders_unauthorized(client):
    res = client.get("/self/reminders")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_self_reminders_forbidden_for_doctor(client, doctor_headers):
    res = client.get("/self/reminders", headers=doctor_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_get_self_reminders_patient_isolation(
    client, admin_headers, patient_headers
):
    # 1. Register a second patient to generate a valid user with role=PATIENT
    create_patient_res = client.post(
        "/users",
        headers=admin_headers,
        json={
            "email": "patient_isolation_test@example.com",
            "password": "Password123!",
            "full_name": "Second Patient",
            "role": "patient",
        },
    )
    assert create_patient_res.status_code == status.HTTP_201_CREATED
    patient2_id = create_patient_res.json()["data"]["user_id"]

    # 2. Seed reminders for both valid patients
    post_res = client.post(
        "/reminders",
        json={
            "reminder": [
                {
                    "patient_id": 3,
                    "time": "07:00",
                    "message": "Patient 1 Meds",
                },
                {
                    "patient_id": patient2_id,
                    "time": "08:00",
                    "message": "Patient 2 Meds",
                },
            ]
        },
        headers=admin_headers,
    )
    assert post_res.status_code == status.HTTP_201_CREATED

    # 3. Patient 3 fetches their own reminders; only their 1 reminder should appear
    res = client.get("/self/reminders", headers=patient_headers)
    assert res.status_code == status.HTTP_200_OK
    reminders = res.json().get("data", res.json())
    assert len(reminders) == 1
    assert reminders[0]["message"] == "Patient 1 Meds"