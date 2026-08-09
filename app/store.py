"""Almacenamiento simple en JSON (MVP local)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STORE_PATH = DATA_DIR / "certificates.json"
_lock = threading.Lock()


def _empty() -> dict[str, Any]:
    return {"certificates": {}}


def _read() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        return _empty()
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty()


def _write(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STORE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STORE_PATH)


def save_certificate(record: dict[str, Any]) -> None:
    with _lock:
        data = _read()
        data["certificates"][record["id"]] = record
        _write(data)


def get_certificate(cert_id: str) -> dict[str, Any] | None:
    with _lock:
        return _read()["certificates"].get(cert_id)


def list_certificates() -> list[dict[str, Any]]:
    with _lock:
        items = list(_read()["certificates"].values())
    items.sort(key=lambda c: c.get("issued_at", ""), reverse=True)
    return items


def update_status(cert_id: str, status: str) -> dict[str, Any] | None:
    with _lock:
        data = _read()
        rec = data["certificates"].get(cert_id)
        if not rec:
            return None
        rec["status"] = status
        data["certificates"][cert_id] = rec
        _write(data)
        return rec
