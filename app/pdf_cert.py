"""PDF estilo certificado de extensión (layout TECSUP), con marca CertiPE."""

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


# Paleta cercana al certificado de referencia (cian / negro / gris)
CYAN = (0.0, 0.68, 0.87)  # ~#00ADEF
INK = (0.05, 0.05, 0.06)
MUTED = (0.28, 0.3, 0.32)
SOFT_LINE = (0.82, 0.85, 0.88)


def qr_png_bytes(url: str, box_size: int = 8) -> bytes:
    img = qrcode.make(url, border=1, box_size=box_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _fmt_fecha(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        meses = (
            "enero febrero marzo abril mayo junio "
            "julio agosto setiembre octubre noviembre diciembre"
        ).split()
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return str(iso)[:10]


def _waves(c: canvas.Canvas, width: float, height: float) -> None:
    """Fondo ondulante gris claro como el modelo de referencia."""
    c.saveState()
    c.setStrokeColorRGB(0.88, 0.9, 0.92)
    c.setLineWidth(0.4)
    for i in range(22):
        y0 = 12 * mm + i * 8.5 * mm
        p = c.beginPath()
        p.moveTo(8 * mm, y0)
        x = 8 * mm
        while x < width - 8 * mm:
            amp = 2.8 * mm
            p.curveTo(
                x + 10 * mm,
                y0 + amp * math.sin((i + x) / 28),
                x + 20 * mm,
                y0 - amp * math.cos((i + x) / 35),
                x + 30 * mm,
                y0,
            )
            x += 30 * mm
        c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def _center(
    c: canvas.Canvas,
    text: str,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: int = 11,
    leading: float = 14,
    max_chars: int = 100,
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
    Layout igual al modelo profesional:
    header izq/der · CERTIFICADO · Otorgado a · texto · ciudad · QR + firma · URL pie.
    """
    buf = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Fondo blanco limpio + olas
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    _waves(c, width, height)

    inst = str(cert.get("institution_name") or "Institución").strip()
    slogan = str(
        cert.get("institution_slogan") or "TECNOLOGÍA CON SENTIDO"
    ).strip().upper()

    # ——— Header: CertiPE (tipo CPE) | Institución (tipo Tecsup) ———
    c.setFillColorRGB(*INK)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(20 * mm, height - 28 * mm, "CertiPE")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*MUTED)
    # dos líneas tipo "Cursos y Programa de Extensión"
    c.drawString(52 * mm, height - 24 * mm, "Certificados y")
    c.drawString(52 * mm, height - 28.5 * mm, "firma digital")

    # Marca de institución a la derecha (cian)
    c.setFillColorRGB(*CYAN)
    size_inst = 16 if len(inst) <= 18 else (12 if len(inst) <= 32 else 9)
    c.setFont("Helvetica-Bold", size_inst)
    c.drawRightString(width - 20 * mm, height - 24 * mm, inst.upper()[:40])
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.35, 0.55, 0.7)
    c.drawRightString(width - 20 * mm, height - 30 * mm, slogan[:48])

    # ——— CERTIFICADO ———
    c.setFillColorRGB(*CYAN)
    c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(width / 2, height - 58 * mm, "CERTIFICADO")

    # Otorgado a
    c.setFillColorRGB(*INK)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 76 * mm, "Otorgado a:")

    name = str(cert.get("holder_name") or "—").strip()
    name_size = 18 if len(name) < 40 else (14 if len(name) < 55 else 12)
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(width / 2, height - 88 * mm, name)

    course = str(cert.get("course_title") or "—").strip()
    hours = cert.get("course_hours")
    grade = (cert.get("grade") or "").strip()
    notes = (cert.get("notes") or "").strip()
    city = (cert.get("city") or "Perú").strip()
    # Capitalizar ciudad como "Trujillo"
    if city:
        city = city[:1].upper() + city[1:]
    fecha = _fmt_fecha(cert.get("issued_at"))
    firmante = str(cert.get("issued_by") or inst).strip()
    role = (cert.get("signer_role") or "Director Académico Nacional").strip()

    y = height - 108 * mm

    # Párrafo nota + curso (nota en negrita en el mismo estilo)
    if grade:
        # "Por haber aprobado con una nota de 16 (Dieciséis) el Curso de Extensión:"
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(*INK)
        pre = "Por haber aprobado con una nota de "
        mid = grade
        post = " el curso / programa:"
        full = pre + mid + post
        # dibujar entero centrado, luego el curso en bold
        y = _center(c, full, y, width, size=11, leading=14, color=INK, max_chars=105)
    else:
        y = _center(
            c,
            "Por haber culminado satisfactoriamente el curso / programa:",
            y,
            width,
            size=11,
            leading=14,
            color=INK,
        )

    c.setFont("Helvetica-Bold", 13 if len(course) < 48 else 11)
    c.setFillColorRGB(*INK)
    for line in textwrap.wrap(course, 72) or [course]:
        c.drawCentredString(width / 2, y, line)
        y -= 15
    y -= 4

    # Fechas / horas (como el modelo en 1–2 líneas)
    if notes and hours:
        line1 = notes.rstrip(".")
        line2 = f"con una duración de {hours} horas."
        y = _center(c, line1, y, width, size=11, leading=14, color=INK)
        y = _center(c, line2, y, width, size=11, leading=14, color=INK)
    elif notes:
        t = notes if notes.endswith(".") else notes + "."
        y = _center(c, t, y, width, size=11, leading=14, color=INK)
    elif hours:
        y = _center(
            c,
            f"Con una duración de {hours} horas.",
            y,
            width,
            size=11,
            leading=14,
            color=INK,
        )

    if fecha:
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(*INK)
        c.drawCentredString(width / 2, y - 8, f"{city}, {fecha}")

    # ——— QR izquierda ———
    qr_size = 26 * mm
    qx, qy = 22 * mm, 24 * mm
    c.drawImage(
        ImageReader(io.BytesIO(qr_png_bytes(verify_url, box_size=5))),
        qx,
        qy,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )

    # ——— Firma centrada (como TECSUP) ———
    sig_cx = width / 2
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.9)
    c.line(sig_cx - 45 * mm, 40 * mm, sig_cx + 45 * mm, 40 * mm)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(*INK)
    c.drawCentredString(sig_cx, 33 * mm, firmante[:56])
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(sig_cx, 27.5 * mm, role[:56])

    # ——— Pie URL + datos institución (sin barra verde gruesa) ———
    c.setFont("Helvetica", 6.5)
    c.setFillColorRGB(*MUTED)
    c.drawCentredString(width / 2, 16 * mm, verify_url[:115])
    c.setFont("Helvetica", 6)
    legal = (
        f"{inst}  ·  Código {cert.get('id', '')}  ·  "
        "Documento firmado digitalmente con Ed25519"
    )
    c.drawCentredString(width / 2, 11.5 * mm, legal[:130])

    c.showPage()
    c.save()
    return buf.getvalue()
