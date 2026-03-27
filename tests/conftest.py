import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import get_db
from app.main import app as fastapi_app
import app.models  # noqa: F401 — ensure all models are loaded for relationship resolution

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
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
        "email": "test@example.com",
        "password": "securepass123",
    })
    return resp.json()


@pytest.fixture
def auth_header(registered_user):
    """Return an Authorization header dict for the registered user."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}
