def test_protected_installation_requires_authentication(client):
    response = client.get("/api/v1/installations/1")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
