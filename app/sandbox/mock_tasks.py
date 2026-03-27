"""Mock Tasks API — Track 2: Query Mastery."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/sandbox/tasks", tags=["Sandbox: Tasks"])

VALID_FIELDS = {
    "id", "title", "status", "priority", "created_at", "updated_at",
    "description", "assignee", "project", "tags", "due_date",
    "estimated_hours", "actual_hours", "category", "completed_at",
}

# Generate 100 tasks
_STATUSES = ["completed", "pending", "in_progress"]
_PRIORITIES = ["low", "medium", "high", "critical"]
_PROJECTS = ["API Quest", "Dashboard", "Mobile App", "Data Pipeline", "Auth Service"]
_CATEGORIES = ["feature", "bug", "improvement", "documentation", "testing"]

_tasks: list[dict] = []
for i in range(1, 101):
    _tasks.append({
        "id": i,
        "title": f"Task {i}: {'Setup database' if i % 7 == 1 else 'Write API tests' if i % 7 == 2 else 'Implement caching' if i % 7 == 3 else 'Fix search bug' if i % 7 == 4 else 'Deploy service' if i % 7 == 5 else 'Update documentation' if i % 7 == 6 else 'Review pull request'}",
        "status": _STATUSES[i % 3],
        "priority": _PRIORITIES[i % 4],
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat(),
        "updated_at": datetime(2025, 6, 15, tzinfo=timezone.utc).isoformat(),
        "description": f"Description for task {i}",
        "assignee": f"user_{(i % 10) + 1}",
        "project": _PROJECTS[i % 5],
        "tags": ["backend", "api"] if i % 2 == 0 else ["frontend", "ui"],
        "due_date": datetime(2025, 12, 31, tzinfo=timezone.utc).isoformat(),
        "estimated_hours": (i % 8) + 1,
        "actual_hours": max(1, (i % 6)),
        "category": _CATEGORIES[i % 5],
        "completed_at": datetime(2025, 6, 1, tzinfo=timezone.utc).isoformat() if _STATUSES[i % 3] == "completed" else None,
    })


@router.get("/")
def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    fields: str | None = None,
):
    result = list(_tasks)

    # Filter: status
    if status:
        result = [t for t in result if t["status"] == status]

    # Filter: priority
    if priority:
        result = [t for t in result if t["priority"] == priority]

    # Filter: search (case-insensitive partial match on title)
    if search:
        search_lower = search.lower()
        result = [t for t in result if search_lower in t["title"].lower()]

    # Sort
    if sort:
        descending = sort.startswith("-")
        sort_field = sort.lstrip("-")
        if sort_field not in VALID_FIELDS:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_field}")
        result = sorted(result, key=lambda t: (t.get(sort_field) is None, t.get(sort_field)), reverse=descending)

    total = len(result)
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Field selection
    if fields:
        requested = [f.strip() for f in fields.split(",")]
        invalid = [f for f in requested if f not in VALID_FIELDS]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid fields: {', '.join(invalid)}")
        result = [{k: t[k] for k in requested if k in t} for t in result]

    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    result = result[start:end]

    return {
        "data": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
