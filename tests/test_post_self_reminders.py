from fastapi import status


def test_post_self_reminders_unauthorized(client):
    res = client.post(
        "/self/reminders",
        json={"reminder": [{"time": "08:00", "message": "Morning pill"}]},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_post_self_reminders_forbidden_for_doctor(client, doctor_headers):
    res = client.post(
        "/self/reminders",
        json={"reminder": [{"time": "08:00", "message": "Morning pill"}]},
        headers=doctor_headers,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_post_self_reminders_success_and_verifiable_via_get(
    client, patient_headers
):
    payload = {
        "reminder": [
            {"time": "08:30", "message": "Take Vitamin D"},
            {"time": "20:30", "message": "Take Evening Walk"},
        ]
    }
    post_res = client.post(
        "/self/reminders", json=payload, headers=patient_headers
    )
    print(post_res.json())
    assert post_res.status_code == status.HTTP_201_CREATED

    get_res = client.get("/self/reminders", headers=patient_headers)
    assert get_res.status_code == status.HTTP_200_OK
    reminders = (
        get_res.json().get("data", get_res.json())
        if isinstance(get_res.json(), dict)
        else get_res.json()
    )
    assert len(reminders) >= 2
    messages = [r["message"] for r in reminders]
    assert "Take Vitamin D" in messages
    assert "Take Evening Walk" in messages