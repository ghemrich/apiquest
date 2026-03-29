import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from jose import jwt as jose_jwt

from app.config import settings
from app.kafka.consumers import (
    register_eventbus_consumers,
    start_kafka_consumers,
    stop_kafka_consumers,
    unregister_eventbus_consumers,
)
from app.kafka.producer import start_kafka_producer, stop_kafka_producer
from app.routers import auth, challenges, leaderboard, root, submissions, tracks, users, websockets
from app.sandbox import (
    mock_advanced,
    mock_auth,
    mock_books,
    mock_broken,
    mock_hello,
    mock_stream,
    mock_tasks,
    mock_users,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for Kafka producer and consumers."""
    # Startup — always register EventBus as fallback
    register_eventbus_consumers()
    await start_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
    from app.kafka.producer import _use_kafka
    if _use_kafka:
        try:
            await start_kafka_consumers()
        except Exception:
            logger.warning("Kafka consumers failed to start")
    else:
        logger.info("Kafka unavailable — using in-process EventBus")
    yield
    # Shutdown
    await stop_kafka_consumers()
    unregister_eventbus_consumers()
    await stop_kafka_producer()


app = FastAPI(
    title="API Quest",
    description="A gamified API learning platform. No frontend — learn APIs by using one.",
    version="1.0.0",
    lifespan=lifespan,
)

# Core routers
app.include_router(root.router)


@app.middleware("http")
async def sandbox_session(request: Request, call_next):
    """Assign a per-session ID from JWT user identity or cookie fallback."""
    if request.url.path.startswith("/api/v1/sandbox"):
        sid = None
        # Try to extract user ID from Bearer token
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            try:
                payload = jose_jwt.decode(
                    auth[7:], settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                )
                sid = payload.get("sub")
            except Exception:
                pass
        # Fall back to cookie
        if not sid:
            sid = request.cookies.get("quest_sandbox")
        # Fall back to client IP (transparent for any HTTP client)
        if not sid:
            sid = f"ip-{request.client.host}" if request.client else None
        new = not sid
        if new:
            sid = uuid.uuid4().hex
        request.state.sandbox_session = sid
        response = await call_next(request)
        if new:
            response.set_cookie(
                "quest_sandbox",
                sid,
                path="/api/v1/sandbox",
                httponly=True,
                samesite="lax",
                max_age=3600,
            )
        return response
    return await call_next(request)


app.include_router(auth.router)
app.include_router(tracks.router)
app.include_router(challenges.router)
app.include_router(submissions.router)
app.include_router(leaderboard.router)
app.include_router(users.router)
app.include_router(websockets.router)

# Sandbox mock APIs
app.include_router(mock_hello.router)
app.include_router(mock_books.router)
app.include_router(mock_tasks.router)
app.include_router(mock_auth.router)
app.include_router(mock_users.router)
app.include_router(mock_broken.router)
app.include_router(mock_stream.router)
app.include_router(mock_advanced.router)
