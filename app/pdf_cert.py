"""PDF formal del certificado en horizontal (landscape) + QR."""

from __future__ import annotations

import io
import textwrap
from datetime import datetime
from typing import Any

import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def qr_png_bytes(url: str, box_size: int = 8) -> bytes:
    img = qrcode.make(url, border=2, box_size=box_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _fmt_fecha(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        raw = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        meses = (
            "enero febrero marzo abril mayo junio "
            "julio agosto setiembre octubre noviembre diciembre"
        ).split()
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return iso[:10]


def _wrapped_centered(
    c: canvas.Canvas,
    text: str,
    y: float,
    *,
    width: float,
    max_chars: int = 78,
    leading: float = 13,
    font: str = "Helvetica",
    size: int = 11,
    color: tuple[float, float, float] = (0.2, 0.22, 0.24),
) -> float:
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    for line in textwrap.wrap(text, width=max_chars) or [""]:
        c.drawCentredString(width / 2, y, line)
        y -= leading
    return y


def build_certificate_pdf(cert: dict[str, Any], verify_url: str) -> bytes:
    """PDF A4 horizontal, estilo certificado formal."""
    buf = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Fondo + doble marco
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColorRGB(0.12, 0.14, 0.16)
    c.setLineWidth(1.4)
    c.rect(10 * mm, 10 * mm, width - 20 * mm, height - 20 * mm, fill=0, stroke=1)
    c.setStrokeColorRGB(0.0, 0.55, 0.78)
    c.setLineWidth(0.6)
    c.rect(12.5 * mm, 12.5 * mm, width - 25 * mm, height - 25 * mm, fill=0, stroke=1)

    inst = str(cert.get("institution_name") or "Institución")

    # —— Cabecera izquierda / derecha ——
    c.setFillColorRGB(0.08, 0.1, 0.12)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, height - 24 * mm, "CertiPE")
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(0.4, 0.45, 0.5)
    c.drawString(20 * mm, height - 29 * mm, "Certificados con firma digital")

    c.setFillColorRGB(0.0, 0.55, 0.78)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 20 * mm, height - 24 * mm, inst.upper()[:42])
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.45, 0.5)
    c.drawRightString(width - 20 * mm, height - 29 * mm, "Documento verificado digitalmente")

    # Línea decorativa bajo cabecera
    c.setStrokeColorRGB(0.85, 0.88, 0.9)
    c.setLineWidth(0.5)
    c.line(20 * mm, height - 34 * mm, width - 20 * mm, height - 34 * mm)

    # —— Título ——
    c.setFillColorRGB(0.0, 0.55, 0.78)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - 52 * mm, "CERTIFICADO")

    c.setFillColorRGB(0.3, 0.33, 0.36)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 64 * mm, "Otorgado a:")

    name = str(cert.get("holder_name") or "—")
    c.setFillColorRGB(0.05, 0.07, 0.09)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 75 * mm, name)

    c.setStrokeColorRGB(0.75, 0.8, 0.85)
    c.setLineWidth(0.6)
    c.line(width / 2 - 70 * mm, height - 79 * mm, width / 2 + 70 * mm, height - 79 * mm)

    course = str(cert.get("course_title") or "—")
    hours = cert.get("course_hours")
    grade = cert.get("grade")
    notes = (cert.get("notes") or "").strip()
    fecha = _fmt_fecha(cert.get("issued_at"))
    city = str(cert.get("city") or "Perú")
    doc = str(cert.get("holder_doc") or "—")

    y = height - 92 * mm
    if grade:
        body = f"Por haber aprobado con una nota de {grade} el curso / programa: {course}."
    else:
        body = f"Por haber culminado satisfactoriamente el curso / programa: {course}."

    y = _wrapped_centered(c, body, y, width=width, max_chars=90, leading=14, size=11)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.35, 0.4, 0.45)
    c.drawCentredString(width / 2, y, f"Documento de identidad: {doc}")
    y -= 14

    if hours:
        y = _wrapped_centered(
            c,
            f"Con una duración de {hours} horas académicas.",
            y,
            width=width,
            max_chars=90,
            leading=13,
            size=11,
        )

    if notes:
        y = _wrapped_centered(
            c,
            notes,
            y,
            width=width,
            max_chars=90,
            leading=12,
            size=10,
            color=(0.4, 0.45, 0.5),
        )

    if fecha:
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(0.2, 0.22, 0.24)
        c.drawCentredString(width / 2, y - 4, f"{city}, {fecha}")

    # —— Pie: QR izquierda · firma derecha ——
    qr_bytes = qr_png_bytes(verify_url, box_size=5)
    qr_img = ImageReader(io.BytesIO(qr_bytes))
    qr_size = 30 * mm
    qx, qy = 22 * mm, 28 * mm
    c.drawImage(qr_img, qx, qy, width=qr_size, height=qr_size, mask="auto")
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.35, 0.4, 0.45)
    c.drawCentredString(qx + qr_size / 2, qy - 4 * mm, "Escanea para validar")

    # Zona firma centrada-derecha
    sig_cx = width * 0.72
    c.setStrokeColorRGB(0.15, 0.18, 0.2)
    c.setLineWidth(0.8)
    c.line(sig_cx - 40 * mm, 42 * mm, sig_cx + 40 * mm, 42 * mm)
    firmante = str(cert.get("issued_by") or inst)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.08, 0.1, 0.12)
    c.drawCentredString(sig_cx, 36 * mm, firmante[:52])
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.45, 0.5)
    c.drawCentredString(sig_cx, 31 * mm, "Responsable de emisión")

    # Barra inferior
    c.setFillColorRGB(0.08, 0.1, 0.12)
    c.rect(10 * mm, 10 * mm, width - 20 * mm, 12 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.95, 0.96, 0.97)
    c.setFont("Helvetica", 6.5)
    code = str(cert.get("id") or "")
    c.drawString(14 * mm, 14 * mm, f"Código: {code}  ·  Validar: {verify_url[:80]}")
    hash_s = str(cert.get("payload_hash") or "")
    c.drawRightString(
        width - 14 * mm,
        14 * mm,
        f"Ed25519 · {hash_s[:18]}…" if len(hash_s) > 18 else f"Ed25519 · {hash_s}",
    )

    c.showPage()
    c.save()
    return buf.getvalue()
