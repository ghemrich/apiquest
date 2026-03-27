from app.services.validation_engine import validate_submission


class TestMethodMatching:
    def test_exact_match(self):
        r = validate_submission("GET", "/path", None, None, None, "GET", "/path", None, None, None)
        assert r.method_match is True

    def test_case_insensitive(self):
        r = validate_submission("get", "/path", None, None, None, "GET", "/path", None, None, None)
        assert r.method_match is True

    def test_mismatch(self):
        r = validate_submission("POST", "/path", None, None, None, "GET", "/path", None, None, None)
        assert r.method_match is False
        assert "HTTP method" in r.feedback

    def test_whitespace_stripped(self):
        r = validate_submission(" GET ", "/path", None, None, None, "GET", "/path", None, None, None)
        assert r.method_match is True


class TestPathMatching:
    def test_exact_match(self):
        r = validate_submission("GET", "/api/v1/books", None, None, None, "GET", "/api/v1/books", None, None, None)
        assert r.path_match is True

    def test_trailing_slash_normalized(self):
        r = validate_submission("GET", "/api/v1/books/", None, None, None, "GET", "/api/v1/books", None, None, None)
        assert r.path_match is True

    def test_case_insensitive(self):
        r = validate_submission("GET", "/API/V1/Books", None, None, None, "GET", "/api/v1/books", None, None, None)
        assert r.path_match is True

    def test_mismatch(self):
        r = validate_submission("GET", "/api/v1/tasks", None, None, None, "GET", "/api/v1/books", None, None, None)
        assert r.path_match is False
        assert "endpoint path" in r.feedback


class TestHeaderMatching:
    def test_no_expected_headers(self):
        r = validate_submission("GET", "/p", None, None, None, "GET", "/p", None, None, None)
        assert r.headers_match is True

    def test_matching_headers(self):
        r = validate_submission(
            "POST", "/p", {"Content-Type": "application/json"}, None, None,
            "POST", "/p", {"Content-Type": "application/json"}, None, None,
        )
        assert r.headers_match is True

    def test_case_insensitive_keys(self):
        r = validate_submission(
            "POST", "/p", {"content-type": "application/json"}, None, None,
            "POST", "/p", {"Content-Type": "application/json"}, None, None,
        )
        assert r.headers_match is True

    def test_missing_required_header(self):
        r = validate_submission(
            "POST", "/p", None, None, None,
            "POST", "/p", {"Content-Type": "application/json"}, None, None,
        )
        assert r.headers_match is False
        assert "headers" in r.feedback.lower()

    def test_extra_headers_ok(self):
        r = validate_submission(
            "POST", "/p", {"Content-Type": "application/json", "X-Custom": "val"}, None, None,
            "POST", "/p", {"Content-Type": "application/json"}, None, None,
        )
        assert r.headers_match is True


class TestQueryParamMatching:
    def test_no_expected_params(self):
        r = validate_submission("GET", "/p", None, None, None, "GET", "/p", None, None, None)
        assert r.query_params_match is True

    def test_matching_params(self):
        r = validate_submission(
            "GET", "/p", None, {"status": "active"}, None,
            "GET", "/p", None, {"status": "active"}, None,
        )
        assert r.query_params_match is True

    def test_missing_param(self):
        r = validate_submission(
            "GET", "/p", None, None, None,
            "GET", "/p", None, {"status": "active"}, None,
        )
        assert r.query_params_match is False

    def test_wrong_value(self):
        r = validate_submission(
            "GET", "/p", None, {"status": "pending"}, None,
            "GET", "/p", None, {"status": "active"}, None,
        )
        assert r.query_params_match is False

    def test_numeric_string_coercion(self):
        r = validate_submission(
            "GET", "/p", None, {"page": "3"}, None,
            "GET", "/p", None, {"page": 3}, None,
        )
        assert r.query_params_match is True


