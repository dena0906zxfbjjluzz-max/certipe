"""PDF profesional horizontal · colores CertiPE (verde) de la versión anterior."""

from __future__ import annotations

import io
import math
import textwrap
from datetime import datetime
from typing import Any

import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# Misma paleta de la app / PDF anterior (no azul TECSUP)
ACCENT = (0.05, 0.43, 0.34)       # #0d6e56
ACCENT_2 = (0.77, 0.42, 0.11)     # #c46a1c naranja institución
INK = (0.08, 0.13, 0.11)          # #14211c
MUTED = (0.36, 0.42, 0.39)        # #5b6b63
LINE = (0.79, 0.84, 0.80)         # #c9d5cc
BG_SOFT = (0.95, 0.96, 0.94)      # #f3f6f2


def qr_png_bytes(url: str, box_size: int = 8) -> bytes:
    img = qrcode.make(url, border=1, box_size=box_size)
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
        return str(iso)[:10]


def _waves(c: canvas.Canvas, width: float, height: float) -> None:
    """Ondas suaves en tonos verdes (como fondo sutil anterior)."""
    c.saveState()
    c.setStrokeColorRGB(0.82, 0.88, 0.84)
    c.setLineWidth(0.35)
    for i in range(16):
        y0 = 16 * mm + i * 10 * mm
        path = c.beginPath()
        path.moveTo(14 * mm, y0)
        x = 14 * mm
        while x < width - 14 * mm:
            path.curveTo(
                x + 12 * mm,
                y0 + 3 * mm * math.sin(i + x / 45),
                x + 24 * mm,
                y0 - 3 * mm * math.sin(i + x / 32),
                x + 36 * mm,
                y0,
            )
            x += 36 * mm
        c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def _center_para(
    c: canvas.Canvas,
    text: str,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: int = 11,
    leading: float = 15,
    max_chars: int = 95,
    color: tuple[float, float, float] = MUTED,
) -> float:
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    for line in textwrap.wrap(text, width=max_chars) or [""]:
        c.drawCentredString(width / 2, y, line)
        y -= leading
    return y


def build_certificate_pdf(cert: dict[str, Any], verify_url: str) -> bytes:
    """Layout profesional horizontal · colores verdes CertiPE."""
    buf = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Fondo + textura
    c.setFillColorRGB(*BG_SOFT)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(11 * mm, 11 * mm, width - 22 * mm, height - 22 * mm, 4 * mm, fill=1, stroke=0)
    _waves(c, width, height)

    # Marco doble (como PDF anterior)
    c.setStrokeColorRGB(*ACCENT)
    c.setLineWidth(2.2)
    c.rect(10 * mm, 10 * mm, width - 20 * mm, height - 20 * mm, fill=0, stroke=1)
    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(0.6)
    c.rect(13 * mm, 13 * mm, width - 26 * mm, height - 26 * mm, fill=0, stroke=1)

    inst = str(cert.get("institution_name") or "Institución").strip()
    slogan = str(cert.get("institution_slogan") or "Formación con sentido").strip()

    # Cabecera
    c.setFillColorRGB(*INK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 25 * mm, "CertiPE")
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(*MUTED)
    c.drawString(20 * mm, height - 30 * mm, "Certificados con firma digital")

    # Institución en naranja (eyebrow de la web)
    inst_u = inst.upper()
    size_inst = 12 if len(inst_u) <= 30 else (10 if len(inst_u) <= 42 else 8)
    c.setFillColorRGB(*ACCENT_2)
    c.setFont("Helvetica-Bold", size_inst)
    c.drawRightString(width - 20 * mm, height - 25 * mm, inst_u[:44])
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(*MUTED)
    c.drawRightString(width - 20 * mm, height - 30 * mm, slogan[:48].upper())

    # Título
    c.setFillColorRGB(*ACCENT)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width / 2, height - 52 * mm, "CERTIFICADO")

    c.setFillColorRGB(*MUTED)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 66 * mm, "Otorgado a:")

    name = str(cert.get("holder_name") or "—").strip()
    c.setFillColorRGB(*INK)
    name_size = 20 if len(name) < 36 else (16 if len(name) < 50 else 13)
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(width / 2, height - 78 * mm, name)

    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(0.6)
    c.line(width / 2 - 68 * mm, height - 82 * mm, width / 2 + 68 * mm, height - 82 * mm)

    course = str(cert.get("course_title") or "—").strip()
    hours = cert.get("course_hours")
    grade = (cert.get("grade") or "").strip()
    notes = (cert.get("notes") or "").strip()
    city = (cert.get("city") or "Perú").strip()
    fecha = _fmt_fecha(cert.get("issued_at"))
    doc = str(cert.get("holder_doc") or "—")
    role = (cert.get("signer_role") or "Director académico").strip()
    firmante = str(cert.get("issued_by") or inst).strip()

    y = height - 98 * mm
    if grade:
        intro = f"Por haber aprobado con una nota de {grade} el curso / programa:"
    else:
        intro = "Por haber culminado satisfactoriamente el curso / programa:"

    y = _center_para(c, intro, y, width, size=11, leading=14, color=MUTED)

    c.setFont("Helvetica-Bold", 13 if len(course) < 50 else 11)
    c.setFillColorRGB(*ACCENT)  # curso en verde (como versión anterior)
    for line in textwrap.wrap(course, width=70) or [course]:
        c.drawCentredString(width / 2, y, line)
        y -= 15
    y -= 3

    detail_parts: list[str] = []
    if notes:
        detail_parts.append(notes.rstrip("."))
    if hours:
        detail_parts.append(f"con una duración de {hours} horas")
    if detail_parts:
        detail = " ".join(detail_parts)
        if detail[0].islower():
            detail = detail[0].upper() + detail[1:]
        if not detail.endswith("."):
            detail += "."
        y = _center_para(c, detail, y, width, size=11, leading=14, color=MUTED)

    y = _center_para(
        c,
        f"Documento de identidad: {doc}",
        y - 1,
        width,
        size=9,
        leading=12,
        color=MUTED,
    )

    if fecha:
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(*INK)
        c.drawCentredString(width / 2, y - 5, f"{city}, {fecha}")

    # QR + firma
    qr_size = 28 * mm
    qx, qy = 22 * mm, 26 * mm
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2 * mm, qy - 2 * mm, qr_size + 4 * mm, qr_size + 8 * mm, 2 * mm, fill=1, stroke=0)
    c.drawImage(
        ImageReader(io.BytesIO(qr_png_bytes(verify_url, box_size=5))),
        qx,
        qy,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(qx + qr_size / 2, qy - 3.5 * mm, "Escanea para validar")

    sig_cx = width / 2 + 10 * mm
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.8)
    c.line(sig_cx - 42 * mm, 42 * mm, sig_cx + 42 * mm, 42 * mm)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(*INK)
    c.drawCentredString(sig_cx, 35 * mm, firmante[:56])
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(sig_cx, 30 * mm, role[:56])

    # Barra inferior verde (como la versión anterior)
    c.setFillColorRGB(*ACCENT)
    c.rect(10 * mm, 10 * mm, width - 20 * mm, 11 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.95, 0.98, 0.96)
    c.setFont("Helvetica", 6.5)
    code = str(cert.get("id") or "")
    c.drawString(14 * mm, 13.5 * mm, f"Código: {code}  ·  {verify_url[:75]}")
    c.setFont("Helvetica", 6)
    c.drawRightString(width - 14 * mm, 13.5 * mm, "Firma digital Ed25519")

    c.showPage()
    c.save()
    return buf.getvalue()
