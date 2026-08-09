#!/usr/bin/env python3
"""
Prueba demo de CertiPE (sin Streamlit).

Recorre el flujo local:
  1) fija seed Ed25519
  2) emite un certificado de ejemplo
  3) valida la firma / hash
  4) comprueba que un tampering se detecta
  5) genera PDF + que el motor_rust esté disponible (si se compiló)

Uso:
  python demo_prueba.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Raíz del repo en sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Seed de demo (solo pruebas; en producción usa secrets)
DEMO_SEED = "43cd50f46eafc89c4dde911db2d2c17bdd09c2f3c6e454cf4b435ded76184526"


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ {msg}")
    sys.exit(1)


def main() -> None:
    print("\n=== CertiPE · prueba demo ===\n")

    from app import certificates, crypto
    from app import pdf_cert
    from app import store

    # Usar store temporal para no mezclar con datos reales
    tmp = tempfile.TemporaryDirectory(prefix="certipe_demo_")
    store.DATA_DIR = Path(tmp.name)
    store.STORE_PATH = Path(tmp.name) / "certificates.json"

    print("1) Claves Ed25519")
    crypto.set_seed_hex(DEMO_SEED)
    crypto.ensure_keys()
    fp = crypto.public_key_fingerprint()
    ok(f"Huella de clave pública: {fp}")
    rust = crypto.motor_rust_disponible()
    ok(f"motor_rust disponible: {rust}")

    print("\n2) Emitir certificado de ejemplo")
    rec = certificates.issue(
        holder_name="Denilson Aurely Padilla Arevalo",
        holder_doc="12345678",
        course_title="Power BI desde cero",
        course_hours=32,
        issued_by="Academia Demo Perú",
        signer_role="Director académico",
        city="Trujillo",
        notes="Prueba demo CertiPE",
        grade="16",
    )
    codigo = rec["id"]
    ok(f"Código: {codigo}")
    ok(f"Hash: {rec['payload_hash'][:16]}…")
    ok(f"Firma (b64): {rec['signature'][:24]}…")

    print("\n3) Validar (debe ser OK)")
    r = certificates.validate(codigo)
    if not r.get("ok"):
        fail(f"Validación falló: {r}")
    ok(r["message"])
    ok(f"Backend de firma: {r.get('verify_backend')}")

    print("\n4) Alterar nombre (debe fallar)")
    rec_bad = dict(rec)
    rec_bad["holder_name"] = "NOMBRE ALTERADO"
    store.save_certificate(rec_bad)
    r2 = certificates.validate(codigo)
    if r2.get("ok"):
        fail("Debió rechazar el certificado alterado")
    ok(f"Detectado: {r2.get('reason')} — {r2.get('message')}")

    # Restaurar original para PDF
    store.save_certificate(rec)

    print("\n5) PDF del certificado")
    verify_url = f"https://ejemplo.streamlit.app/?codigo={codigo}"
    try:
        pdf = pdf_cert.build_certificate_pdf(rec, verify_url)
        if not pdf.startswith(b"%PDF"):
            fail("El PDF no tiene cabecera válida")
        out = Path(tmp.name) / f"{codigo}.pdf"
        out.write_bytes(pdf)
        ok(f"PDF generado ({len(pdf)} bytes) → {out.name}")
    except Exception as e:  # noqa: BLE001
        fail(f"PDF: {e}")

    print("\n=== Demo OK — flujo emitir / validar / detectar fraude / PDF ===\n")
    print("Siguiente: streamlit run app.py")
    print("  · Emitir (login institución)")
    print("  · Validar con el código CERT-…")
    print("  · Lista de alumnos → Supabase\n")
    tmp.cleanup()


if __name__ == "__main__":
    main()
