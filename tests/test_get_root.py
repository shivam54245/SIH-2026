from fastapi import status


def test_public_healthcheck_returns_string(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    # OAS confirms response is a direct string schema
    assert isinstance(response.json(), str)