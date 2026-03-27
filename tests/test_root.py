def test_welcome_endpoint(client):
    resp = client.get("/api/v1/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["welcome"] == "Welcome to API Quest!"
    assert "getting_started" in data
    assert "step_1" in data["getting_started"]
    assert "documentation" in data


def test_welcome_contains_registration_info(client):
    resp = client.get("/api/v1/")
    data = resp.json()
    assert "register" in data["getting_started"]["step_1"].lower()
    assert "/api/v1/auth/register" in data["getting_started"]["step_1"]
