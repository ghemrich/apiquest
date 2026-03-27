class TestGetChallenge:
    def test_get_challenge(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        resp = client.get(f"/api/v1/challenges/{cid}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Hello, API"
        assert data["points_value"] == 50
        assert data["hints_available"] == 5
        assert data["hints_revealed"] == 0
        # Must NOT expose solution fields
        assert "expected_method" not in data
        assert "expected_path" not in data
        assert "expected_body" not in data

    def test_get_challenge_not_found(self, client, auth_header):
        import uuid
        resp = client.get(f"/api/v1/challenges/{uuid.uuid4()}", headers=auth_header)
        assert resp.status_code == 404


class TestHints:
    def test_reveal_first_hint(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        resp = client.get(f"/api/v1/challenges/{cid}/hints/1", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["hint_number"] == 1
        assert data["hint"] == "What's the simplest HTTP request?"
        assert data["point_cost"] == 5
        assert data["hints_remaining"] == 4

    def test_must_reveal_in_order(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        # Skip hint 1, try hint 2
        resp = client.get(f"/api/v1/challenges/{cid}/hints/2", headers=auth_header)
        assert resp.status_code == 400
        assert "hint 1" in resp.json()["detail"].lower()

    def test_reveal_sequential(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        client.get(f"/api/v1/challenges/{cid}/hints/1", headers=auth_header)
        resp = client.get(f"/api/v1/challenges/{cid}/hints/2", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["hint_number"] == 2

    def test_invalid_hint_number(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        resp = client.get(f"/api/v1/challenges/{cid}/hints/99", headers=auth_header)
        assert resp.status_code == 400

    def test_hint_idempotent(self, client, auth_header, sample_track):
        """Revealing same hint twice doesn't create duplicate."""
        cid = str(sample_track["challenge"].id)
        resp1 = client.get(f"/api/v1/challenges/{cid}/hints/1", headers=auth_header)
        resp2 = client.get(f"/api/v1/challenges/{cid}/hints/1", headers=auth_header)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # Check hints_revealed didn't double-count
        resp = client.get(f"/api/v1/challenges/{cid}", headers=auth_header)
        assert resp.json()["hints_revealed"] == 1
