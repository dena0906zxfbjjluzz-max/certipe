"""Generación premium del certificado PDF (A4 horizontal) con ReportLab."""

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


# Paleta premium
NAVY = (0x0F / 255, 0x2C / 255, 0x59 / 255)  # #0F2C59
GOLD = (0xC4 / 255, 0x9A / 255, 0x3C / 255)  # acento sobrio
INK = (0.10, 0.12, 0.14)
MUTED = (0.38, 0.40, 0.44)
LINE = (0.78, 0.80, 0.84)

# Márgenes A4 landscape
MARGIN = 16 * mm


def qr_png_bytes(url: str, box_size: int = 6) -> bytes:
    img = qrcode.make(url, border=1, box_size=box_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _fmt_fecha(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        meses = (
            "enero febrero marzo abril mayo junio "
            "julio agosto setiembre octubre noviembre diciembre"
        ).split()
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return str(iso)[:10]


def _draw_frame(c: canvas.Canvas, w: float, h: float) -> None:
    """Marco doble limpio con margen premium."""
    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1.8)
    c.rect(MARGIN, MARGIN, w - 2 * MARGIN, h - 2 * MARGIN, stroke=1, fill=0)
    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(0.5)
    inset = 2.2 * mm
    c.rect(
        MARGIN + inset,
        MARGIN + inset,
        w - 2 * MARGIN - 2 * inset,
        h - 2 * MARGIN - 2 * inset,
        stroke=1,
        fill=0,
    )


def _center_text(
    c: canvas.Canvas,
    text: str,
    x_center: float,
    y: float,
    *,
    font: str = "Helvetica",
    size: float = 11,
    color: tuple[float, float, float] = INK,
    max_width_chars: int = 90,
    leading: float = 14,
) -> float:
    """Escribe párrafo centrado y devuelve la Y inferior siguiente."""
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    lines = textwrap.wrap(text, width=max_width_chars) or [""]
    for line in lines:
        c.drawCentredString(x_center, y, line)
        y -= leading
    return y


def generar_pdf(cert: dict[str, Any], verify_url: str) -> bytes:
    """
    Certificado profesional A4 horizontal.

    Estructura (de arriba a abajo):
      cabecera (marca + institución)
      CERTIFICADO
      Otorgado a / nombre
      párrafo limpio de mérito
      firma (centro-derecha)
      QR (abajo izquierda, sin URL legible)
    """
    buf = io.BytesIO()
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    cx = page_w / 2

    # Fondo
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    _draw_frame(c, page_w, page_h)

    # ── Cabecera ──────────────────────────────────────────────
    brand_y = page_h - MARGIN - 14 * mm
    c.setFillColorRGB(*INK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 8 * mm, brand_y, "CertiPE")
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(*MUTED)
    c.drawString(MARGIN + 8 * mm, brand_y - 4.5 * mm, "Certificados con firma digital")

    inst = str(cert.get("institution_name") or "Academia Demo Perú").strip()
    slogan = str(cert.get("institution_slogan") or "Formación con sentido").strip()
    c.setFillColorRGB(*NAVY)
    size_inst = 12 if len(inst) <= 28 else 9
    c.setFont("Helvetica-Bold", size_inst)
    c.drawRightString(page_w - MARGIN - 8 * mm, brand_y, inst.upper()[:42])
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(*MUTED)
    c.drawRightString(page_w - MARGIN - 8 * mm, brand_y - 4.5 * mm, slogan.upper()[:48])

    # ── Título ────────────────────────────────────────────────
    title_y = page_h - 58 * mm
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(cx, title_y, "CERTIFICADO")

    # Acento dorado fino bajo el título
    c.setStrokeColorRGB(*GOLD)
    c.setLineWidth(1.2)
    c.line(cx - 28 * mm, title_y - 4 * mm, cx + 28 * mm, title_y - 4 * mm)

    # ── Otorgado a + nombre ───────────────────────────────────
    c.setFillColorRGB(*MUTED)
    c.setFont("Helvetica", 11)
    c.drawCentredString(cx, title_y - 16 * mm, "Otorgado a:")

    name = str(cert.get("holder_name") or "—").strip()
    name_y = title_y - 30 * mm
    c.setFillColorRGB(*INK)
    name_size = 24 if len(name) <= 36 else (18 if len(name) <= 50 else 14)
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(cx, name_y, name)

    # Línea decorativa bajo el nombre
    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(0.7)
    c.line(cx - 55 * mm, name_y - 5 * mm, cx + 55 * mm, name_y - 5 * mm)

    # ── Cuerpo limpio (sin DNIs, IDs ni hashes) ────────────────
    course = str(cert.get("course_title") or "—").strip()
    hours = cert.get("course_hours")
    fecha = _fmt_fecha(cert.get("issued_at"))
    city = str(cert.get("city") or "").strip()
    if city:
        city = city[:1].upper() + city[1:]

    body_parts: list[str] = [
        "Por haber aprobado satisfactoriamente el curso / programa de:"
    ]
    body_y = name_y - 18 * mm
    body_y = _center_text(
        c,
        body_parts[0],
        cx,
        body_y,
        font="Helvetica",
        size=11,
        color=MUTED,
        max_width_chars=95,
        leading=14,
    )

    # Nombre del curso destacado
    c.setFont("Helvetica-Bold", 14 if len(course) < 48 else 11)
    c.setFillColorRGB(*NAVY)
    for line in textwrap.wrap(course, width=70) or [course]:
        c.drawCentredString(cx, body_y, line)
        body_y -= 16

    # Horas + fecha en una lectura fluida
    detail: list[str] = []
    if hours:
        detail.append(f"con una duración de {hours} horas")
    if fecha:
        if city:
            detail.append(f"Otorgado en {city} el {fecha}")
        else:
            detail.append(f"Otorgado el {fecha}")
    if detail:
        # Primera línea: duración; segunda: otorgado (más limpio)
        if hours and fecha:
            body_y = _center_text(
                c,
                f"con una duración de {hours} horas.",
                cx,
                body_y - 2,
                size=11,
                color=MUTED,
                leading=14,
            )
            body_y = _center_text(
                c,
                f"Otorgado el {fecha}." if not city else f"Otorgado en {city} el {fecha}.",
                cx,
                body_y,
                size=11,
                color=MUTED,
                leading=14,
            )
        else:
            text = detail[0]
            if not text.endswith("."):
                text += "."
            body_y = _center_text(
                c, text, cx, body_y - 2, size=11, color=MUTED, leading=14
            )

    # Periodo extra (notas) solo si aporta texto legible, sin códigos
    notes = (cert.get("notes") or "").strip()
    if notes and not notes.upper().startswith("CERT-"):
        body_y = _center_text(
            c,
            notes if notes.endswith(".") else notes + ".",
            cx,
            body_y - 2,
            size=10,
            color=MUTED,
            max_width_chars=95,
            leading=13,
        )

    # ── QR (abajo izquierda) — sin URL debajo ─────────────────
    qr_size = 26 * mm
    qr_x = MARGIN + 10 * mm
    qr_y = MARGIN + 12 * mm
    c.drawImage(
        ImageReader(io.BytesIO(qr_png_bytes(verify_url, box_size=5))),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 4 * mm, "Validar certificado")

    # ── Firma elegante (centro-derecha) ───────────────────────
    sig_cx = page_w * 0.62
    sig_line_y = MARGIN + 28 * mm
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.8)
    c.line(sig_cx - 38 * mm, sig_line_y, sig_cx + 38 * mm, sig_line_y)

    firmante = str(cert.get("issued_by") or inst).strip()
    cargo = str(cert.get("signer_role") or "Director académico").strip()

    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(*INK)
    c.drawCentredString(sig_cx, sig_line_y - 6 * mm, firmante[:52])

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(sig_cx, sig_line_y - 11 * mm, cargo[:52])

    # Institución debajo de la firma (sin IDs ni números)
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(*NAVY)
    c.drawCentredString(sig_cx, sig_line_y - 17 * mm, inst[:48])

    c.showPage()
    c.save()
    return buf.getvalue()


# API usada por la app
def build_certificate_pdf(cert: dict[str, Any], verify_url: str) -> bytes:
    return generar_pdf(cert, verify_url)
