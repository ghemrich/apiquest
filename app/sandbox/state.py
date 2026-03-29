"""Per-session sandbox state isolation.

Each sandbox module registers a factory that returns fresh seed data.
State is cached per session (identified by cookie) and expires after
one hour of inactivity.
"""

import time
from typing import Any, Callable

from fastapi import Request

_TTL = 3600  # seconds

# module_name -> callable returning a fresh state dict
_factories: dict[str, Callable[[], dict[str, Any]]] = {}

# "module:session_id" -> {"data": {...}, "ts": float}
_store: dict[str, dict[str, Any]] = {}


def register(module: str, factory: Callable[[], dict[str, Any]]) -> None:
    """Register a seed-data factory for a sandbox module."""
    _factories[module] = factory


def get(module: str, request: Request) -> dict[str, Any]:
    """Return per-session state for *module*, creating from factory on first access."""
    sid: str = getattr(request.state, "sandbox_session", "anonymous")
    key = f"{module}:{sid}"
    entry = _store.get(key)
    if entry is not None:
        entry["ts"] = time.time()
        return entry["data"]
    data = _factories[module]()
    _store[key] = {"data": data, "ts": time.time()}
    _purge()
    return data


def _purge() -> None:
    cutoff = time.time() - _TTL
    for k in [k for k, v in _store.items() if v["ts"] < cutoff]:
        del _store[k]
