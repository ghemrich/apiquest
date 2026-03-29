"""Mock Broken API — Track 5: Error Detective."""

import copy
import hashlib

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi import Request as _Request

from app.sandbox import state

router = APIRouter(prefix="/api/v1/sandbox/broken", tags=["Sandbox: Broken"])

# --- Read-only constants (shared safely) ---
_products_v1 = {1: {"id": 1, "name": "Widget Pro", "price": 29.99}}
_products_v2 = {1: {"id": 1, "name": "Widget Pro", "price": 29.99, "description": "Premium widget", "category": "electronics"}}

_CHAIN_TOKEN = "quest-chain-token"
_CHAIN_ID = "chain-42"
_CHAIN_ANSWER = "api-quest-complete"

# --- Mutable seed templates ---
_ITEMS = [
    {"id": i, "name": f"Item {i}", "status": "active" if i % 2 else "inactive"}
    for i in range(1, 21)
]

_DOCUMENTS = {
    1: {"id": 1, "title": "Original Document", "content": "Initial content"},
}
_ETAGS = {
    1: hashlib.md5(b"Original Document:Initial content").hexdigest(),
}


def _seed():
    return {
        "items": copy.deepcopy(_ITEMS),
        "orders": [],
        "next_order_id": 1,
        "documents": copy.deepcopy(_DOCUMENTS),
        "etags": dict(_ETAGS),
    }


state.register("broken", _seed)


@router.get("/step1")
def chain_step1():
    return {
        "token": _CHAIN_TOKEN,
        "next": "GET /api/v1/sandbox/broken/step2?token=quest-chain-token",
        "message": "Use this token in step2",
    }


@router.get("/step2")
def chain_step2(token: str = Query(default="")):
    if token != _CHAIN_TOKEN:
        raise HTTPException(status_code=400, detail="Invalid or missing token. Start at GET /step1")
    return {
        "id": _CHAIN_ID,
        "next": f"GET /api/v1/sandbox/broken/step3/{_CHAIN_ID}",
        "message": "Use this id in step3",
    }


@router.get("/step3/{chain_id}")
def chain_step3(chain_id: str):
    if chain_id != _CHAIN_ID:
        raise HTTPException(status_code=404, detail="Invalid id. Start at GET /step1")
    return {
        "answer": _CHAIN_ANSWER,
        "next": "POST /api/v1/sandbox/broken/chain-complete",
        "message": "Chain complete! Submit this answer to /chain-complete",
    }


@router.post("/chain-complete")
def chain_complete(body: dict | None = None):
    if not body or "answer" not in body:
        raise HTTPException(
            status_code=400,
            detail='Submit {"answer": "<value>"} — get the answer by following the chain from /step1',
        )
    if body["answer"] == _CHAIN_ANSWER:
        return {"correct": True, "message": "You followed the entire chain!"}
    return {
        "correct": False,
        "message": "Wrong answer. Follow the chain: GET /step1 → /step2?token=X → /step3/{id}",
    }


@router.get("/items")
def list_items(
    request: Request,
    status: str | None = None,
    staus: str | None = None,  # deliberate typo — silently ignored
):
    s = state.get("broken", request)
    result = list(s["items"])
    # Only the correctly-spelled "status" filters
    if status:
        result = [i for i in result if i["status"] == status]
    # staus is intentionally ignored (the bug users must discover)
    return {"data": result, "total": len(result)}


@router.post("/items/{item_id}")
def post_item_not_allowed(item_id: int):
    raise HTTPException(status_code=405, detail="Method Not Allowed. Use PUT to update.")


@router.put("/items/{item_id}")
def update_item(item_id: int, request: Request, body: dict | None = None):
    s = state.get("broken", request)
    item = next((i for i in s["items"] if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not body or "name" not in body or "status" not in body:
        raise HTTPException(status_code=400, detail="name and status are required")
    item["name"] = body["name"]
    item["status"] = body["status"]
    return item


@router.post("/orders")
def create_order(request: Request, body: dict | None = None):
    s = state.get("broken", request)
    if not body:
        raise HTTPException(status_code=400, detail="Request body required")
    errors = []
    for field in ("product", "quantity", "shipping_address"):
        if field not in body:
            errors.append({"field": field, "message": "This field is required"})
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    order = {"id": s["next_order_id"], **body}
    s["next_order_id"] += 1
    s["orders"].append(order)
    return order


@router.get("/search")
def search(q: str = Query(default="")):
    # The query comes URL-decoded by FastAPI, so this always works
    # if the client properly encodes. If they send literal un-encoded
    # spaces the request itself would be malformed at HTTP level.
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    return {"query": q, "results": [{"id": 1, "title": f"Result for '{q}'"}]}


@router.get("/v1/products/{product_id}")
def get_product_v1(product_id: int):
    product = _products_v1.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    result = dict(product)
    result["_notice"] = "This is API v1 (deprecated). Use /v2/products/ for additional fields."
    return result


@router.get("/v2/products/{product_id}")
def get_product_v2(product_id: int):
    product = _products_v2.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/heavy-data")
def heavy_data(limit: int | None = None):
    if limit is None or limit > 100:
        raise HTTPException(status_code=504, detail="Gateway Timeout — request too large. Try adding a limit parameter (max 100).")
    data = [{"id": i, "value": f"row_{i}"} for i in range(1, limit + 1)]
    return {"data": data, "total": limit}


@router.get("/documents/{doc_id}")
def get_document(request: Request, doc_id: int, response: Response):
    s = state.get("broken", request)
    doc = s["documents"].get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    etag = s["etags"].get(doc_id, "")
    response.headers["ETag"] = f'"{etag}"'
    return doc


@router.put("/documents/{doc_id}")
def update_document(doc_id: int, request: _Request, body: dict | None = None, response: Response = None):
    s = state.get("broken", request)
    doc = s["documents"].get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if_match = request.headers.get("if-match", "").strip('"')
    current_etag = s["etags"].get(doc_id, "")
    if if_match and if_match != current_etag:
        raise HTTPException(status_code=412, detail="Precondition Failed — ETag mismatch")
    if not body:
        raise HTTPException(status_code=400, detail="Request body required")
    if "title" in body:
        doc["title"] = body["title"]
    if "content" in body:
        doc["content"] = body["content"]
    new_etag = hashlib.md5(f"{doc['title']}:{doc['content']}".encode()).hexdigest()
    s["etags"][doc_id] = new_etag
    response.headers["ETag"] = f'"{new_etag}"'
    return doc


