from fastapi import FastAPI

from app.routers import auth, challenges, leaderboard, root, submissions, tracks
from app.sandbox import mock_advanced, mock_auth, mock_books, mock_broken, mock_stream, mock_tasks, mock_users

app = FastAPI(
    title="API Quest",
    description="A gamified API learning platform. No frontend — learn APIs by using one.",
    version="1.0.0",
)

# Core routers
app.include_router(root.router)
app.include_router(auth.router)
app.include_router(tracks.router)
app.include_router(challenges.router)
app.include_router(submissions.router)
app.include_router(leaderboard.router)

# Sandbox mock APIs
app.include_router(mock_books.router)
app.include_router(mock_tasks.router)
app.include_router(mock_auth.router)
app.include_router(mock_users.router)
app.include_router(mock_broken.router)
app.include_router(mock_stream.router)
app.include_router(mock_advanced.router)
