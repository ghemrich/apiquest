from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_correct: bool
    feedback: str
    method_match: bool
    path_match: bool
    headers_match: bool
    query_params_match: bool
    body_match: bool


def _normalize_path(path: str) -> str:
    return path.rstrip("/").lower()


def _check_method(submitted: str, expected: str) -> bool:
    return submitted.strip().upper() == expected.strip().upper()


def _check_path(submitted: str, expected: str) -> bool:
    return _normalize_path(submitted) == _normalize_path(expected)


def _check_headers(submitted: dict | None, expected: dict | None) -> bool:
    if not expected:
        return True
    if not submitted:
        return False
    submitted_lower = {k.lower(): v for k, v in submitted.items()}
    for key, value in expected.items():
        if submitted_lower.get(key.lower()) != value:
            return False
    return True


def _check_query_params(submitted: dict | None, expected: dict | None) -> bool:
    if not expected:
        return True
    if not submitted:
        return False
    for key, value in expected.items():
        if str(submitted.get(key, "")) != str(value):
            return False
    return True


def _deep_compare(submitted, expected) -> bool:
    if isinstance(expected, dict):
        if not isinstance(submitted, dict):
            return False
        for key in expected:
            if key not in submitted:
                return False
            if not _deep_compare(submitted[key], expected[key]):
                return False
        return True
    if isinstance(expected, list):
        if not isinstance(submitted, list):
            return False
        if len(submitted) != len(expected):
            return False
        return all(_deep_compare(s, e) for s, e in zip(submitted, expected))
    # Scalar comparison — type-aware but flexible with int/float
    if isinstance(expected, (int, float)) and isinstance(submitted, (int, float)):
        return float(submitted) == float(expected)
    return submitted == expected


def _check_body(submitted, expected) -> bool:
    if expected is None:
        return True
    if submitted is None:
        return False
    return _deep_compare(submitted, expected)


def _generate_feedback(
    method_match: bool,
    path_match: bool,
    headers_match: bool,
    query_params_match: bool,
    body_match: bool,
) -> str:
    if method_match and path_match and headers_match and query_params_match and body_match:
        return "Correct! Challenge solved!"

    wrong_count = sum(
        1 for m in [method_match, path_match, headers_match, query_params_match, body_match] if not m
    )

    if wrong_count >= 3:
        return "Let's start with the basics — which HTTP method and endpoint should you use?"

    if not method_match:
        return "Check your HTTP method. Is this a read or write operation?"

    if not path_match:
        return "Right method! But the endpoint path isn't quite right."

    if not query_params_match:
        return "Right method and path! But your query parameters need adjustment."

    if not headers_match:
        return "Almost there! The server needs additional information in your request headers."

    if not body_match:
        return "Your request body doesn't match what the server expects. Check field names and types."

    return "Something isn't quite right. Review your request and try again."


def validate_submission(
    submitted_method: str,
    submitted_path: str,
    submitted_headers: dict | None,
    submitted_query_params: dict | None,
    submitted_body: dict | list | None,
    expected_method: str,
    expected_path: str,
    expected_headers: dict | None,
    expected_query_params: dict | None,
    expected_body: dict | list | None,
) -> ValidationResult:
    method_match = _check_method(submitted_method, expected_method)
    path_match = _check_path(submitted_path, expected_path)
    headers_match = _check_headers(submitted_headers, expected_headers)
    query_params_match = _check_query_params(submitted_query_params, expected_query_params)
    body_match = _check_body(submitted_body, expected_body)

    is_correct = all([method_match, path_match, headers_match, query_params_match, body_match])
    feedback = _generate_feedback(method_match, path_match, headers_match, query_params_match, body_match)

    return ValidationResult(
        is_correct=is_correct,
        feedback=feedback,
        method_match=method_match,
        path_match=path_match,
        headers_match=headers_match,
        query_params_match=query_params_match,
        body_match=body_match,
    )
