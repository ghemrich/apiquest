import os

import pytest
from fastapi.testclient import TestClient

# Disable Kafka in tests
os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "")
# Disable Redis caching in tests (prevents stale leaderboard cache across tests)
os.environ["REDIS_URL"] = "redis://localhost:63999/0"
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — ensure all models are loaded for relationship resolution
from app.database import Base
from app.dependencies import get_db
from app.main import app as fastapi_app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Register a user and return the response data."""
    resp = client.post("/api/v1/auth/register", json={
        "username": "testplayer",
        "password": "securepass123",
    })
    return resp.json()


@pytest.fixture
def auth_header(registered_user):
    """Return an Authorization header dict for the registered user."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
def sample_track(db):
    """Create a beginner track with one challenge."""
    from app.models.challenge import Challenge, Difficulty, Track

    track = Track(
        title="REST Fundamentals",
        description="Learn GET, POST, PUT, DELETE.",
        difficulty=Difficulty.beginner,
        order_index=1,
    )
    db.add(track)
    db.commit()
    db.refresh(track)

    challenge = Challenge(
        track_id=track.id,
        title="Hello, API",
        description="Find the welcome endpoint.\nThe API base URL is /api/v1/sandbox/books",
        difficulty=Difficulty.beginner,
        points_value=50,
        expected_method="GET",
        expected_path="/api/v1/sandbox/books/",
        expected_headers=None,
        expected_query_params=None,
        expected_body=None,
        clues=["The sandbox has a books collection waiting to be explored.", "What HTTP method is used to read data?", "Try the base URL for the books sandbox."],
        hints=["What's the simplest HTTP request?", "Try GET on the base URL.", "GET /api/v1/sandbox/books/", "Send: GET /api/v1/sandbox/books/", "Full answer explanation."],
        order_index=1,
        sandbox_endpoint="/api/v1/sandbox/books",
    )
    db.add(challenge)

    challenge2 = Challenge(
        track_id=track.id,
        title="The Library",
        description="Retrieve all books.",
        difficulty=Difficulty.beginner,
        points_value=50,
        expected_method="GET",
        expected_path="/api/v1/sandbox/books",
        expected_headers=None,
        expected_query_params=None,
        expected_body=None,
        clues=["REST APIs use plural nouns for collections.", "No parameters needed for a full listing."],
        hints=["Collections use plural nouns.", "GET /api/v1/sandbox/books"],
        order_index=2,
        sandbox_endpoint="/api/v1/sandbox/books",
    )
    db.add(challenge2)
    db.commit()
    db.refresh(challenge)
    db.refresh(challenge2)

    return {"track": track, "challenge": challenge, "challenge2": challenge2}
