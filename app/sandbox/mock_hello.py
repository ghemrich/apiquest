"""Mock Hello API — The very first endpoint a player hits."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/sandbox/hello", tags=["Sandbox: Hello"])


@router.get("/")
def hello():
    return {"message": "Hello from API Quest!", "hint": "You just made your first GET request. Well done!"}
