"""Tests for gap-fix features: points formula, change-password, badges in /me, stats fields."""


from app.models.challenge import Challenge, Difficulty, Track
from app.models.gamification import Badge


def _make_track(db, title="Test Track", difficulty=Difficulty.beginner):
    track = Track(title=title, description="desc", difficulty=difficulty, order_index=1)
    db.add(track)
    db.flush()
    return track


def _make_challenge(db, track, order=1, points=50, time_limit=None):
    ch = Challenge(
        track_id=track.id, title=f"Ch {order}", description="d",
        difficulty=track.difficulty, points_value=points,
        expected_method="GET", expected_path="/api/v1/sandbox/books/",
        hints=["h1"], order_index=order, sandbox_endpoint="/api/v1/sandbox/books",
        time_limit_seconds=time_limit,
    )
    db.add(ch)
    db.flush()
    return ch


def _make_badge(db, name, criteria_type, criteria_value):
    badge = Badge(name=name, description="d", criteria_type=criteria_type, criteria_value=criteria_value)
    db.add(badge)
    db.flush()
    return badge


class TestPointsFormula:
    """Verify time_bonus and streak_bonus in points calculation."""

    def test_streak_bonus_applied(self, client, auth_header, db, registered_user):
        """Streak bonus = min(streak, 7) * 25 added to points."""
        from app.models.user import User
        user = db.query(User).filter(User.username == "testplayer").first()
        user.current_streak = 5
        db.flush()

        track = _make_track(db)
        ch = _make_challenge(db, track, points=50)
        db.commit()

        resp = client.post(
            f"/api/v1/challenges/{ch.id}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        data = resp.json()
        assert data["is_correct"] is True
        # base=50, first attempt multiplier=2.0, streak_bonus = min(5,7)*25 = 125
        # (50 - 0) * 2.0 + 0 + 125 = 225
        # But streak gets incremented before calculation in submit flow,
        # Actually — streak updates AFTER points calculation in the current code.
        # The current_streak passed to _calculate_points is user.current_streak at call time.
        # The submit flow: if correct → points = _calculate_points(..., current_streak=current_user.current_streak)
        # Then update_streak increments it. So streak=5 at calculation time.
        # (50) * 2.0 + 0 + min(5,7)*25 = 100 + 125 = 225
        assert data["points_earned"] == 225

    def test_streak_bonus_capped_at_7(self, client, auth_header, db, registered_user):
        """Streak bonus caps at 7 * 25 = 175."""
        from app.models.user import User
        user = db.query(User).filter(User.username == "testplayer").first()
        user.current_streak = 15
        db.flush()

        track = _make_track(db)
        ch = _make_challenge(db, track, points=50)
        db.commit()

        resp = client.post(
            f"/api/v1/challenges/{ch.id}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        data = resp.json()
        # (50) * 2.0 + 0 + min(15,7)*25 = 100 + 175 = 275
        assert data["points_earned"] == 275


class TestChangePassword:
    def test_change_password_success(self, client, auth_header):
        resp = client.post(
            "/api/v1/auth/change-password",
            headers=auth_header,
            json={"current_password": "securepass123", "new_password": "newpass12345"},
        )
        assert resp.status_code == 200
        assert "changed" in resp.json()["message"].lower()

        # Login with new password
        resp2 = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "newpass12345",
        })
        assert resp2.status_code == 200

    def test_change_password_wrong_current(self, client, auth_header):
        resp = client.post(
            "/api/v1/auth/change-password",
            headers=auth_header,
            json={"current_password": "wrongpassword", "new_password": "newpass12345"},
        )
        assert resp.status_code == 401

    def test_change_password_short_new(self, client, auth_header):
        resp = client.post(
            "/api/v1/auth/change-password",
            headers=auth_header,
            json={"current_password": "securepass123", "new_password": "short"},
        )
        assert resp.status_code == 422

    def test_change_password_no_auth(self, client):
        resp = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "securepass123", "new_password": "newpass12345"},
        )
        assert resp.status_code == 401


class TestBadgesInMe:
    def test_me_has_badges_field(self, client, auth_header):
        resp = client.get("/api/v1/auth/me", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "badges" in data
        assert data["badges"] == []

    def test_me_shows_earned_badges(self, client, auth_header, sample_track, db):
        _make_badge(db, "First Steps", "challenge_count", 1)
        db.commit()

        cid = str(sample_track["challenge"].id)
        client.post(
            f"/api/v1/challenges/{cid}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )

        resp = client.get("/api/v1/auth/me", headers=auth_header)
        assert "First Steps" in resp.json()["badges"]

    def test_users_me_has_badges(self, client, auth_header):
        resp = client.get("/api/v1/users/me", headers=auth_header)
        assert resp.status_code == 200
        assert "badges" in resp.json()
        assert resp.json()["badges"] == []


class TestStatsFields:
    def test_stats_has_average_solve_time(self, client, auth_header, registered_user, sample_track):
        user_id = registered_user["id"]
        # Solve a challenge
        cid = str(sample_track["challenge"].id)
        client.post(
            f"/api/v1/challenges/{cid}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )

        resp = client.get(f"/api/v1/users/{user_id}/stats", headers=auth_header)
        data = resp.json()
        assert "average_solve_time" in data
        # Could be 0.0 or a small positive number
        assert data["average_solve_time"] is None or data["average_solve_time"] >= 0

    def test_stats_has_tier_progress(self, client, auth_header, registered_user, sample_track):
        user_id = registered_user["id"]
        resp = client.get(f"/api/v1/users/{user_id}/stats", headers=auth_header)
        data = resp.json()
        assert "tier_progress" in data
        # Before solving: "Beginner 0%"
        assert data["tier_progress"] is not None
        assert "Beginner" in data["tier_progress"]

    def test_stats_tier_progress_after_solve(self, client, auth_header, registered_user, sample_track):
        user_id = registered_user["id"]
        cid = str(sample_track["challenge"].id)
        client.post(
            f"/api/v1/challenges/{cid}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        resp = client.get(f"/api/v1/users/{user_id}/stats", headers=auth_header)
        data = resp.json()
        # sample_track has 2 beginner challenges, solved 1 → 50%
        assert "Beginner 50%" in data["tier_progress"]


class TestSpeedDemonBadge:
    def test_speed_demon_badge_awarded(self, client, auth_header, db):
        """Speed Demon badge: solve challenges under time limit."""
        _make_badge(db, "Speed Demon", "speed_solves", 1)

        track = _make_track(db)
        ch = _make_challenge(db, track, points=50, time_limit=600)  # 10 min limit
        db.commit()

        resp = client.post(
            f"/api/v1/challenges/{ch.id}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        data = resp.json()
        assert data["is_correct"] is True
        assert "Speed Demon" in data["badges_earned"]
