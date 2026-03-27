"""Tests for user profile, stats, badges, and progress endpoints."""

import uuid


class TestGetProfile:
    def test_get_my_profile(self, client, auth_header):
        resp = client.get("/api/v1/users/me", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testplayer"
        assert data["email"] == "test@example.com"
        assert data["total_points"] == 0
        assert data["current_streak"] == 0

    def test_get_my_profile_unauthenticated(self, client):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401


class TestUpdateProfile:
    def test_update_username(self, client, auth_header):
        resp = client.put("/api/v1/users/me", json={"username": "newname"}, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["username"] == "newname"

    def test_update_bio(self, client, auth_header):
        resp = client.put("/api/v1/users/me", json={"bio": "I love APIs"}, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["bio"] == "I love APIs"

    def test_update_avatar_url(self, client, auth_header):
        resp = client.put(
            "/api/v1/users/me",
            json={"avatar_url": "https://example.com/avatar.png"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["avatar_url"] == "https://example.com/avatar.png"

    def test_update_username_conflict(self, client, auth_header):
        # Register a second user
        client.post("/api/v1/auth/register", json={
            "username": "otherplayer",
            "email": "other@example.com",
            "password": "securepass123",
        })
        resp = client.put("/api/v1/users/me", json={"username": "otherplayer"}, headers=auth_header)
        assert resp.status_code == 409

    def test_update_no_change(self, client, auth_header):
        resp = client.put("/api/v1/users/me", json={}, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testplayer"


class TestDeleteAccount:
    def test_delete_account(self, client, auth_header):
        resp = client.delete("/api/v1/users/me", headers=auth_header)
        assert resp.status_code == 204

        # Verify can't access profile anymore
        resp2 = client.get("/api/v1/users/me", headers=auth_header)
        assert resp2.status_code == 401

    def test_delete_account_with_submissions(self, client, auth_header, sample_track):
        """Delete should cascade and remove submissions, badges, progress, hints."""
        challenge = sample_track["challenge"]
        # Submit a solution first
        client.post(
            f"/api/v1/challenges/{challenge.id}/submit",
            json={
                "method": challenge.expected_method,
                "path": challenge.expected_path,
            },
            headers=auth_header,
        )
        resp = client.delete("/api/v1/users/me", headers=auth_header)
        assert resp.status_code == 204


class TestPublicProfile:
    def test_get_user_profile(self, client, registered_user, auth_header):
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testplayer"
        # Email should not be in public profile (value is None)
        assert data.get("email") is None

    def test_get_user_not_found(self, client, auth_header):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/users/{fake_id}", headers=auth_header)
        assert resp.status_code == 404

    def test_get_user_unauthenticated(self, client, registered_user):
        resp = client.get(f"/api/v1/users/{registered_user['id']}")
        assert resp.status_code == 401


class TestUserStats:
    def test_get_stats_fresh_user(self, client, registered_user, auth_header):
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/stats", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_points"] == 0
        assert data["challenges_solved"] == 0
        assert data["badges_earned"] == 0
        assert data["completion_percentage"] == 0.0
        assert data["global_rank"] == 1  # Only user → rank 1

    def test_get_stats_after_solve(self, client, auth_header, registered_user, sample_track):
        challenge = sample_track["challenge"]
        client.post(
            f"/api/v1/challenges/{challenge.id}/submit",
            json={
                "method": challenge.expected_method,
                "path": challenge.expected_path,
            },
            headers=auth_header,
        )
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/stats", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["challenges_solved"] == 1
        assert data["total_points"] > 0
        assert data["current_streak"] == 1

    def test_get_stats_not_found(self, client, auth_header):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/users/{fake_id}/stats", headers=auth_header)
        assert resp.status_code == 404


class TestUserBadges:
    def test_get_badges_empty(self, client, registered_user, auth_header):
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/badges", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_badges_after_earn(self, client, auth_header, registered_user, sample_track, db):
        """Earn a badge by solving a challenge and check it appears."""
        from app.models.gamification import Badge
        badge = Badge(
            name="First Steps",
            description="Solve your first challenge",
            criteria_type="challenge_count",
            criteria_value=1,
        )
        db.add(badge)
        db.commit()

        challenge = sample_track["challenge"]
        client.post(
            f"/api/v1/challenges/{challenge.id}/submit",
            json={
                "method": challenge.expected_method,
                "path": challenge.expected_path,
            },
            headers=auth_header,
        )

        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/badges", headers=auth_header)
        assert resp.status_code == 200
        badges = resp.json()
        assert len(badges) == 1
        assert badges[0]["name"] == "First Steps"
        assert badges[0]["earned_at"] is not None

    def test_get_badges_not_found(self, client, auth_header):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/users/{fake_id}/badges", headers=auth_header)
        assert resp.status_code == 404


class TestUserProgress:
    def test_get_progress_no_tracks(self, client, registered_user, auth_header):
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/progress", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_progress_with_track(self, client, registered_user, auth_header, sample_track):
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/progress", headers=auth_header)
        assert resp.status_code == 200
        progress = resp.json()
        assert len(progress) == 1
        assert progress[0]["track_title"] == "REST Fundamentals"
        assert progress[0]["total_challenges"] == 2
        assert progress[0]["challenges_completed"] == 0
        assert progress[0]["completion_percentage"] == 0.0

    def test_get_progress_after_solve(self, client, auth_header, registered_user, sample_track):
        challenge = sample_track["challenge"]
        client.post(
            f"/api/v1/challenges/{challenge.id}/submit",
            json={
                "method": challenge.expected_method,
                "path": challenge.expected_path,
            },
            headers=auth_header,
        )

        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/progress", headers=auth_header)
        assert resp.status_code == 200
        progress = resp.json()
        assert progress[0]["challenges_completed"] == 1
        assert progress[0]["completion_percentage"] == 50.0

    def test_get_progress_not_found(self, client, auth_header):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/users/{fake_id}/progress", headers=auth_header)
        assert resp.status_code == 404
