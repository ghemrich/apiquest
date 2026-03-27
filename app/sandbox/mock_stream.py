"""Mock Stream API — Track 6: Real-Time APIs (WebSocket + SSE)."""

import asyncio
import json
import random
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/sandbox/stream", tags=["Sandbox: Stream"])


# --- SSE: Price stream ---
async def _price_generator():
    symbols = ["BTC", "ETH", "DOGE", "SOL", "ADA"]
    prices = {"BTC": 67000.0, "ETH": 3500.0, "DOGE": 0.15, "SOL": 145.0, "ADA": 0.55}
    for _ in range(20):
        symbol = random.choice(symbols)
        prices[symbol] *= 1 + random.uniform(-0.02, 0.02)
        event = json.dumps({"symbol": symbol, "price": round(prices[symbol], 2), "timestamp": time.time()})
        yield f"data: {event}\n\n"
        await asyncio.sleep(1)


@router.get("/prices")
async def sse_prices():
    return StreamingResponse(
        _price_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# --- WebSocket: Chat echo ---
@router.websocket("/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Welcome to API Quest Chat!", "type": "system"})
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "")
            await websocket.send_json({"echo": text, "type": "echo"})
    except WebSocketDisconnect:
        pass


# --- WebSocket: Quiz ---
@router.websocket("/quiz")
async def ws_quiz(websocket: WebSocket):
    await websocket.accept()
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    correct_answer = a * b
    await websocket.send_json({
        "question": f"What is {a} * {b}?",
        "timeout_seconds": 5,
    })
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        answer = data.get("answer")
        if answer == correct_answer:
            await websocket.send_json({"correct": True, "message": "Well done!"})
        else:
            await websocket.send_json({"correct": False, "message": f"Wrong! The answer was {correct_answer}."})
    except asyncio.TimeoutError:
        await websocket.send_json({"correct": False, "message": "Time's up!"})
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# --- WebSocket: Heartbeat ---
@router.websocket("/heartbeat")
async def ws_heartbeat(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "Send ping every 15s to stay alive"})
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "disconnect", "reason": "No ping received for 30 seconds"})
                await websocket.close()
                break
    except WebSocketDisconnect:
        pass


# --- WebSocket: Channels ---
_CHANNELS = {"sports", "tech", "finance"}


@router.websocket("/channels")
async def ws_channels(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Subscribe to a channel: sports, tech, or finance"})
    subscribed: set[str] = set()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            channel = data.get("channel", "")
            if action == "subscribe" and channel in _CHANNELS:
                subscribed.add(channel)
                await websocket.send_json({
                    "subscribed": channel,
                    "message": f"You will now receive {channel} updates",
                })
                # Send a sample notification
                await websocket.send_json({
                    "channel": channel,
                    "type": "notification",
                    "data": {"headline": f"Breaking {channel} news!", "timestamp": time.time()},
                })
            elif action == "subscribe":
                await websocket.send_json({"error": f"Unknown channel: {channel}"})
            elif action == "unsubscribe" and channel in subscribed:
                subscribed.discard(channel)
                await websocket.send_json({"unsubscribed": channel})
            else:
                await websocket.send_json({"error": "Send {action: 'subscribe', channel: '<name>'}"})
    except WebSocketDisconnect:
        pass
