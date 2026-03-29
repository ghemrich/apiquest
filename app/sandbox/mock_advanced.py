"""Mock Advanced API — Track 7: System Design."""

import hashlib
import json
import time
import uuid as uuid_mod

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.sandbox import state

router = APIRouter(prefix="/api/v1/sandbox/advanced", tags=["Sandbox: Advanced"])

# --- Read-only (shared safely) ---
_expensive_data = {"data": [{"id": i, "value": f"result_{i}"} for i in range(1, 11)]}
_expensive_etag = hashlib.md5(json.dumps(_expensive_data).encode()).hexdigest()


def _seed():
    return {
        "batch_items": [],
        "batch_next_id": 1,
        "reports": {},
        "payments": {},
        "payment_next_id": 1,
        "webhook_registrations": [],
        "webhook_received": [],
        "flaky_counter": 0,
    }


state.register("advanced", _seed)


@router.get("/expensive-data")
def get_expensive_data(request: Request, response: Response):
    if_none_match = request.headers.get("if-none-match", "").strip('"')
    if if_none_match == _expensive_etag:
        return Response(status_code=304)
    response.headers["ETag"] = f'"{_expensive_etag}"'
    response.headers["Cache-Control"] = "max-age=300"
    return _expensive_data


@router.post("/items/batch")
def batch_create(request: Request, body: dict | None = None):
    s = state.get("advanced", request)
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
        new_item = {"id": s["batch_next_id"], "name": item["name"]}
        s["batch_next_id"] += 1
        s["batch_items"].append(new_item)
        created.append(new_item)
    return {"created": len(created), "items": created, "errors": errors}


@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
def create_report(request: Request, body: dict | None = None):
    s = state.get("advanced", request)
    if not body or "type" not in body:
        raise HTTPException(status_code=400, detail="type is required")
    # Deterministic ID for sales/Q1 so the challenge is testable
    if body.get("type") == "sales" and body.get("period") == "Q1":
        report_id = "rpt-q1"
    else:
        report_id = uuid_mod.uuid4().hex[:12]
    if report_id not in s["reports"]:
        s["reports"][report_id] = {
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
        "next_step": "Poll the status_url until status is 'complete', then GET /download",
    }


@router.get("/reports/{report_id}/status")
def report_status(request: Request, report_id: str):
    s = state.get("advanced", request)
    report = s["reports"].get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    elapsed = time.time() - report["created_at"]
    if elapsed < 3:
        report["status"] = "pending"
    elif elapsed < 6:
        report["status"] = "processing"
    else:
        report["status"] = "complete"
    result = {"report_id": report_id, "status": report["status"]}
    if report["status"] == "complete":
        result["download_url"] = f"/api/v1/sandbox/advanced/reports/{report_id}/download"
    return result


@router.get("/reports/{report_id}/download")
def download_report(request: Request, report_id: str):
    s = state.get("advanced", request)
    report = s["reports"].get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["status"] != "complete":
        elapsed = time.time() - report["created_at"]
        if elapsed < 6:
            raise HTTPException(status_code=409, detail="Report not yet complete. Poll /status until 'complete'.")
    data = [{"month": m, "revenue": 10000 + m * 500} for m in range(1, 4)]
    return {
        "report_id": report_id,
        "type": report["type"],
        "period": report["period"],
        "data": data,
        "next_step": "Sum the revenue values and POST to /report-check with report_id and total_revenue",
    }


@router.post("/report-check")
def report_check(request: Request, body: dict | None = None):
    """Validate that the player completed the full async flow."""
    s = state.get("advanced", request)
    if not body or "report_id" not in body or "total_revenue" not in body:
        raise HTTPException(
            status_code=400,
            detail='Submit {"report_id": "<id>", "total_revenue": <sum>} after downloading the report',
        )
    report = s["reports"].get(body["report_id"])
    if not report:
        return {"correct": False, "message": "Unknown report_id. Start by POSTing to /reports"}
    expected_revenue = sum(10000 + m * 500 for m in range(1, 4))  # 33000
    results = []
    all_correct = True
    if body["report_id"] == report["id"]:
        results.append({"field": "report_id", "correct": True})
    else:
        all_correct = False
        results.append({"field": "report_id", "correct": False, "hint": "Check the report_id from /reports"})
    if body["total_revenue"] == expected_revenue:
        results.append({"field": "total_revenue", "correct": True})
    else:
        all_correct = False
        results.append({"field": "total_revenue", "correct": False, "hint": "Sum all revenue values from the downloaded data"})
    return {"all_correct": all_correct, "results": results}


@router.post("/payments")
def create_payment(request: Request, body: dict | None = None):
    s = state.get("advanced", request)
    if not body or "amount" not in body or "currency" not in body:
        raise HTTPException(status_code=400, detail="amount and currency are required")
    idempotency_key = request.headers.get("idempotency-key", "")
    if idempotency_key and idempotency_key in s["payments"]:
        return s["payments"][idempotency_key]
    payment = {
        "id": s["payment_next_id"],
        "amount": body["amount"],
        "currency": body["currency"],
        "status": "completed",
    }
    s["payment_next_id"] += 1
    if idempotency_key:
        s["payments"][idempotency_key] = payment
    return payment


@router.post("/webhooks/register")
def register_webhook(request: Request, body: dict | None = None):
    s = state.get("advanced", request)
    if not body or "url" not in body or "events" not in body:
        raise HTTPException(status_code=400, detail="url and events are required")
    registration = {
        "id": uuid_mod.uuid4().hex[:8],
        "url": body["url"],
        "events": body["events"],
    }
    s["webhook_registrations"].append(registration)
    return registration


@router.post("/orders")
def create_order(request: Request, body: dict | None = None):
    s = state.get("advanced", request)
    if not body or "product" not in body:
        raise HTTPException(status_code=400, detail="product is required")
    order = {
        "id": uuid_mod.uuid4().hex[:8],
        "product": body["product"],
        "status": "created",
    }
    # Simulate webhook delivery
    for reg in s["webhook_registrations"]:
        if "order.created" in reg["events"]:
            s["webhook_received"].append({
                "event": "order.created",
                "data": order,
                "delivered_to": reg["url"],
                "timestamp": time.time(),
            })
    return order


@router.get("/webhooks/echo/received")
def get_received_webhooks(request: Request):
    s = state.get("advanced", request)
    return {"received": s["webhook_received"]}


@router.get("/flaky-service")
def flaky_service(request: Request):
    s = state.get("advanced", request)
    s["flaky_counter"] += 1
    if s["flaky_counter"] % 2 == 0:
        raise HTTPException(status_code=503, detail="Service Unavailable")
    return {"status": "ok", "data": "Here's your flaky data", "attempt": s["flaky_counter"]}
