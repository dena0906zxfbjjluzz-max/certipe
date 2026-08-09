"""Emisión, revocación y validación de certificados."""

from __future__ import annotations

import os
import secrets
import string
from datetime import datetime, timezone
from typing import Any

from app import crypto, store

DEFAULT_INSTITUTION_NAME = "Academia Demo Perú"
DEFAULT_INSTITUTION_ID = "academia-demo-pe"


def institution_name() -> str:
    return (
        os.environ.get("INSTITUTION_NAME")
        or os.environ.get("NOMBRE_INSTITUCION")
        or DEFAULT_INSTITUTION_NAME
    ).strip()


def institution_id() -> str:
    return (os.environ.get("INSTITUTION_ID") or DEFAULT_INSTITUTION_ID).strip()


# Compatibilidad con código anterior
INSTITUTION_NAME = DEFAULT_INSTITUTION_NAME
INSTITUTION_ID = DEFAULT_INSTITUTION_ID


def _new_id() -> str:
    alphabet = string.ascii_uppercase + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(12))
    return f"CERT-{body[:4]}-{body[4:8]}-{body[8:]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def issue(
    *,
    holder_name: str,
    holder_doc: str,
    course_title: str,
    course_hours: int | None = None,
    issued_by: str | None = None,
    notes: str | None = None,
    grade: str | None = None,
    city: str | None = None,
    signer_role: str | None = None,
    institution_slogan: str | None = None,
) -> dict[str, Any]:
    crypto.ensure_keys()
    cert_id = _new_id()
    issued_at = _now_iso()
    name = institution_name()
    inst_id = institution_id()

    payload = {
        "id": cert_id,
        "institution_id": inst_id,
        "institution_name": name,
        "holder_name": holder_name.strip(),
        "holder_doc": holder_doc.strip(),
        "course_title": course_title.strip(),
        "course_hours": course_hours,
        "issued_at": issued_at,
        "issued_by": (issued_by or name).strip(),
        "notes": (notes or "").strip() or None,
        "schema": "cert.pe.v1",
        "alg": "Ed25519",
    }

    signature = crypto.sign_payload(payload)
    pub = crypto.public_key_b64()
    digest = crypto.payload_hash(payload)

    record = {
        **payload,
        "grade": (grade or "").strip() or None,
        "city": (city or "").strip() or None,
        "signer_role": (signer_role or "").strip() or "Director académico",
        "institution_slogan": (institution_slogan or "").strip()
        or os.environ.get("INSTITUTION_SLOGAN", "Formación con sentido"),
        "signature": signature,
        "public_key": pub,
        "payload_hash": digest,
        "status": "valid",
    }
    store.save_certificate(record)
    return record


def revoke(cert_id: str) -> dict[str, Any] | None:
    rec = store.get_certificate(cert_id)
    if not rec:
        return None
    return store.update_status(cert_id, "revoked")


def validate(cert_id: str) -> dict[str, Any]:
    rec = store.get_certificate(cert_id)
    if not rec:
        return {
            "ok": False,
            "reason": "not_found",
            "message": "No existe un certificado con ese código.",
        }

    payload = {
        "id": rec["id"],
        "institution_id": rec["institution_id"],
        "institution_name": rec["institution_name"],
        "holder_name": rec["holder_name"],
        "holder_doc": rec["holder_doc"],
        "course_title": rec["course_title"],
        "course_hours": rec.get("course_hours"),
        "issued_at": rec["issued_at"],
        "issued_by": rec["issued_by"],
        "notes": rec.get("notes"),
        "schema": rec.get("schema", "cert.pe.v1"),
        "alg": rec.get("alg", "Ed25519"),
    }

    sig_ok = crypto.verify_payload(payload, rec["signature"], rec.get("public_key"))
    hash_ok = crypto.payload_hash(payload) == rec.get("payload_hash")
    status = rec.get("status", "valid")
    backend = crypto.last_verify_backend()

    if not sig_ok or not hash_ok:
        return {
            "ok": False,
            "reason": "tampered",
            "message": "La firma no coincide: el certificado fue alterado o es falso.",
            "certificate": rec,
            "signature_valid": sig_ok,
            "hash_valid": hash_ok,
            "verify_backend": backend,
        }

    if status == "revoked":
        return {
            "ok": False,
            "reason": "revoked",
            "message": "El certificado es auténtico pero fue revocado por la institución.",
            "certificate": rec,
            "signature_valid": True,
            "hash_valid": True,
            "verify_backend": backend,
        }

    motor_txt = " (motor_rust)" if backend == "motor_rust" else f" ({backend})"
    return {
        "ok": True,
        "reason": "valid",
        "message": (
            "Certificado auténtico: firma Ed25519 válida y sin alteraciones"
            f"{motor_txt}."
        ),
        "certificate": rec,
        "signature_valid": True,
        "hash_valid": True,
        "verify_backend": backend,
    }


def list_all() -> list[dict[str, Any]]:
    return store.list_certificates()
