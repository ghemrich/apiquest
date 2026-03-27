"""Mock Users-Data API — Track 4: Data Relationships."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/sandbox/users-data", tags=["Sandbox: Users Data"])

# --- Seed data ---
_teams = [
    {"id": 1, "name": "Backend Team", "members": [1, 2, 3]},
    {"id": 2, "name": "Frontend Team", "members": [4, 6]},
    {"id": 3, "name": "DevOps Team", "members": [8, 9]},
]

_users = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "role": "developer" if i % 2 else "manager"}
    for i in range(1, 11)
]

_projects = [
    {"id": 1, "title": "API Quest", "owner_id": 1, "status": "active"},
    {"id": 2, "title": "Dashboard", "owner_id": 1, "status": "active"},
    {"id": 3, "title": "Mobile App", "owner_id": 7, "status": "active"},
    {"id": 4, "title": "Data Pipeline", "owner_id": 3, "status": "completed"},
    {"id": 5, "title": "Auth Service", "owner_id": 5, "status": "active"},
]

_tasks = [
    {"id": 1, "title": "Setup database", "project_id": 1, "priority": "high", "status": "completed"},
    {"id": 2, "title": "Write API tests", "project_id": 1, "priority": "medium", "status": "pending"},
    {"id": 3, "title": "Design UI mockups", "project_id": 3, "priority": "high", "status": "in_progress"},
    {"id": 4, "title": "Configure CI/CD", "project_id": 4, "priority": "medium", "status": "completed"},
    {"id": 5, "title": "Add OAuth flow", "project_id": 5, "priority": "high", "status": "pending"},
    {"id": 6, "title": "Write unit tests", "project_id": 3, "priority": "medium", "status": "pending"},
    {"id": 7, "title": "Deploy staging", "project_id": 2, "priority": "low", "status": "pending"},
    {"id": 8, "title": "Database migration", "project_id": 1, "priority": "critical", "status": "pending"},
]

_next_task_id = max(t["id"] for t in _tasks) + 1


def _get_user(user_id: int) -> dict | None:
    return next((u for u in _users if u["id"] == user_id), None)


def _get_project(project_id: int) -> dict | None:
    return next((p for p in _projects if p["id"] == project_id), None)


def _get_tasks_for_project(project_id: int) -> list[dict]:
    return [t for t in _tasks if t["project_id"] == project_id]


def _get_projects_for_user(user_id: int) -> list[dict]:
    return [p for p in _projects if p["owner_id"] == user_id]


@router.get("/")
def list_users():
    return {"data": _users}


@router.get("/{user_id}")
def get_user(user_id: int):
    user = _get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/projects")
def get_user_projects(user_id: int):
    user = _get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": _get_projects_for_user(user_id)}


@router.get("/{user_id}/projects/{project_id}/tasks")
def get_project_tasks_nested(user_id: int, project_id: int):
    user = _get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    project = _get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": _get_tasks_for_project(project_id)}


@router.get("/projects/{project_id}")
def get_project(project_id: int, include: str | None = None):
    project = _get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = dict(project)
    if include and "tasks" in include:
        result["tasks"] = _get_tasks_for_project(project_id)
    return result


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(body: dict | None = None):
    global _next_task_id
    if not body or "title" not in body or "project_id" not in body:
        raise HTTPException(status_code=400, detail="title and project_id are required")
    project = _get_project(body["project_id"])
    if not project:
        raise HTTPException(status_code=400, detail="Project does not exist")
    task = {
        "id": _next_task_id,
        "title": body["title"],
        "project_id": body["project_id"],
        "priority": body.get("priority", "medium"),
        "status": "pending",
    }
    _next_task_id += 1
    _tasks.append(task)
    return task


@router.post("/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
def add_team_member(team_id: int, body: dict | None = None):
    team = next((t for t in _teams if t["id"] == team_id), None)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not body or "user_id" not in body:
        raise HTTPException(status_code=400, detail="user_id is required")
    user_id = body["user_id"]
    if user_id in team["members"]:
        raise HTTPException(status_code=409, detail="User is already a member of this team")
    user = _get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    team["members"].append(user_id)
    return {"team_id": team_id, "user_id": user_id, "added": True}


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int):
    project = _get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Cascade: remove all tasks for this project
    global _tasks
    _tasks = [t for t in _tasks if t["project_id"] != project_id]
    _projects.remove(project)
