"""End-to-end integration test: register → browse tracks → view challenge → submit → leaderboard."""

import pytest


class TestEndToEndFlow:
    """Walk through the full player journey in a single test."""

    @pytest.fixture(autouse=True)
    def _setup_track(self, sample_track):
        self.track = sample_track["track"]
        self.challenge = sample_track["challenge"]
        self.challenge2 = sample_track["challenge2"]

    def test_full_player_journey(self, client):
        # 1. Register
        reg = client.post("/api/v1/auth/register", json={
            "username": "journeyplayer",
            "password": "strongpass99",
        })
        assert reg.status_code == 201
        reg_data = reg.json()
        assert "access_token" in reg_data
        token = reg_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Check profile
        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        me_data = me.json()
        assert me_data["username"] == "journeyplayer"
        assert me_data["total_points"] == 0

        # 3. Browse tracks
        tracks_resp = client.get("/api/v1/tracks", headers=headers)
        assert tracks_resp.status_code == 200
        tracks_data = tracks_resp.json()
        assert "tracks" in tracks_data
        assert len(tracks_data["tracks"]) == 1
        track_info = tracks_data["tracks"][0]
        assert track_info["title"] == "REST Fundamentals"
        assert track_info["unlocked"] is True
        assert track_info["your_progress"] == "0/2 completed"

        # 4. List challenges in track
        track_id = track_info["id"]
        challenges_resp = client.get(f"/api/v1/tracks/{track_id}/challenges", headers=headers)
        assert challenges_resp.status_code == 200
        challenges_list = challenges_resp.json()
        assert len(challenges_list) >= 1
        ch_id = str(self.challenge.id)

        # 5. View challenge detail
        detail = client.get(f"/api/v1/challenges/{ch_id}", headers=headers)
        assert detail.status_code == 200
        detail_data = detail.json()
        assert detail_data["title"] == "Hello, API"
        assert "submit_endpoint" in detail_data
        assert "sandbox_base_url" in detail_data

        # 6. Request a hint
        hint_resp = client.get(f"/api/v1/challenges/{ch_id}/hints/1", headers=headers)
        assert hint_resp.status_code == 200
        assert hint_resp.json()["hint_number"] == 1
        assert hint_resp.json()["point_cost"] == 5

        # 7. Submit wrong answer
        wrong = client.post(f"/api/v1/challenges/{ch_id}/submit", headers=headers, json={
            "method": "POST",
            "path": "/wrong",
        })
        assert wrong.status_code == 200
        wrong_data = wrong.json()
        assert wrong_data["is_correct"] is False
        assert "partial_matches" in wrong_data

        # 8. Submit correct answer
        correct = client.post(f"/api/v1/challenges/{ch_id}/submit", headers=headers, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        assert correct.status_code == 200
        correct_data = correct.json()
        assert correct_data["is_correct"] is True
        assert correct_data["points_earned"] > 0
        assert correct_data["total_points"] > 0

        # 9. Cannot re-submit solved challenge
        dup = client.post(f"/api/v1/challenges/{ch_id}/submit", headers=headers, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books/",
        })
        assert dup.status_code == 400

        # 10. Solve second challenge to complete track
        ch2_id = str(self.challenge2.id)
        solve2 = client.post(f"/api/v1/challenges/{ch2_id}/submit", headers=headers, json={
            "method": "GET",
            "path": "/api/v1/sandbox/books",
        })
        assert solve2.status_code == 200
        solve2_data = solve2.json()
        assert solve2_data["is_correct"] is True
        # Track completion bonus should be included
        total_after_track = solve2_data["total_points"]

        # 11. Check track progress updated
        tracks2 = client.get("/api/v1/tracks", headers=headers)
        track2_info = tracks2.json()["tracks"][0]
        assert track2_info["your_progress"] == "2/2 completed"

        # 12. Global leaderboard shows our player
        lb = client.get("/api/v1/leaderboard", headers=headers)
        assert lb.status_code == 200
        lb_data = lb.json()
        assert lb_data["total_players"] >= 1
        player_entry = next(e for e in lb_data["entries"] if e["username"] == "journeyplayer")
        assert player_entry["total_points"] == total_after_track

        # 13. Weekly leaderboard
        wlb = client.get("/api/v1/leaderboard/weekly", headers=headers)
        assert wlb.status_code == 200
        assert wlb.json()["period"] == "weekly"

        # 14. Track leaderboard
        tlb = client.get(f"/api/v1/leaderboard/track/{track_id}", headers=headers)
        assert tlb.status_code == 200

        # 15. User stats
        user_id = me_data["id"]
        stats = client.get(f"/api/v1/users/{user_id}/stats", headers=headers)
        assert stats.status_code == 200
        stats_data = stats.json()
        assert stats_data["challenges_solved"] == 2
        assert stats_data["total_points"] == total_after_track

        # 16. Profile still consistent
        me_final = client.get("/api/v1/auth/me", headers=headers)
        assert me_final.json()["total_points"] == total_after_track
