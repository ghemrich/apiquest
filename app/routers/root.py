from fastapi import APIRouter

router = APIRouter(tags=["Root"])


@router.get("/api/v1/")
def welcome():
    return {
        "welcome": "Welcome to API Quest!",
        "description": "API Quest is a gamified API learning platform. Everything happens through API calls — there is no frontend.",
        "getting_started": {
            "step_1": "Register an account: POST /api/v1/auth/register with {\"username\": \"your_name\", \"email\": \"you@example.com\", \"password\": \"your_password\"}",
            "step_2": "Login to get your token: POST /api/v1/auth/login with {\"email\": \"you@example.com\", \"password\": \"your_password\"}",
            "step_3": "Use your token: Add header 'Authorization: Bearer <your_token>' to all requests",
            "step_4": "View available tracks: GET /api/v1/tracks",
            "step_5": "Start solving challenges and earn points!",
        },
        "documentation": "/docs",
        "tools": "Use HTTPie, Postman, curl, or any HTTP client to interact with this API.",
    }
