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
        ch = _make_challenge(db, track, order=1, points=50)
        _make_challenge(db, track, order=2, points=50)  # prevent track completion
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
        ch = _make_challenge(db, track, order=1, points=50)
        _make_challenge(db, track, order=2, points=50)  # prevent track completion
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
        ch = _make_challenge(db, track, order=1, points=50, time_limit=600)  # 10 min limit
        _make_challenge(db, track, order=2, points=50)  # prevent track completion
        db.commit()

        resp = client.post(
            f"/api/v1/challenges/{ch.id}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        data = resp.json()
        assert data["is_correct"] is True
        assert "Speed Demon" in data["badges_earned"]


class TestTrackCompletionBonus:
    """Completing a track should award 500 × 1.5 = 750 bonus points."""

    def test_track_completion_bonus_awarded(self, client, auth_header, db):
        track = _make_track(db)
        ch1 = _make_challenge(db, track, order=1, points=50)
        ch2 = _make_challenge(db, track, order=2, points=50)
        db.commit()

        # Solve first challenge (track NOT complete yet)
        resp1 = client.post(
            f"/api/v1/challenges/{ch1.id}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        data1 = resp1.json()
        assert data1["is_correct"] is True
        points_after_first = data1["total_points"]

        # Solve second challenge (track COMPLETES → +750 bonus)
        resp2 = client.post(
            f"/api/v1/challenges/{ch2.id}/submit",
            headers=auth_header,
            json={"method": "GET", "path": "/api/v1/sandbox/books/"},
        )
        data2 = resp2.json()
        assert data2["is_correct"] is True
        # Second challenge earns base points + track bonus
        # Base: 50 * 2.0 (first attempt) + streak_bonus(1)*25 = 100 + 25 = 125
        # Track bonus: 500 * 1.5 = 750
        # Total earned on this submit = 125 + 750 = 875
        assert data2["points_earned"] == 875
        assert data2["total_points"] == points_after_first + 875


class TestServiceImports:
    """Verify the three service files are importable and have expected attributes."""

    def test_challenge_service(self):
        from app.services.challenge_service import (
            get_challenge,
            get_track,
            is_track_unlocked,
            list_challenges_in_track,
            list_tracks,
            next_challenge,
        )
        assert callable(list_tracks)
        assert callable(get_track)
        assert callable(get_challenge)
        assert callable(list_challenges_in_track)
        assert callable(next_challenge)
        assert callable(is_track_unlocked)

    def test_submission_service(self):
        from app.services.submission_service import (
            check_already_solved,
            get_attempt_number,
            get_first_attempt,
            save_submission,
            validate,
        )
        assert callable(check_already_solved)
        assert callable(get_attempt_number)
        assert callable(get_first_attempt)
        assert callable(validate)
        assert callable(save_submission)

    def test_notification_service(self):
        from app.services.notification_service import (
            broadcast_leaderboard,
            notify_badge_earned,
            notify_streak_milestone,
            notify_track_completed,
            notify_user,
        )
        assert callable(notify_user)
        assert callable(broadcast_leaderboard)
        assert callable(notify_badge_earned)
        assert callable(notify_streak_milestone)
        assert callable(notify_track_completed)
