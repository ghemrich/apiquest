"""Mock Books API — Track 1: REST Fundamentals."""

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.sandbox.seed_data import get_books_store, get_next_id

router = APIRouter(prefix="/api/v1/sandbox/books", tags=["Sandbox: Books"])

# In-memory store — persists across requests within one process run.
_books: list[dict] = get_books_store()


def _find_book(book_id: int) -> dict | None:
    return next((b for b in _books if b["id"] == book_id), None)


@router.get("/")
def list_books(page: int = 1, per_page: int = 10):
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "data": _books[start:end],
        "total": len(_books),
        "page": page,
        "per_page": per_page,
    }


@router.get("/{book_id}")
def get_book(book_id: int):
    book = _find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_book(request: Request, response: Response, body: dict | None = None):
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    if not body or not body.get("title") or not body.get("author"):
        raise HTTPException(status_code=400, detail="title and author are required")
    new_book = {
        "id": get_next_id(),
        "title": body["title"],
        "author": body["author"],
        "year": body.get("year"),
    }
    _books.append(new_book)
    return new_book


@router.put("/{book_id}")
def update_book(book_id: int, request: Request, body: dict | None = None):
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    book = _find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not body or not all(k in body for k in ("title", "author", "year")):
        raise HTTPException(status_code=400, detail="All fields (title, author, year) are required")
    book["title"] = body["title"]
    book["author"] = body["author"]
    book["year"] = body["year"]
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    book = _find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    _books.remove(book)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
def delete_books_collection():
    raise HTTPException(status_code=405, detail="Cannot delete entire collection")


@router.post("/status-check")
def status_check(body: dict | None = None):
    if not body or "codes" not in body:
        raise HTTPException(status_code=400, detail="codes array required")
    return {"valid": True, "codes_acknowledged": body["codes"]}
