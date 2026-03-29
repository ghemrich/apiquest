"""Mock Users-Data API — Track 4: Data Relationships."""

import copy

from fastapi import APIRouter, HTTPException, Request, status

from app.sandbox import state

router = APIRouter(prefix="/api/v1/sandbox/users-data", tags=["Sandbox: Users Data"])

# --- Seed templates (never mutated) ---
_TEAMS = [
    {"id": 1, "name": "Backend Team", "members": [1, 2, 3]},
    {"id": 2, "name": "Frontend Team", "members": [4, 6]},
    {"id": 3, "name": "DevOps Team", "members": [8, 9]},
]

_USERS = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "role": "developer" if i % 2 else "manager"}
    for i in range(1, 11)
]

_PROJECTS = [
    {"id": 1, "title": "API Quest", "owner_id": 1, "status": "active"},
    {"id": 2, "title": "Dashboard", "owner_id": 1, "status": "active"},
    {"id": 3, "title": "Mobile App", "owner_id": 7, "status": "active"},
    {"id": 4, "title": "Data Pipeline", "owner_id": 3, "status": "completed"},
    {"id": 5, "title": "Auth Service", "owner_id": 5, "status": "active"},
]

_TASKS = [
    {"id": 1, "title": "Setup database", "project_id": 1, "priority": "high", "status": "completed"},
    {"id": 2, "title": "Write API tests", "project_id": 1, "priority": "medium", "status": "pending"},
    {"id": 3, "title": "Design UI mockups", "project_id": 3, "priority": "high", "status": "in_progress"},
    {"id": 4, "title": "Configure CI/CD", "project_id": 4, "priority": "medium", "status": "completed"},
    {"id": 5, "title": "Add OAuth flow", "project_id": 5, "priority": "high", "status": "pending"},
    {"id": 6, "title": "Write unit tests", "project_id": 3, "priority": "medium", "status": "pending"},
    {"id": 7, "title": "Deploy staging", "project_id": 2, "priority": "low", "status": "pending"},
    {"id": 8, "title": "Database migration", "project_id": 1, "priority": "critical", "status": "pending"},
]


def _seed():
    return {
        "teams": copy.deepcopy(_TEAMS),
        "users": copy.deepcopy(_USERS),
        "projects": copy.deepcopy(_PROJECTS),
        "tasks": copy.deepcopy(_TASKS),
        "next_task_id": max(t["id"] for t in _TASKS) + 1,
    }


state.register("users", _seed)


@router.get("/")
def list_users(request: Request):
    s = state.get("users", request)
    return {"data": s["users"]}


@router.get("/{user_id}")
def get_user(request: Request, user_id: int):
    s = state.get("users", request)
    user = next((u for u in s["users"] if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/projects")
def get_user_projects(request: Request, user_id: int):
    s = state.get("users", request)
    user = next((u for u in s["users"] if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": [p for p in s["projects"] if p["owner_id"] == user_id]}


@router.get("/{user_id}/projects/{project_id}/tasks")
def get_project_tasks_nested(request: Request, user_id: int, project_id: int):
    s = state.get("users", request)
    user = next((u for u in s["users"] if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    project = next((p for p in s["projects"] if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": [t for t in s["tasks"] if t["project_id"] == project_id]}


@router.get("/projects/{project_id}")
def get_project(request: Request, project_id: int, include: str | None = None):
    s = state.get("users", request)
    project = next((p for p in s["projects"] if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = dict(project)
    if include and "tasks" in include:
        result["tasks"] = [t for t in s["tasks"] if t["project_id"] == project_id]
    return result


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(request: Request, body: dict | None = None):
    s = state.get("users", request)
    if not body or "title" not in body or "project_id" not in body:
        raise HTTPException(status_code=400, detail="title and project_id are required")
    project = next((p for p in s["projects"] if p["id"] == body["project_id"]), None)
    if not project:
        raise HTTPException(status_code=400, detail="Project does not exist")
    task = {
        "id": s["next_task_id"],
        "title": body["title"],
        "project_id": body["project_id"],
        "priority": body.get("priority", "medium"),
        "status": "pending",
    }
    s["next_task_id"] += 1
    s["tasks"].append(task)
    return task


@router.post("/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
def add_team_member(request: Request, team_id: int, body: dict | None = None):
    s = state.get("users", request)
    team = next((t for t in s["teams"] if t["id"] == team_id), None)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not body or "user_id" not in body:
        raise HTTPException(status_code=400, detail="user_id is required")
    user_id = body["user_id"]
    if user_id in team["members"]:
        raise HTTPException(status_code=409, detail="User is already a member of this team")
    user = next((u for u in s["users"] if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    team["members"].append(user_id)
    return {"team_id": team_id, "user_id": user_id, "added": True}


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(request: Request, project_id: int):
    s = state.get("users", request)
    project = next((p for p in s["projects"] if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Cascade: remove all tasks for this project
    s["tasks"] = [t for t in s["tasks"] if t["project_id"] != project_id]
    s["projects"].remove(project)
