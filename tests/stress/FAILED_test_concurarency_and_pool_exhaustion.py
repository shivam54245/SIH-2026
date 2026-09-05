import concurrent.futures
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.database import DoctorPatientLink, UserProfile


def test_concurrent_parallel_inserts_on_memory_pool(
    client: TestClient, patient_headers: dict
):
    # Runs 10 concurrent requests to test StaticPool connection locking
    def send_post(index: int):
        payload = {
            "game_session": [
                {
                    "game_type": f"parallel_{index}",
                    "game_data": f'{{"thread_id": {index}}}'
                }
            ]
        }
        return client.post("/myaccount/games", json=payload, headers=patient_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_post, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for res in results:
        assert res.status_code < 500, f"Thread failed with server error: {res.text}"


def test_interleaved_read_during_write_contention(
    client: TestClient, patient_headers: dict
):
    # Alternates rapid writes and reads to stress transaction isolation
    def writer(i: int):
        payload = {
            "game_session": [
                {"game_type": f"write_race_{i}", "game_data": "{}"}
            ]
        }
        return client.post("/myaccount/games", json=payload, headers=patient_headers)

    def reader():
        return client.get("/myaccount/games", headers=patient_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        write_futures = [executor.submit(writer, i) for i in range(10)]
        read_futures = [executor.submit(reader) for _ in range(10)]
        all_results = [f.result() for f in concurrent.futures.as_completed(write_futures + read_futures)]

    for res in all_results:
        assert res.status_code < 500, f"Read/Write contention threw 500: {res.text}"


def test_rapid_fire_batch_burst_without_backoff(
    client: TestClient, patient_headers: dict
):
    # Fires 30 back-to-back requests sequentially to identify unclosed sessions
    for i in range(30):
        payload = {
            "game_session": [
                {"game_type": f"burst_{i}", "game_data": "{}"}
            ]
        }
        res = client.post("/myaccount/games", json=payload, headers=patient_headers)
        assert res.status_code < 500, f"Burst request #{i} failed with status {res.status_code}"


def test_simulated_cross_table_lock_deadlock(
    client: TestClient, test_db_session: Session, admin_headers: dict
):
    # Simulates simultaneous assignments to test foreign key verification locking
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    def assign_call():
        return client.post(
            "/assign",
            json={"doctor_id": doctor.id, "patient_id": patient.id},
            headers=admin_headers
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(assign_call) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for res in results:
        assert res.status_code < 500, f"Deadlock check failed with 500: {res.text}"


def test_rapid_session_commit_and_query_saturation(
    client: TestClient, patient_headers: dict
):
    # Creates games and reminders in rapid succession to ensure no session leaks occur
    for step in range(15):
        g_res = client.post(
            "/myaccount/games",
            json={"game_session": [{"game_type": "saturate", "game_data": "{}"}]},
            headers=patient_headers
        )
        assert g_res.status_code < 500

        r_res = client.post(
            "/myaccount/reminders",
            json={"reminder": [{"message": "sync", "time": "08:00"}]},
            headers=patient_headers
        )
        assert r_res.status_code < 500


def test_connection_lease_depletion_under_high_read_counts(
    client: TestClient, patient_headers: dict
):
    # Rapidly issues 50 GET requests to verify SQLite cursors are closed properly
    for _ in range(50):
        res = client.get("/myaccount/games", headers=patient_headers)
        assert res.status_code < 500, f"Cursor exhaustion on read: {res.text}"


def test_concurrent_writes_targeting_identical_patient_id(
    client: TestClient, test_db_session: Session, admin_headers: dict
):
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    def admin_insert(idx: int):
        payload = {
            "game_session": [
                {
                    "patient_id": patient.id,
                    "game_type": f"target_race_{idx}",
                    "game_data": "{}"
                }
            ]
        }
        return client.post("/games", json=payload, headers=admin_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(admin_insert, i) for i in range(12)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for res in results:
        assert res.status_code < 500, f"Target collision generated 500: {res.text}"


def test_high_frequency_doctor_queries_during_patient_writes(
    client: TestClient, test_db_session: Session, doctor_headers: dict, patient_headers: dict
):
    doctor = test_db_session.exec(select(UserProfile).where(UserProfile.email == "doctor@example.com")).first()
    patient = test_db_session.exec(select(UserProfile).where(UserProfile.email == "patient@example.com")).first()

    # Create link
    test_db_session.add(DoctorPatientLink(doctor_id=doctor.id, patient_id=patient.id))
    test_db_session.commit()

    def patient_write(i: int):
        return client.post(
            "/myaccount/games",
            json={"game_session": [{"game_type": f"race_{i}", "game_data": "{}"}]},
            headers=patient_headers
        )

    def doctor_read():
        return client.get(f"/myaccount/patients/games?patient_id={patient.id}", headers=doctor_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(patient_write, i) for i in range(6)] + [executor.submit(doctor_read) for _ in range(6)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for res in results:
        assert res.status_code < 500, f"Simultaneous read/write caused 500: {res.text}"


def test_bulk_reminders_racing_bulk_games(
    client: TestClient, patient_headers: dict
):
    def send_reminders():
        payload = {
            "reminder": [
                {"message": f"rem_{i}", "time": "12:00"}
                for i in range(25)
            ]
        }
        return client.post("/myaccount/reminders", json=payload, headers=patient_headers)

    def send_games():
        payload = {
            "game_session": [
                {"game_type": f"game_{i}", "game_data": "{}"}
                for i in range(25)
            ]
        }
        return client.post("/myaccount/games", json=payload, headers=patient_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(send_reminders) for _ in range(4)] + [executor.submit(send_games) for _ in range(4)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for res in results:
        assert res.status_code < 500, f"Cross-domain batch race threw 500: {res.text}"


def test_connection_starvation_under_rapid_thread_cycling(
    client: TestClient, patient_headers: dict
):
    # Opens and collapses thread contexts quickly to check thread pool cleanup
    for _ in range(5):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(client.get, "/myaccount/games", headers=patient_headers)
                for _ in range(10)
            ]
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                assert res.status_code < 500
