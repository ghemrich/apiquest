"""Mock Books API — Track 1: REST Fundamentals."""

import copy

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.sandbox import state
from app.sandbox.seed_data import BOOKS

router = APIRouter(prefix="/api/v1/sandbox/books", tags=["Sandbox: Books"])


def _seed():
    return {
        "books": copy.deepcopy(BOOKS),
        "next_id": max(b["id"] for b in BOOKS) + 1,
    }


state.register("books", _seed)


@router.get("/")
def list_books(request: Request, page: int = 1, per_page: int = 10):
    s = state.get("books", request)
    books = s["books"]
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "data": books[start:end],
        "total": len(books),
        "page": page,
        "per_page": per_page,
    }


@router.get("/{book_id}")
def get_book(request: Request, book_id: int):
    s = state.get("books", request)
    book = next((b for b in s["books"] if b["id"] == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_book(request: Request, response: Response, body: dict | None = None):
    s = state.get("books", request)
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    if not body or not body.get("title") or not body.get("author"):
        raise HTTPException(status_code=400, detail="title and author are required")
    new_book = {
        "id": s["next_id"],
        "title": body["title"],
        "author": body["author"],
        "year": body.get("year"),
    }
    s["next_id"] += 1
    s["books"].append(new_book)
    return new_book


@router.put("/{book_id}")
def update_book(book_id: int, request: Request, body: dict | None = None):
    s = state.get("books", request)
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")
    book = next((b for b in s["books"] if b["id"] == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not body or not all(k in body for k in ("title", "author", "year")):
        raise HTTPException(status_code=400, detail="All fields (title, author, year) are required")
    book["title"] = body["title"]
    book["author"] = body["author"]
    book["year"] = body["year"]
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(request: Request, book_id: int):
    s = state.get("books", request)
    book = next((b for b in s["books"] if b["id"] == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    s["books"].remove(book)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
def delete_books_collection():
    raise HTTPException(status_code=405, detail="Cannot delete entire collection")


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
