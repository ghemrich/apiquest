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


@router.post("/content-type-mystery")
async def content_type_mystery(request: Request):
    """Challenge endpoint: player must POST a book with the correct Content-Type."""
    content_type = request.headers.get("content-type", "")

    if not content_type:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "No Content-Type header detected",
                "content_type_received": None,
                "hint": "The server needs to know what format your data is in. "
                        "Add a Content-Type header to your request.",
            },
        )

    if "application/json" not in content_type:
        raise HTTPException(
            status_code=415,
            detail={
                "error": f"Unsupported Media Type: {content_type}",
                "content_type_received": content_type,
                "hint": "The server only understands JSON. "
                        "What Content-Type value represents JSON data?",
            },
        )

    # Content-Type is correct — now validate the body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    missing = [f for f in ("title", "author") if not body.get(f)]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing)}",
        )

    return {
        "message": "Book accepted!",
        "book": {
            "title": body["title"],
            "author": body["author"],
            "year": body.get("year"),
        },
        "content_type_received": content_type,
        "lesson": "The Content-Type header tells the server how to interpret "
                  "your request body. For JSON data, use application/json.",
    }


@router.post("/status-check")
def status_check(body: dict | None = None):
    if not body or "codes" not in body:
        raise HTTPException(status_code=400, detail="codes array required")
    codes = body["codes"]
    if not isinstance(codes, list) or len(codes) != 3:
        raise HTTPException(status_code=400, detail="codes must be an array of exactly 3 status codes")

    scenarios = [
        {"scenario": "Requesting a book that doesn't exist", "expected": 404},
        {"scenario": "Sending an invalid request body", "expected": 400},
        {"scenario": "Using PATCH on /books/1", "expected": 405},
    ]
    results = []
    all_correct = True
    for i, scenario in enumerate(scenarios):
        correct = codes[i] == scenario["expected"] if i < len(codes) else False
        if not correct:
            all_correct = False
        results.append({
            "scenario": scenario["scenario"],
            "your_answer": codes[i] if i < len(codes) else None,
            "correct": correct,
            "hint": "Try it yourself and check the status code" if not correct else "Correct!",
        })
    return {"all_correct": all_correct, "results": results}
