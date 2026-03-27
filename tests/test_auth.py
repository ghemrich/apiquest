import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "newplayer",
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newplayer"
        assert data["email"] == "new@example.com"
        assert data["total_points"] == 0
        assert data["current_streak"] == 0
        assert "access_token" in data
        assert "refresh_token" in data
        assert "message" in data

    def test_register_duplicate_email(self, client, registered_user):
        resp = client.post("/api/v1/auth/register", json={
            "username": "another",
            "email": "test@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 409
        assert "email" in resp.json()["detail"].lower()

    def test_register_duplicate_username(self, client, registered_user):
        resp = client.post("/api/v1/auth/register", json={
            "username": "testplayer",
            "email": "other@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 409
        assert "username" in resp.json()["detail"].lower()

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "player",
            "email": "p@example.com",
            "password": "short",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "player",
            "email": "not-an-email",
            "password": "securepass123",
        })
        assert resp.status_code == 422

    def test_register_short_username(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "ab",
            "email": "p@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "message" in data

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_success(self, client, registered_user):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["refresh_token"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_fails(self, client, registered_user):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_user["access_token"],
        })
        assert resp.status_code == 401

    def test_refresh_with_garbage_token(self, client):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "not.a.valid.token",
        })
        assert resp.status_code == 401


class TestMe:
    def test_me_authenticated(self, client, auth_header):
        resp = client.get("/api/v1/auth/me", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testplayer"
        assert data["email"] == "test@example.com"
        assert data["total_points"] == 0
        assert "next_step" in data

    def test_me_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer garbage.token.here",
        })
        assert resp.status_code == 401
