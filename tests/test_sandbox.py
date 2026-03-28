"""Tests for all sandbox mock APIs."""


class TestBooksAPI:
    def test_books_root(self, client):
        resp = client.get("/api/v1/sandbox/books/")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert data["total"] >= 25

    def test_list_books(self, client):
        resp = client.get("/api/v1/sandbox/books/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 25
        assert len(data["data"]) == 10  # default per_page

    def test_list_books_pagination(self, client):
        resp = client.get("/api/v1/sandbox/books/?page=2&per_page=5")
        data = resp.json()
        assert data["page"] == 2
        assert data["per_page"] == 5
        assert len(data["data"]) == 5

    def test_get_book_42(self, client):
        resp = client.get("/api/v1/sandbox/books/42")
        assert resp.status_code == 200
        assert resp.json()["title"] == "API Design Patterns"

    def test_get_book_not_found(self, client):
        resp = client.get("/api/v1/sandbox/books/9999")
        assert resp.status_code == 404

    def test_create_book(self, client):
        resp = client.post(
            "/api/v1/sandbox/books/",
            json={"title": "New Book", "author": "Author", "year": 2025},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "New Book"

    def test_create_book_missing_fields(self, client):
        resp = client.post(
            "/api/v1/sandbox/books/",
            json={"title": "Only Title"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_update_book(self, client):
        resp = client.put(
            "/api/v1/sandbox/books/42",
            json={"title": "Updated", "author": "Auth", "year": 2025},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    def test_delete_collection_not_allowed(self, client):
        resp = client.delete("/api/v1/sandbox/books/")
        assert resp.status_code == 405

    def test_status_check(self, client):
        resp = client.post("/api/v1/sandbox/books/status-check", json={"codes": [404, 400, 405]})
        assert resp.status_code == 200
        assert resp.json()["all_correct"] is True

    def test_status_check_wrong_answer(self, client):
        resp = client.post("/api/v1/sandbox/books/status-check", json={"codes": [200, 201, 204]})
        assert resp.status_code == 200
        assert resp.json()["all_correct"] is False


class TestTasksAPI:
    def test_list_all(self, client):
        resp = client.get("/api/v1/sandbox/tasks/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 100

    def test_filter_by_status(self, client):
        resp = client.get("/api/v1/sandbox/tasks/?status=completed")
        data = resp.json()
        assert all(t["status"] == "completed" for t in data["data"])

    def test_search(self, client):
        resp = client.get("/api/v1/sandbox/tasks/?search=database")
        data = resp.json()
        assert all("database" in t["title"].lower() for t in data["data"])

    def test_sort_descending(self, client):
        resp = client.get("/api/v1/sandbox/tasks/?sort=-id")
        data = resp.json()
        ids = [t["id"] for t in data["data"]]
        assert ids == sorted(ids, reverse=True)

    def test_field_selection(self, client):
        resp = client.get("/api/v1/sandbox/tasks/?fields=title,status")
        data = resp.json()
        for t in data["data"]:
            assert set(t.keys()) == {"title", "status"}

    def test_invalid_field(self, client):
        resp = client.get("/api/v1/sandbox/tasks/?fields=nonexistent")
        assert resp.status_code == 400

    def test_pagination_metadata(self, client):
        resp = client.get("/api/v1/sandbox/tasks/?per_page=5")
        data = resp.json()
        assert data["per_page"] == 5
        assert data["total_pages"] == 20


class TestMockAuthAPI:
    def test_login_success(self, client):
        resp = client.post("/api/v1/sandbox/mock-auth/login", json={"username": "player1", "password": "quest123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        resp = client.post("/api/v1/sandbox/mock-auth/login", json={"username": "player1", "password": "wrong"})
        assert resp.status_code == 401

    def test_profile_with_token(self, client):
        login = client.post("/api/v1/sandbox/mock-auth/login", json={"username": "player1", "password": "quest123"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/sandbox/mock-auth/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "player1"

    def test_profile_no_auth(self, client):
        resp = client.get("/api/v1/sandbox/mock-auth/profile")
        assert resp.status_code == 401

    def test_admin_access(self, client):
        login = client.post("/api/v1/sandbox/mock-auth/login", json={"username": "admin1", "password": "adminquest123"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/sandbox/mock-auth/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_admin_forbidden_for_user(self, client):
        login = client.post("/api/v1/sandbox/mock-auth/login", json={"username": "player1", "password": "quest123"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/sandbox/mock-auth/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_api_key(self, client):
        resp = client.get("/api/v1/sandbox/mock-auth/external/data", headers={"X-API-Key": "sk_test_abc123xyz"})
        assert resp.status_code == 200

    def test_api_key_wrong(self, client):
        resp = client.get("/api/v1/sandbox/mock-auth/external/data", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

    def test_cors_options(self, client):
        resp = client.options("/api/v1/sandbox/mock-auth/cors-test")
        assert resp.status_code == 200
        assert "Access-Control-Allow-Origin" in resp.headers

    def test_input_sanitization(self, client):
        resp = client.post("/api/v1/sandbox/mock-auth/users", json={"name": "<script>alert('xss')</script>"})
        assert resp.status_code == 400
        assert "invalid characters" in resp.json()["detail"]


class TestUsersDataAPI:
    def test_list_users(self, client):
        resp = client.get("/api/v1/sandbox/users-data/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 10

    def test_get_user_projects(self, client):
        resp = client.get("/api/v1/sandbox/users-data/7/projects")
        assert resp.status_code == 200

    def test_deep_nesting(self, client):
        resp = client.get("/api/v1/sandbox/users-data/7/projects/3/tasks")
        assert resp.status_code == 200

    def test_include_tasks(self, client):
        resp = client.get("/api/v1/sandbox/users-data/projects/3?include=tasks")
        assert resp.status_code == 200
        assert "tasks" in resp.json()

    def test_without_include(self, client):
        resp = client.get("/api/v1/sandbox/users-data/projects/3")
        assert resp.status_code == 200
        assert "tasks" not in resp.json()

    def test_create_task(self, client):
        resp = client.post("/api/v1/sandbox/users-data/tasks", json={"title": "New task", "project_id": 1, "priority": "low"})
        assert resp.status_code == 201

    def test_create_task_invalid_project(self, client):
        resp = client.post("/api/v1/sandbox/users-data/tasks", json={"title": "T", "project_id": 999})
        assert resp.status_code == 400

    def test_add_team_member(self, client):
        resp = client.post("/api/v1/sandbox/users-data/teams/2/members", json={"user_id": 7})
        assert resp.status_code == 201

    def test_add_team_member_conflict(self, client):
        resp = client.post("/api/v1/sandbox/users-data/teams/2/members", json={"user_id": 4})
        assert resp.status_code == 409


class TestBrokenAPI:
    def test_typo_param_ignored(self, client):
        resp = client.get("/api/v1/sandbox/broken/items?staus=active")
        data = resp.json()
        assert data["total"] == 20  # no filtering happened

    def test_correct_param_filters(self, client):
        resp = client.get("/api/v1/sandbox/broken/items?status=active")
        data = resp.json()
        assert all(i["status"] == "active" for i in data["data"])

    def test_wrong_method(self, client):
        resp = client.post("/api/v1/sandbox/broken/items/42")
        assert resp.status_code == 405

    def test_put_works(self, client):
        resp = client.put("/api/v1/sandbox/broken/items/1", json={"name": "Updated", "status": "active"})
        assert resp.status_code == 200

    def test_missing_required_fields(self, client):
        resp = client.post("/api/v1/sandbox/broken/orders", json={"product": "W"})
        assert resp.status_code == 422

    def test_complete_order(self, client):
        resp = client.post("/api/v1/sandbox/broken/orders", json={"product": "W", "quantity": 1, "shipping_address": "123 St"})
        assert resp.status_code == 200

    def test_api_versions(self, client):
        v1 = client.get("/api/v1/sandbox/broken/v1/products/1").json()
        v2 = client.get("/api/v1/sandbox/broken/v2/products/1").json()
        assert "description" not in v1
        assert "description" in v2

    def test_heavy_data_timeout(self, client):
        resp = client.get("/api/v1/sandbox/broken/heavy-data")
        assert resp.status_code == 504

    def test_heavy_data_with_limit(self, client):
        resp = client.get("/api/v1/sandbox/broken/heavy-data?limit=50")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 50

    def test_document_etag(self, client):
        resp = client.get("/api/v1/sandbox/broken/documents/1")
        assert "etag" in resp.headers

    def test_chain(self, client):
        # Step 1
        s1 = client.get("/api/v1/sandbox/broken/step1").json()
        assert "token" in s1
        # Step 2
        s2 = client.get(f"/api/v1/sandbox/broken/step2?token={s1['token']}").json()
        assert "id" in s2
        # Step 3
        s3 = client.get(f"/api/v1/sandbox/broken/step3/{s2['id']}").json()
        assert "answer" in s3


class TestAdvancedAPI:
    def test_expensive_data_etag(self, client):
        resp = client.get("/api/v1/sandbox/advanced/expensive-data")
        assert resp.status_code == 200
        assert "etag" in resp.headers

    def test_expensive_data_304(self, client):
        resp = client.get("/api/v1/sandbox/advanced/expensive-data")
        etag = resp.headers["etag"]
        resp2 = client.get("/api/v1/sandbox/advanced/expensive-data", headers={"If-None-Match": etag})
        assert resp2.status_code == 304

    def test_batch_create(self, client):
        resp = client.post("/api/v1/sandbox/advanced/items/batch", json={"items": [{"name": "A"}, {"name": "B"}]})
        assert resp.status_code == 200
        assert resp.json()["created"] == 2

    def test_batch_over_limit(self, client):
        items = [{"name": f"Item {i}"} for i in range(101)]
        resp = client.post("/api/v1/sandbox/advanced/items/batch", json={"items": items})
        assert resp.status_code == 400

    def test_async_report(self, client):
        resp = client.post("/api/v1/sandbox/advanced/reports", json={"type": "sales", "period": "Q1"})
        assert resp.status_code == 202
        report_id = resp.json()["report_id"]
        status = client.get(f"/api/v1/sandbox/advanced/reports/{report_id}/status")
        assert status.json()["status"] in ("pending", "processing", "complete")

    def test_idempotent_payment(self, client):
        pay1 = client.post(
            "/api/v1/sandbox/advanced/payments",
            json={"amount": 99.99, "currency": "USD"},
            headers={"Idempotency-Key": "test-key-123"},
        )
        pay2 = client.post(
            "/api/v1/sandbox/advanced/payments",
            json={"amount": 99.99, "currency": "USD"},
            headers={"Idempotency-Key": "test-key-123"},
        )
        assert pay1.json()["id"] == pay2.json()["id"]

    def test_payment_no_idempotency_key(self, client):
        pay1 = client.post("/api/v1/sandbox/advanced/payments", json={"amount": 10.0, "currency": "EUR"})
        pay2 = client.post("/api/v1/sandbox/advanced/payments", json={"amount": 10.0, "currency": "EUR"})
        assert pay1.json()["id"] != pay2.json()["id"]

    def test_webhook_flow(self, client):
        # Register
        client.post("/api/v1/sandbox/advanced/webhooks/register", json={
            "url": "/api/v1/sandbox/advanced/webhooks/echo",
            "events": ["order.created"],
        })
        # Create order triggers webhook
        client.post("/api/v1/sandbox/advanced/orders", json={"product": "Widget"})
        # Check received
        resp = client.get("/api/v1/sandbox/advanced/webhooks/echo/received")
        assert len(resp.json()["received"]) >= 1

    def test_flaky_service(self, client):
        # Call twice — one should succeed, one should fail
        results = [client.get("/api/v1/sandbox/advanced/flaky-service").status_code for _ in range(2)]
        assert 200 in results
        assert 503 in results
