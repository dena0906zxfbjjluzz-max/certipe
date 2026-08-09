"""Firmas Ed25519 (mismo enfoque que validador: seed hex + cryptography/PyNaCl)."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets as pysecrets
from pathlib import Path
from typing import Any

KEYS_DIR = Path(__file__).resolve().parent.parent / "keys"
SEED_PATH = KEYS_DIR / "institution_ed25519.seed.hex"

# Seed en memoria (prioridad: set_seed / env / archivo / generar)
_SEED: bytes | None = None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64d(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _hex_to_seed(texto: str) -> bytes:
    limpio = "".join(texto.strip().split())
    if limpio.startswith("0x"):
        limpio = limpio[2:]
    if len(limpio) != 64:
        raise ValueError("LLAVE_PRIVADA debe ser 64 caracteres hex (32 bytes).")
    return bytes.fromhex(limpio)


def set_seed_hex(seed_hex: str) -> None:
    """Fija la seed desde Streamlit secrets (producción)."""
    global _SEED
    _SEED = _hex_to_seed(seed_hex)


def _load_seed() -> bytes:
    global _SEED
    if _SEED is not None:
        return _SEED

    env = (
        os.environ.get("LLAVE_PRIVADA")
        or os.environ.get("INSTITUTION_PRIVATE_KEY")
        or ""
    ).strip()
    if env:
        _SEED = _hex_to_seed(env)
        return _SEED

    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if SEED_PATH.exists():
        _SEED = _hex_to_seed(SEED_PATH.read_text(encoding="utf-8"))
        return _SEED

    # Desarrollo: generar seed nueva
    raw = pysecrets.token_bytes(32)
    SEED_PATH.write_text(raw.hex(), encoding="utf-8")
    try:
        SEED_PATH.chmod(0o600)
    except OSError:
        pass
    _SEED = raw
    return _SEED


def ensure_keys() -> None:
    _load_seed()


def _sign_raw(message: bytes) -> tuple[bytes, bytes, str]:
    """
    Retorna (public_key_raw_32, signature_64, backend).
    Orden igual a validador: cryptography → PyNaCl.
    """
    seed = _load_seed()
    errores: list[str] = []

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        sk = Ed25519PrivateKey.from_private_bytes(seed)
        sig = sk.sign(message)
        pub = sk.public_key().public_bytes_raw()
        return pub, sig, "cryptography"
    except Exception as e:  # noqa: BLE001
        errores.append(f"cryptography: {e}")

    try:
        from nacl.signing import SigningKey

        sk = SigningKey(seed)
        signed = sk.sign(message)
        return bytes(sk.verify_key), bytes(signed.signature), "pynacl"
    except Exception as e:  # noqa: BLE001
        errores.append(f"pynacl: {e}")

    raise RuntimeError(
        "Ed25519 no disponible. Instale `cryptography` o `PyNaCl`. " + " | ".join(errores)
    )


def _verify_raw(message: bytes, signature: bytes, public_key: bytes) -> bool:
    errores: list[str] = []
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        vk = Ed25519PublicKey.from_public_bytes(public_key)
        vk.verify(signature, message)
        return True
    except Exception as e:  # noqa: BLE001
        errores.append(f"cryptography: {e}")

    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError

        VerifyKey(public_key).verify(message, signature)
        return True
    except Exception as e:  # noqa: BLE001
        errores.append(f"pynacl: {e}")

    return False


def public_key_raw() -> bytes:
    pub, _, _ = _sign_raw(b"")  # no: signing empty is ok but wasteful
    # better: derive without sign
    seed = _load_seed()
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw()
    except Exception:
        from nacl.signing import SigningKey

        return bytes(SigningKey(seed).verify_key)


def public_key_b64() -> str:
    return _b64(public_key_raw())


def public_key_hex() -> str:
    return public_key_raw().hex()


def public_key_fingerprint() -> str:
    return hashlib.sha256(public_key_raw()).hexdigest()[:16]


def seed_hex_for_export() -> str:
    """Solo para setup local: muestra seed (cuidado: secreto)."""
    return _load_seed().hex()


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(payload)).hexdigest()


def sign_payload(payload: dict[str, Any]) -> str:
    _, sig, _ = _sign_raw(canonical_payload(payload))
    return _b64(sig)


def verify_payload(
    payload: dict[str, Any],
    signature_b64: str,
    public_key_b64: str | None = None,
) -> bool:
    try:
        signature = _b64d(signature_b64)
        if public_key_b64:
            if len(public_key_b64) == 64 and all(c in "0123456789abcdefABCDEF" for c in public_key_b64):
                pub = bytes.fromhex(public_key_b64)
            else:
                pub = _b64d(public_key_b64)
        else:
            pub = public_key_raw()
        return _verify_raw(canonical_payload(payload), signature, pub)
    except Exception:
        return False
