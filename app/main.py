from fastapi import FastAPI

from app.routers import auth, root

app = FastAPI(
    title="API Quest",
    description="A gamified API learning platform. No frontend — learn APIs by using one.",
    version="1.0.0",
)

app.include_router(root.router)
app.include_router(auth.router)
