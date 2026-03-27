"""Mock Broken API — Track 5: Error Detective."""

import hashlib
import time
import uuid as uuid_mod

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi import Request as _Request

router = APIRouter(prefix="/api/v1/sandbox/broken", tags=["Sandbox: Broken"])

# --- In-memory data ---
_items = [
    {"id": i, "name": f"Item {i}", "status": "active" if i % 2 else "inactive"}
    for i in range(1, 21)
]

_orders: list[dict] = []
_next_order_id = 1

_products_v1 = {1: {"id": 1, "name": "Widget Pro", "price": 29.99}}
_products_v2 = {1: {"id": 1, "name": "Widget Pro", "price": 29.99, "description": "Premium widget", "category": "electronics"}}

# Documents with ETags
_documents = {
    1: {"id": 1, "title": "Original Document", "content": "Initial content"},
}
_etags: dict[int, str] = {}
_etags[1] = hashlib.md5(b"Original Document:Initial content").hexdigest()

# Multi-step chain
_chain_tokens: dict[str, dict] = {}  # token -> {id, expires_at}
_chain_ids: dict[str, str] = {}  # id -> answer


@router.get("/items")
def list_items(
    status: str | None = None,
    staus: str | None = None,  # deliberate typo — silently ignored
):
    result = list(_items)
    # Only the correctly-spelled "status" filters
    if status:
        result = [i for i in result if i["status"] == status]
    # staus is intentionally ignored (the bug users must discover)
    return {"data": result, "total": len(result)}


@router.post("/items/{item_id}")
def post_item_not_allowed(item_id: int):
    raise HTTPException(status_code=405, detail="Method Not Allowed. Use PUT to update.")


@router.put("/items/{item_id}")
def update_item(item_id: int, body: dict | None = None):
    item = next((i for i in _items if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not body or "name" not in body or "status" not in body:
        raise HTTPException(status_code=400, detail="name and status are required")
    item["name"] = body["name"]
    item["status"] = body["status"]
    return item


@router.post("/orders")
def create_order(body: dict | None = None):
    global _next_order_id
    if not body:
        raise HTTPException(status_code=400, detail="Request body required")
    errors = []
    for field in ("product", "quantity", "shipping_address"):
        if field not in body:
            errors.append({"field": field, "message": "This field is required"})
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    order = {"id": _next_order_id, **body}
    _next_order_id += 1
    _orders.append(order)
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
    return product


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
def get_document(doc_id: int, response: Response):
    doc = _documents.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    etag = _etags.get(doc_id, "")
    response.headers["ETag"] = f'"{etag}"'
    return doc


@router.put("/documents/{doc_id}")
def update_document(doc_id: int, request: _Request, body: dict | None = None, response: Response = None):
    doc = _documents.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if_match = request.headers.get("if-match", "").strip('"')
    current_etag = _etags.get(doc_id, "")
    if if_match and if_match != current_etag:
        raise HTTPException(status_code=412, detail="Precondition Failed — ETag mismatch")
    if not body:
        raise HTTPException(status_code=400, detail="Request body required")
    if "title" in body:
        doc["title"] = body["title"]
    if "content" in body:
        doc["content"] = body["content"]
    new_etag = hashlib.md5(f"{doc['title']}:{doc['content']}".encode()).hexdigest()
    _etags[doc_id] = new_etag
    response.headers["ETag"] = f'"{new_etag}"'
    return doc


@router.get("/step1")
def chain_step1():
    token = uuid_mod.uuid4().hex[:16]
    chain_id = uuid_mod.uuid4().hex[:8]
    _chain_tokens[token] = {"id": chain_id, "expires_at": time.time() + 30}
    answer = uuid_mod.uuid4().hex[:12]
    _chain_ids[chain_id] = answer
    return {"token": token, "message": "Use this token in step2 within 30 seconds"}


@router.get("/step2")
def chain_step2(token: str = Query(default="")):
    if not token or token not in _chain_tokens:
        raise HTTPException(status_code=400, detail="Invalid or missing token")
    data = _chain_tokens[token]
    if time.time() > data["expires_at"]:
        del _chain_tokens[token]
        raise HTTPException(status_code=400, detail="Token expired")
    chain_id = data["id"]
    del _chain_tokens[token]  # single-use
    return {"id": chain_id, "message": "Use this id in step3"}


@router.get("/step3/{chain_id}")
def chain_step3(chain_id: str):
    answer = _chain_ids.get(chain_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Invalid id")
    del _chain_ids[chain_id]
    return {"answer": answer, "message": "Chain complete!"}
