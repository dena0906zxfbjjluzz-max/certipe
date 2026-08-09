"""PDF profesional del certificado (layout paisajístico tipo extensión académica)."""

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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


# Azul institucional (referencia: limpio y legible)
BLUE = (0.0, 0.62, 0.82)
INK = (0.08, 0.1, 0.12)
MUTED = (0.35, 0.4, 0.45)
SOFT = (0.9, 0.92, 0.94)


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
    """Fondo sutil de líneas onduladas (aspecto profesional, no genérico plano)."""
    c.saveState()
    c.setStrokeColorRGB(0.88, 0.9, 0.92)
    c.setLineWidth(0.35)
    for i in range(18):
        y0 = 18 * mm + i * 9 * mm
        path = c.beginPath()
        path.moveTo(15 * mm, y0)
        x = 15 * mm
        while x < width - 15 * mm:
            path.curveTo(
                x + 12 * mm,
                y0 + 3.5 * mm * math.sin(i + x / 40),
                x + 24 * mm,
                y0 - 3.5 * mm * math.sin(i + x / 30),
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
    """
    Layout horizontal profesional:
    logos/header · CERTIFICADO · Otorgado a · cuerpo · ciudad/fecha · QR + firma · pie.
    """
    buf = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Fondo blanco + textura suave
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    _waves(c, width, height)

    inst = str(cert.get("institution_name") or "Institución").strip()
    slogan = str(cert.get("institution_slogan") or "Formación con sentido").strip()
    brand = str(cert.get("brand_short") or "CertiPE").strip()
    brand_sub = str(cert.get("brand_sub") or "Certificados con firma digital").strip()

    # ——— Cabecera tipo CPE | Institución ———
    # Izquierda: marca corta
    c.setFillColorRGB(*INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(22 * mm, height - 26 * mm, brand[:18])
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MUTED)
    c.drawString(22 * mm, height - 31 * mm, brand_sub[:48])

    # Derecha: nombre de institución (nivel profesional, no se aprieta)
    c.setFillColorRGB(*BLUE)
    c.setFont("Helvetica-Bold", 14)
    # Si el nombre es largo, reducir tamaño
    max_inst = 42
    inst_draw = inst.upper()
    size_inst = 14 if len(inst_draw) <= 28 else (11 if len(inst_draw) <= 40 else 9)
    c.setFont("Helvetica-Bold", size_inst)
    c.drawRightString(width - 22 * mm, height - 25 * mm, inst_draw[:max_inst])
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(*MUTED)
    c.drawRightString(width - 22 * mm, height - 30 * mm, slogan[:50].upper())

    # ——— Título principal ———
    c.setFillColorRGB(*BLUE)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 58 * mm, "CERTIFICADO")

    # ——— Otorgado a ———
    c.setFillColorRGB(*MUTED)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 74 * mm, "Otorgado a:")

    name = str(cert.get("holder_name") or "—").strip()
    c.setFillColorRGB(*INK)
    name_size = 20 if len(name) < 36 else (16 if len(name) < 50 else 13)
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(width / 2, height - 86 * mm, name)

    # ——— Cuerpo del texto (centro, como el modelo profesional) ———
    course = str(cert.get("course_title") or "—").strip()
    hours = cert.get("course_hours")
    grade = (cert.get("grade") or "").strip()
    notes = (cert.get("notes") or "").strip()
    city = (cert.get("city") or "Perú").strip()
    fecha = _fmt_fecha(cert.get("issued_at"))
    doc = str(cert.get("holder_doc") or "—")
    role = (cert.get("signer_role") or "Director académico").strip()
    firmante = str(cert.get("issued_by") or inst).strip()

    y = height - 104 * mm

    if grade:
        intro = f"Por haber aprobado con una nota de {grade} el curso / programa:"
    else:
        intro = "Por haber culminado satisfactoriamente el curso / programa:"

    y = _center_para(c, intro, y, width, size=11, leading=14, color=MUTED, max_chars=100)

    # Nombre del curso en negrita (más jerárquico)
    c.setFont("Helvetica-Bold", 13 if len(course) < 50 else 11)
    c.setFillColorRGB(*INK)
    for line in textwrap.wrap(course, width=70) or [course]:
        c.drawCentredString(width / 2, y, line)
        y -= 15
    y -= 4

    # Rango de fechas / detalle (notas) + horas en un solo bloque limpio
    detail_parts: list[str] = []
    if notes:
        detail_parts.append(notes.rstrip("."))
    if hours:
        detail_parts.append(f"con una duración de {hours} horas")
    if detail_parts:
        detail = " ".join(detail_parts)
        if not detail[0].isupper():
            detail = detail[0].upper() + detail[1:]
        if not detail.endswith("."):
            detail += "."
        y = _center_para(c, detail, y, width, size=11, leading=14, color=MUTED, max_chars=100)

    y = _center_para(
        c,
        f"Documento de identidad: {doc}",
        y - 2,
        width,
        size=9,
        leading=12,
        color=MUTED,
        max_chars=100,
    )

    if fecha:
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(*INK)
        c.drawCentredString(width / 2, y - 6, f"{city}, {fecha}")

    # ——— QR (izq) · Firma centrada (como TECSUP) ———
    qr_size = 28 * mm
    qx, qy = 24 * mm, 26 * mm
    c.drawImage(
        ImageReader(io.BytesIO(qr_png_bytes(verify_url, box_size=5))),
        qx,
        qy,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )

    # Firma al centro inferior
    sig_cx = width / 2 + 8 * mm
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.8)
    c.line(sig_cx - 42 * mm, 40 * mm, sig_cx + 42 * mm, 40 * mm)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(*INK)
    c.drawCentredString(sig_cx, 33 * mm, firmante[:56])
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(sig_cx, 28 * mm, role[:56])

    # ——— Pie legal / validación ———
    c.setFont("Helvetica", 6.5)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(width / 2, 18 * mm, verify_url[:110])
    c.setFont("Helvetica", 6)
    legal = f"{inst}  ·  Código {cert.get('id', '')}  ·  Firma digital Ed25519"
    c.drawCentredString(width / 2, 13.5 * mm, legal[:120])

    c.showPage()
    c.save()
    return buf.getvalue()
