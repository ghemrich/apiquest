class TestSubmitSolution:
    def test_correct_submission(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        resp = client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["feedback"] == "Correct! Challenge solved!"
        assert data["points_earned"] == 100  # 50 base × 2.0 first attempt
        assert data["first_attempt_bonus"] is True
        assert data["total_points"] == 100
        assert data["next_challenge"] is not None

    def test_incorrect_submission(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        resp = client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "POST",
            "path": "/api/v1/sandbox/books/",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is False
        assert data["partial_matches"]["method"] is False
        assert data["partial_matches"]["path"] is True
        assert data["hints_available"] == 5

    def test_cannot_resubmit_after_solve(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        resp = client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        assert resp.status_code == 400
        assert "already solved" in resp.json()["detail"].lower()

    def test_second_attempt_lower_points(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        # First attempt: wrong
        client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "POST",
            "path": "/wrong",
        })
        # Second attempt: correct
        resp = client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        data = resp.json()
        assert data["is_correct"] is True
        assert data["points_earned"] == 75  # 50 × 1.5 second attempt
        assert data["first_attempt_bonus"] is False

    def test_with_hints_penalty(self, client, auth_header, sample_track):
        cid = str(sample_track["challenge"].id)
        # Reveal 2 hints (cost: 5 + 10 = 15)
        client.get(f"/api/v1/challenges/{cid}/hints/1", headers=auth_header)
        client.get(f"/api/v1/challenges/{cid}/hints/2", headers=auth_header)
        # Submit correct on first attempt
        resp = client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        data = resp.json()
        assert data["is_correct"] is True
        # (50 - 15) × 2.0 = 70
        assert data["points_earned"] == 70

    def test_challenge_not_found(self, client, auth_header):
        import uuid
        resp = client.post(f"/api/v1/challenges/{uuid.uuid4()}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/test",
        })
        assert resp.status_code == 404

    def test_no_auth(self, client, sample_track):
        cid = str(sample_track["challenge"].id)
        resp = client.post(f"/api/v1/challenges/{cid}/submit", json={
            "method": "GET",
            "path": "/test",
        })
        assert resp.status_code == 401

    def test_points_update_on_user(self, client, auth_header, sample_track, registered_user):
        """After solving, user's total_points should reflect on /me."""
        cid = str(sample_track["challenge"].id)
        client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        resp = client.get("/api/v1/auth/me", headers=auth_header)
        assert resp.json()["total_points"] == 100

    def test_track_progress_updates_after_solve(self, client, auth_header, sample_track):
        """After solving a challenge, track listing should show progress."""
        cid = str(sample_track["challenge"].id)
        client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        resp = client.get("/api/v1/tracks", headers=auth_header)
        data = resp.json()
        assert data["tracks"][0]["your_progress"] == "1/2 completed"
