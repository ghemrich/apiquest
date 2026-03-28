"""Mock Auth API — Track 3: Auth & Security."""

import hashlib
import hmac
import time

from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(prefix="/api/v1/sandbox/mock-auth", tags=["Sandbox: Auth"])

# Credential store
_USERS = {
    "player1": {"password": "quest123", "role": "user", "name": "Player One", "email": "player1@apiquest.dev"},
    "admin1": {"password": "adminquest123", "role": "admin", "name": "Admin User", "email": "admin1@apiquest.dev"},
}

_VALID_API_KEY = "sk_test_abc123xyz"

# Token store: token_string -> {username, role, expires_at, type}
_tokens: dict[str, dict] = {}

# Rate limiter: ip -> {count, window_start}
_rate_limits: dict[str, dict] = {}
_RATE_LIMIT = 5
_RATE_WINDOW = 60  # seconds


def _generate_token(username: str, role: str, token_type: str, ttl: int = 60) -> str:
    raw = f"{username}:{role}:{token_type}:{time.time()}"
    token = hmac.new(b"sandbox-secret", raw.encode(), hashlib.sha256).hexdigest()
    _tokens[token] = {
        "username": username,
        "role": role,
        "type": token_type,
        "expires_at": time.time() + ttl,
    }
    return token


def _validate_bearer(request: Request) -> dict:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token_str = auth[7:]
    token_data = _tokens.get(token_str)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    if time.time() > token_data["expires_at"]:
        del _tokens[token_str]
        raise HTTPException(status_code=401, detail="Token expired")
    return token_data


@router.post("/login")
def login(body: dict | None = None):
    if not body or "username" not in body or "password" not in body:
        raise HTTPException(status_code=400, detail="username and password required")
    username = body["username"]
    password = body["password"]
    user = _USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = _generate_token(username, user["role"], "access", ttl=60)
    refresh_token = _generate_token(username, user["role"], "refresh", ttl=3600)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh(body: dict | None = None):
    if not body or "refresh_token" not in body:
        raise HTTPException(status_code=400, detail="refresh_token required")
    token_data = _tokens.get(body["refresh_token"])
    if not token_data or token_data["type"] != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if time.time() > token_data["expires_at"]:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    # Revoke old tokens
    del _tokens[body["refresh_token"]]
    username = token_data["username"]
    role = token_data["role"]
    access_token = _generate_token(username, role, "access", ttl=60)
    refresh_token = _generate_token(username, role, "refresh", ttl=3600)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/profile")
def get_profile(request: Request):
    token_data = _validate_bearer(request)
    user = _USERS[token_data["username"]]
    return {
        "username": token_data["username"],
        "role": token_data["role"],
        "name": user["name"],
        "email": user["email"],
    }


@router.get("/admin/users")
def admin_users(request: Request):
    token_data = _validate_bearer(request)
    if token_data["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"Admin access required. Your current role is '{token_data['role']}'. "
                   "Check GET /api/v1/sandbox/mock-auth/accounts for available test accounts.",
        )
    return {
        "users": [
            {"username": u, "role": d["role"], "name": d["name"]}
            for u, d in _USERS.items()
        ]
    }


@router.get("/external/data")
def external_data(request: Request):
    api_key = request.headers.get("x-api-key", "")
    if api_key != _VALID_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. This endpoint requires an X-API-Key header. "
                   "Get a test key from GET /api/v1/sandbox/mock-auth/api-keys",
        )
    return {"source": "external", "data": [{"id": 1, "value": "secret-data"}]}


@router.get("/limited")
def rate_limited(request: Request, response: Response):
    token_data = _validate_bearer(request)
    client_id = token_data["username"]
    now = time.time()

    if client_id not in _rate_limits or now - _rate_limits[client_id]["window_start"] > _RATE_WINDOW:
        _rate_limits[client_id] = {"count": 0, "window_start": now}

    rl = _rate_limits[client_id]
    rl["count"] += 1
    remaining = max(0, _RATE_LIMIT - rl["count"])
    retry_after = int(rl["window_start"] + _RATE_WINDOW - now)

    response.headers["X-RateLimit-Limit"] = str(_RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["Retry-After"] = str(max(0, retry_after))

    if rl["count"] > _RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(_RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(max(0, retry_after)),
            },
        )
    return {"message": "Success", "requests_remaining": remaining}


@router.get("/api-keys")
def get_api_keys():
    """Returns a test API key for the /external/data endpoint."""
    return {
        "api_key": _VALID_API_KEY,
        "header": "X-API-Key",
        "usage": "Add this header to requests: X-API-Key: sk_test_abc123xyz",
    }


@router.get("/accounts")
def list_accounts():
    """Lists available test accounts (no passwords — those are for you to discover)."""
    return {
        "accounts": [
            {"username": u, "role": d["role"], "hint": "Password follows a pattern based on the role"}
            for u, d in _USERS.items()
        ]
    }


@router.post("/rate-limit-report")
def rate_limit_report(body: dict | None = None):
    """Validate that the player correctly identified the rate limit parameters."""
    if not body or "limit" not in body or "window_seconds" not in body:
        raise HTTPException(
            status_code=400,
            detail="Submit {\"limit\": <number>, \"window_seconds\": <number>} "
                   "based on the headers you observed from GET /limited",
        )
    results = []
    all_correct = True
    if body["limit"] == _RATE_LIMIT:
        results.append({"field": "limit", "correct": True, "hint": "Correct!"})
    else:
        all_correct = False
        results.append({"field": "limit", "correct": False, "hint": "Check X-RateLimit-Limit header"})
    if body["window_seconds"] == _RATE_WINDOW:
        results.append({"field": "window_seconds", "correct": True, "hint": "Correct!"})
    else:
        all_correct = False
        results.append({"field": "window_seconds", "correct": False, "hint": "Check the Retry-After header on your first request"})
    return {"all_correct": all_correct, "results": results}


@router.options("/cors-test")
def cors_test(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return {"cors": "enabled"}


@router.post("/users")
def create_user(body: dict | None = None):
    if not body or "name" not in body:
        raise HTTPException(status_code=400, detail="name is required")
    name = body["name"]
    # Reject HTML/script tags
    if "<" in name or ">" in name:
        raise HTTPException(status_code=400, detail="Input contains invalid characters")
    return {"id": 99, "name": name, "created": True}
