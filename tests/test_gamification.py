"""Tests for gamification service and leaderboard."""

from datetime import date, timedelta

from app.models.challenge import Challenge, Difficulty, Track
from app.models.gamification import Badge
from app.services.gamification_service import (
    update_streak,
    update_track_progress,
)


def _make_track(db, title="Test Track", difficulty=Difficulty.beginner):
    track = Track(title=title, description="desc", difficulty=difficulty, order_index=1)
    db.add(track)
    db.flush()
    return track


def _make_challenge(db, track, order=1, points=50):
    ch = Challenge(
        track_id=track.id, title=f"Ch {order}", description="d",
        difficulty=track.difficulty, points_value=points,
        expected_method="GET", expected_path="/test",
        hints=["h1"], order_index=order, sandbox_endpoint="/s",
    )
    db.add(ch)
    db.flush()
    return ch


def _make_badge(db, name, criteria_type, criteria_value):
    badge = Badge(name=name, description="d", criteria_type=criteria_type, criteria_value=criteria_value)
    db.add(badge)
    db.flush()
    return badge


class TestStreak:
    def test_first_activity(self, db, registered_user):
        from app.models.user import User
        user = db.query(User).filter(User.username == "testplayer").first()
        update_streak(db, user)
        assert user.current_streak == 1
        assert user.last_active_date == date.today()

    def test_consecutive_day(self, db, registered_user):
        from app.models.user import User
        user = db.query(User).filter(User.username == "testplayer").first()
        user.last_active_date = date.today() - timedelta(days=1)
        user.current_streak = 3
        db.flush()
        update_streak(db, user)
        assert user.current_streak == 4

    def test_same_day_no_change(self, db, registered_user):
        from app.models.user import User
        user = db.query(User).filter(User.username == "testplayer").first()
        user.last_active_date = date.today()
        user.current_streak = 5
        db.flush()
        update_streak(db, user)
        assert user.current_streak == 5

    def test_streak_reset(self, db, registered_user):
        from app.models.user import User
        user = db.query(User).filter(User.username == "testplayer").first()
        user.last_active_date = date.today() - timedelta(days=3)
        user.current_streak = 10
        user.longest_streak = 10
        db.flush()
        update_streak(db, user)
        assert user.current_streak == 1
        assert user.longest_streak == 10


class TestTrackProgress:
    def test_creates_progress(self, db, registered_user):
        from app.models.user import User
        from app.models.submission import Submission
        user = db.query(User).filter(User.username == "testplayer").first()
        track = _make_track(db)
        ch = _make_challenge(db, track, order=1)
        db.add(Submission(
            user_id=user.id, challenge_id=ch.id,
            submitted_method="GET", submitted_path="/test",
            is_correct=True, points_earned=50,
        ))
        db.flush()
        progress = update_track_progress(db, user.id, track.id)
        assert progress.challenges_completed == 1

    def test_marks_complete(self, db, registered_user):
        from app.models.user import User
        from app.models.submission import Submission
        user = db.query(User).filter(User.username == "testplayer").first()
        track = _make_track(db)
        ch = _make_challenge(db, track, order=1)
        db.add(Submission(
            user_id=user.id, challenge_id=ch.id,
            submitted_method="GET", submitted_path="/test",
            is_correct=True, points_earned=50,
        ))
        db.flush()
        progress = update_track_progress(db, user.id, track.id)
        assert progress.completed_at is not None


class TestBadgeAward:
    def test_first_steps_badge(self, client, auth_header, sample_track, db):
        """Solving first challenge should earn First Steps badge if badge exists."""
        _make_badge(db, "First Steps", "challenge_count", 1)
        db.commit()
        cid = str(sample_track["challenge"].id)
        resp = client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        data = resp.json()
        assert data["is_correct"] is True
        assert "First Steps" in data["badges_earned"]


class TestLeaderboard:
    def test_global_leaderboard(self, client, auth_header):
        resp = client.get("/api/v1/leaderboard", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["period"] == "all-time"

    def test_weekly_leaderboard(self, client, auth_header):
        resp = client.get("/api/v1/leaderboard/weekly", headers=auth_header)
        assert resp.status_code == 200

    def test_leaderboard_no_auth(self, client):
        resp = client.get("/api/v1/leaderboard")
        assert resp.status_code == 401

    def test_leaderboard_has_entries(self, client, auth_header, sample_track):
        # Solve a challenge to get points
        cid = str(sample_track["challenge"].id)
        client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        resp = client.get("/api/v1/leaderboard", headers=auth_header)
        entries = resp.json()["entries"]
        assert len(entries) >= 1
        assert entries[0]["total_points"] > 0

    def test_track_leaderboard(self, client, auth_header, sample_track):
        track_id = str(sample_track["track"].id)
        cid = str(sample_track["challenge"].id)
        client.post(f"/api/v1/challenges/{cid}/submit", headers=auth_header, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        resp = client.get(f"/api/v1/leaderboard/track/{track_id}", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["entries"]) >= 1
