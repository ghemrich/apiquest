class TestListTracks:
    def test_list_tracks(self, client, auth_header, sample_track):
        resp = client.get("/api/v1/tracks", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "tracks" in data
        tracks = data["tracks"]
        assert len(tracks) == 1
        assert tracks[0]["title"] == "REST Fundamentals"
        assert tracks[0]["challenge_count"] == 2
        assert tracks[0]["your_progress"] == "0/2 completed"
        assert tracks[0]["unlocked"] is True

    def test_list_tracks_no_auth(self, client):
        resp = client.get("/api/v1/tracks")
        assert resp.status_code == 401


class TestGetTrack:
    def test_get_track_detail(self, client, auth_header, sample_track):
        track_id = str(sample_track["track"].id)
        resp = client.get(f"/api/v1/tracks/{track_id}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "REST Fundamentals"
        assert len(data["challenges"]) == 2
        assert data["challenges"][0]["title"] == "Hello, API"
        assert data["challenges"][0]["solved"] is False

    def test_get_nonexistent_track(self, client, auth_header):
        import uuid
        resp = client.get(f"/api/v1/tracks/{uuid.uuid4()}", headers=auth_header)
        assert resp.status_code == 404


class TestListTrackChallenges:
    def test_list_challenges(self, client, auth_header, sample_track):
        track_id = str(sample_track["track"].id)
        resp = client.get(f"/api/v1/tracks/{track_id}/challenges", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["title"] == "Hello, API"
        assert data[1]["title"] == "The Library"