class TestBodyMatching:
    def test_no_expected_body(self):
        r = validate_submission("GET", "/p", None, None, None, "GET", "/p", None, None, None)
        assert r.body_match is True

    def test_matching_body(self):
        body = {"title": "Test", "author": "Author"}
        r = validate_submission("POST", "/p", None, None, body, "POST", "/p", None, None, body)
        assert r.body_match is True

    def test_key_order_independent(self):
        sub = {"author": "Author", "title": "Test"}
        exp = {"title": "Test", "author": "Author"}
        r = validate_submission("POST", "/p", None, None, sub, "POST", "/p", None, None, exp)
        assert r.body_match is True

    def test_missing_field(self):
        sub = {"title": "Test"}
        exp = {"title": "Test", "author": "Author"}
        r = validate_submission("POST", "/p", None, None, sub, "POST", "/p", None, None, exp)
        assert r.body_match is False
        assert "body" in r.feedback.lower()

    def test_wrong_value(self):
        sub = {"title": "Wrong", "author": "Author"}
        exp = {"title": "Test", "author": "Author"}
        r = validate_submission("POST", "/p", None, None, sub, "POST", "/p", None, None, exp)
        assert r.body_match is False

    def test_nested_body(self):
        body = {"data": {"name": "test", "items": [1, 2, 3]}}
        r = validate_submission("POST", "/p", None, None, body, "POST", "/p", None, None, body)
        assert r.body_match is True

    def test_nested_mismatch(self):
        sub = {"data": {"name": "test", "items": [1, 2]}}
        exp = {"data": {"name": "test", "items": [1, 2, 3]}}
        r = validate_submission("POST", "/p", None, None, sub, "POST", "/p", None, None, exp)
        assert r.body_match is False

    def test_int_float_equivalence(self):
        sub = {"amount": 99.0}
        exp = {"amount": 99}
        r = validate_submission("POST", "/p", None, None, sub, "POST", "/p", None, None, exp)
        assert r.body_match is True

    def test_none_submitted_when_expected(self):
        exp = {"title": "Test"}
        r = validate_submission("POST", "/p", None, None, None, "POST", "/p", None, None, exp)
        assert r.body_match is False

    def test_list_body(self):
        body = [{"id": 1}, {"id": 2}]
        r = validate_submission("POST", "/p", None, None, body, "POST", "/p", None, None, body)
        assert r.body_match is True


class TestFeedback:
    def test_all_correct(self):
        r = validate_submission("GET", "/p", None, None, None, "GET", "/p", None, None, None)
        assert r.is_correct is True
        assert r.feedback == "Correct! Challenge solved!"

    def test_multiple_wrong_gives_basics_feedback(self):
        r = validate_submission(
            "POST", "/wrong", {"Bad": "header"}, None, {"bad": "body"},
            "GET", "/correct", {"Good": "header"}, None, {"good": "body"},
        )
        assert r.is_correct is False
        assert "basics" in r.feedback.lower()

    def test_method_wrong_feedback(self):
        r = validate_submission("POST", "/p", None, None, None, "GET", "/p", None, None, None)
        assert "HTTP method" in r.feedback

    def test_path_wrong_method_right(self):
        r = validate_submission("GET", "/wrong", None, None, None, "GET", "/right", None, None, None)
        assert "Right method" in r.feedback

    def test_headers_wrong_feedback(self):
        r = validate_submission(
            "POST", "/p", None, None, None,
            "POST", "/p", {"Content-Type": "application/json"}, None, None,
        )
        assert "headers" in r.feedback.lower()

    def test_body_wrong_feedback(self):
        r = validate_submission(
            "POST", "/p", None, None, {"wrong": True},
            "POST", "/p", None, None, {"right": True},
        )
        assert "body" in r.feedback.lower()

    def test_query_params_wrong_feedback(self):
        r = validate_submission(
            "GET", "/p", None, {"status": "wrong"}, None,
            "GET", "/p", None, {"status": "active"}, None,
        )
        assert "query parameters" in r.feedback.lower()


class TestFullChallenge:
    def test_rest_fundamentals_hello_api(self):
        """Challenge 1.1: GET the welcome endpoint."""
        r = validate_submission(
            "GET", "/api/v1/sandbox/books/", None, None, None,
            "GET", "/api/v1/sandbox/books/", None, None, None,
        )
        assert r.is_correct is True

    def test_rest_fundamentals_create_book(self):
        """Challenge 1.4: POST a new book with Content-Type."""
        r = validate_submission(
            "POST", "/api/v1/sandbox/books",
            {"Content-Type": "application/json"}, None,
            {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008},
            "POST", "/api/v1/sandbox/books",
            {"Content-Type": "application/json"}, None,
            {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008},
        )
        assert r.is_correct is True

    def test_query_mastery_filter(self):
        """Challenge 2.1: Filter tasks by status."""
        r = validate_submission(
            "GET", "/api/v1/sandbox/tasks", None, {"status": "completed"}, None,
            "GET", "/api/v1/sandbox/tasks", None, {"status": "completed"}, None,
        )
        assert r.is_correct is True

    def test_wrong_method_on_create(self):
        """User tries GET instead of POST to create."""
        r = validate_submission(
            "GET", "/api/v1/sandbox/books",
            {"Content-Type": "application/json"}, None,
            {"title": "Test"},
            "POST", "/api/v1/sandbox/books",
            {"Content-Type": "application/json"}, None,
            {"title": "Test"},
        )
        assert r.is_correct is False
        assert r.method_match is False
        assert r.path_match is True
