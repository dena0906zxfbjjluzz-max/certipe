"""PDF formal del certificado (estilo institucional) + QR de validación."""

from __future__ import annotations

import io
import textwrap
from datetime import datetime
from typing import Any

import qrcode
from reportlab.lib.pagesizes import A4
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
        # 2026-08-09T21:02:55+00:00
        raw = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        meses = (
            "enero febrero marzo abril mayo junio "
            "julio agosto setiembre octubre noviembre diciembre"
        ).split()
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return iso[:10]


def _draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    *,
    max_width_chars: int = 62,
    leading: float = 14,
    font: str = "Helvetica",
    size: int = 11,
    color: tuple[float, float, float] = (0.2, 0.22, 0.24),
    center: bool = True,
    page_width: float = A4[0],
) -> float:
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    lines = textwrap.wrap(text, width=max_width_chars) or [""]
    for line in lines:
        if center:
            c.drawCentredString(page_width / 2, y, line)
        else:
            c.drawString(x, y, line)
        y -= leading
    return y


def build_certificate_pdf(cert: dict[str, Any], verify_url: str) -> bytes:
    """
    PDF vertical tipo certificado institucional (referencia TECSUP/CPE),
    con QR y huella criptográfica discreta al pie.
    """
    buf = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # Fondo blanco limpio + marco fino
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    # doble marco
    c.setStrokeColorRGB(0.12, 0.14, 0.16)
    c.setLineWidth(1.2)
    c.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm, fill=0, stroke=1)
    c.setLineWidth(0.4)
    c.setStrokeColorRGB(0.45, 0.55, 0.65)
    c.rect(14 * mm, 14 * mm, width - 28 * mm, height - 28 * mm, fill=0, stroke=1)

    inst = str(cert.get("institution_name") or "Institución")
    # Cabecera institucional (estilo CPE + marca a la derecha)
    c.setFillColorRGB(0.08, 0.1, 0.12)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(22 * mm, height - 28 * mm, "CertiPE")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.35, 0.4, 0.45)
    c.drawString(22 * mm, height - 33 * mm, "Certificados con firma digital")

    c.setFillColorRGB(0.0, 0.55, 0.78)  # azul institucional tipo referencia
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 22 * mm, height - 28 * mm, inst.upper()[:40])
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.45, 0.5)
    c.drawRightString(width - 22 * mm, height - 33 * mm, "Documento verificado digitalmente")

    # Título grande
    c.setFillColorRGB(0.0, 0.55, 0.78)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width / 2, height - 55 * mm, "CERTIFICADO")

    # Otorgado a
    c.setFillColorRGB(0.25, 0.28, 0.3)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 72 * mm, "Otorgado a:")

    name = str(cert.get("holder_name") or "—")
    c.setFillColorRGB(0.05, 0.07, 0.09)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 84 * mm, name)

    # Línea bajo el nombre
    c.setStrokeColorRGB(0.75, 0.8, 0.85)
    c.setLineWidth(0.6)
    c.line(width / 2 - 55 * mm, height - 88 * mm, width / 2 + 55 * mm, height - 88 * mm)

    doc = str(cert.get("holder_doc") or "—")
    course = str(cert.get("course_title") or "—")
    hours = cert.get("course_hours")
    grade = cert.get("grade")  # opcional, ej. "16"
    notes = (cert.get("notes") or "").strip()
    fecha = _fmt_fecha(cert.get("issued_at"))
    city = str(cert.get("city") or "Perú")

    # Párrafo principal
    if grade:
        body = (
            f"Por haber aprobado con una nota de {grade} el curso / programa: {course}."
        )
    else:
        body = f"Por haber culminado satisfactoriamente el curso / programa: {course}."

    y = height - 102 * mm
    y = _draw_wrapped(
        c,
        body,
        22 * mm,
        y,
        max_width_chars=68,
        leading=15,
        font="Helvetica",
        size=11,
        page_width=width,
    )

    if hours:
        y -= 4
        y = _draw_wrapped(
            c,
            f"Con una duración de {hours} horas académicas.",
            22 * mm,
            y,
            max_width_chars=68,
            leading=14,
            size=11,
            page_width=width,
        )

    if notes:
        y -= 2
        y = _draw_wrapped(
            c,
            notes,
            22 * mm,
            y,
            max_width_chars=68,
            leading=13,
            size=10,
            color=(0.35, 0.4, 0.45),
            page_width=width,
        )

    y -= 6
    if fecha:
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(0.2, 0.22, 0.24)
        c.drawCentredString(width / 2, y, f"{city}, {fecha}")
        y -= 18

    # Bloque firma (derecha) + QR (izquierda) — como el de referencia
    qr_bytes = qr_png_bytes(verify_url, box_size=5)
    qr_img = ImageReader(io.BytesIO(qr_bytes))
    qr_size = 32 * mm
    qx = 24 * mm
    qy = 48 * mm
    c.drawImage(qr_img, qx, qy, width=qr_size, height=qr_size, mask="auto")
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.35, 0.4, 0.45)
    c.drawCentredString(qx + qr_size / 2, qy - 4 * mm, "Escanea para validar")

    # Firma
    sig_x = width - 70 * mm
    c.setStrokeColorRGB(0.2, 0.22, 0.24)
    c.setLineWidth(0.7)
    c.line(sig_x - 25 * mm, 62 * mm, sig_x + 35 * mm, 62 * mm)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.08, 0.1, 0.12)
    firmante = str(cert.get("issued_by") or inst)
    c.drawCentredString(sig_x + 5 * mm, 55 * mm, firmante[:48])
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.45, 0.5)
    c.drawCentredString(sig_x + 5 * mm, 50 * mm, "Responsable de emisión")

    # Barra inferior negra + código / validación
    c.setFillColorRGB(0.08, 0.1, 0.12)
    c.rect(12 * mm, 12 * mm, width - 24 * mm, 18 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.95, 0.96, 0.97)
    c.setFont("Helvetica", 6.5)
    code = str(cert.get("id") or "")
    c.drawString(16 * mm, 20 * mm, f"Código: {code}")
    c.drawString(16 * mm, 15 * mm, f"Validar: {verify_url[:72]}{'…' if len(verify_url) > 72 else ''}")
    c.setFont("Helvetica", 6)
    c.drawRightString(width - 16 * mm, 20 * mm, f"Alg: {cert.get('alg', 'Ed25519')}")
    hash_s = str(cert.get("payload_hash") or "")
    c.drawRightString(width - 16 * mm, 15 * mm, f"Hash: {hash_s[:20]}…" if len(hash_s) > 20 else f"Hash: {hash_s}")

    c.showPage()
    c.save()
    return buf.getvalue()
