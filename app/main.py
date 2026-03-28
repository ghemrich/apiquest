import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
