"""Mock Advanced API — Track 7: System Design."""

import hashlib
import json
import time
import uuid as uuid_mod

from fastapi import APIRouter, HTTPException, Request, Response, status

router = APIRouter(prefix="/api/v1/sandbox/advanced", tags=["Sandbox: Advanced"])

# --- Cache / ETag ---
_expensive_data = {"data": [{"id": i, "value": f"result_{i}"} for i in range(1, 11)]}
_expensive_etag = hashlib.md5(json.dumps(_expensive_data).encode()).hexdigest()


@router.get("/expensive-data")
def get_expensive_data(request: Request, response: Response):
    if_none_match = request.headers.get("if-none-match", "").strip('"')
    if if_none_match == _expensive_etag:
        return Response(status_code=304)
    response.headers["ETag"] = f'"{_expensive_etag}"'
    response.headers["Cache-Control"] = "max-age=300"
    return _expensive_data


# --- Batch ---
_batch_items: list[dict] = []
_batch_next_id = 1


@router.post("/items/batch")
def batch_create(body: dict | None = None):
    global _batch_next_id
    if not body or "items" not in body:
        raise HTTPException(status_code=400, detail="items array required")
    items = body["items"]
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be an array")
    if len(items) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 items per batch")
    created = []
    errors = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict) or "name" not in item:
            errors.append({"index": idx, "error": "name is required"})
            continue
        new_item = {"id": _batch_next_id, "name": item["name"]}
        _batch_next_id += 1
        _batch_items.append(new_item)
        created.append(new_item)
    return {"created": len(created), "items": created, "errors": errors}


# --- Async reports ---
_reports: dict[str, dict] = {}


@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
def create_report(body: dict | None = None):
    if not body or "type" not in body:
        raise HTTPException(status_code=400, detail="type is required")
    report_id = uuid_mod.uuid4().hex[:12]
    _reports[report_id] = {
        "id": report_id,
        "type": body.get("type"),
        "period": body.get("period"),
        "status": "pending",
        "created_at": time.time(),
    }
    return {
        "report_id": report_id,
        "status": "pending",
        "status_url": f"/api/v1/sandbox/advanced/reports/{report_id}/status",
    }


@router.get("/reports/{report_id}/status")
def report_status(report_id: str):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    elapsed = time.time() - report["created_at"]
    if elapsed < 3:
        report["status"] = "pending"
    elif elapsed < 6:
        report["status"] = "processing"
    else:
        report["status"] = "complete"
    return {"report_id": report_id, "status": report["status"]}


@router.get("/reports/{report_id}/download")
def download_report(report_id: str):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["status"] != "complete":
        elapsed = time.time() - report["created_at"]
        if elapsed < 6:
            raise HTTPException(status_code=409, detail="Report not yet complete")
    return {
        "report_id": report_id,
        "type": report["type"],
        "period": report["period"],
        "data": [{"month": m, "revenue": 10000 + m * 500} for m in range(1, 4)],
    }


# --- Idempotent payments ---
_payments: dict[str, dict] = {}  # idempotency_key -> payment
_payment_next_id = 1


@router.post("/payments")
def create_payment(request: Request, body: dict | None = None):
    global _payment_next_id
    if not body or "amount" not in body or "currency" not in body:
        raise HTTPException(status_code=400, detail="amount and currency are required")
    idempotency_key = request.headers.get("idempotency-key", "")
    if idempotency_key and idempotency_key in _payments:
        return _payments[idempotency_key]
    payment = {
        "id": _payment_next_id,
        "amount": body["amount"],
        "currency": body["currency"],
        "status": "completed",
    }
    _payment_next_id += 1
    if idempotency_key:
        _payments[idempotency_key] = payment
    return payment


# --- Webhooks ---
_webhook_registrations: list[dict] = []
_webhook_received: list[dict] = []


@router.post("/webhooks/register")
def register_webhook(body: dict | None = None):
    if not body or "url" not in body or "events" not in body:
        raise HTTPException(status_code=400, detail="url and events are required")
    registration = {
        "id": uuid_mod.uuid4().hex[:8],
        "url": body["url"],
        "events": body["events"],
    }
    _webhook_registrations.append(registration)
    return registration


@router.post("/orders")
def create_order(body: dict | None = None):
    if not body or "product" not in body:
        raise HTTPException(status_code=400, detail="product is required")
    order = {
        "id": uuid_mod.uuid4().hex[:8],
        "product": body["product"],
        "status": "created",
    }
    # Simulate webhook delivery
    for reg in _webhook_registrations:
        if "order.created" in reg["events"]:
            _webhook_received.append({
                "event": "order.created",
                "data": order,
                "delivered_to": reg["url"],
                "timestamp": time.time(),
            })
    return order


@router.get("/webhooks/echo/received")
def get_received_webhooks():
    return {"received": _webhook_received}


# --- Flaky service (50% failure rate) ---
import random

_flaky_counter = 0


@router.get("/flaky-service")
def flaky_service():
    global _flaky_counter
    _flaky_counter += 1
    if _flaky_counter % 2 == 0:
        raise HTTPException(status_code=503, detail="Service Unavailable")
    return {"status": "ok", "data": "Here's your flaky data", "attempt": _flaky_counter}
