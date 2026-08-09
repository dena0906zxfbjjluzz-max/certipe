"""PDF del certificado + QR de validación pública."""

from __future__ import annotations

import io
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


def build_certificate_pdf(cert: dict[str, Any], verify_url: str) -> bytes:
    """Genera un PDF A4 horizontal con datos del certificado y QR."""
    buf = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Fondo y marco
    c.setFillColorRGB(0.95, 0.96, 0.94)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColorRGB(0.05, 0.43, 0.34)
    c.setLineWidth(2.5)
    c.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm, fill=0, stroke=1)
    c.setLineWidth(0.6)
    c.setStrokeColorRGB(0.77, 0.83, 0.80)
    c.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm, fill=0, stroke=1)

    # Cabecera
    c.setFillColorRGB(0.77, 0.42, 0.11)
    c.setFont("Helvetica-Bold", 11)
    inst = str(cert.get("institution_name") or "Institución")
    c.drawCentredString(width / 2, height - 28 * mm, inst.upper())

    c.setFillColorRGB(0.08, 0.13, 0.11)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2 - 18 * mm, height - 48 * mm, "Certificado de participación")

    c.setFillColorRGB(0.36, 0.42, 0.39)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2 - 18 * mm, height - 58 * mm, "Se certifica que")

    c.setFillColorRGB(0.08, 0.13, 0.11)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2 - 18 * mm, height - 72 * mm, str(cert.get("holder_name") or "—"))

    c.setFillColorRGB(0.36, 0.42, 0.39)
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        width / 2 - 18 * mm,
        height - 82 * mm,
        f"Documento: {cert.get('holder_doc') or '—'}",
    )
    c.drawCentredString(width / 2 - 18 * mm, height - 92 * mm, "completó el programa")

    c.setFillColorRGB(0.05, 0.43, 0.34)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2 - 18 * mm, height - 105 * mm, str(cert.get("course_title") or "—"))

    hours = cert.get("course_hours")
    if hours:
        c.setFillColorRGB(0.36, 0.42, 0.39)
        c.setFont("Helvetica", 11)
        c.drawCentredString(
            width / 2 - 18 * mm,
            height - 114 * mm,
            f"{hours} horas académicas",
        )

    # Metadatos
    c.setFillColorRGB(0.08, 0.13, 0.11)
    c.setFont("Helvetica", 9)
    y = 48 * mm
    lines = [
        f"Código: {cert.get('id')}",
        f"Emitido: {cert.get('issued_at')}",
        f"Firmado por: {cert.get('issued_by')}",
        f"Algoritmo: {cert.get('alg', 'Ed25519')}",
        f"Hash SHA-256: {cert.get('payload_hash')}",
        f"Firma: {str(cert.get('signature') or '')[:56]}…",
    ]
    for line in lines:
        c.drawString(22 * mm, y, line)
        y -= 5 * mm

    # QR
    qr_bytes = qr_png_bytes(verify_url, box_size=6)
    qr_img = ImageReader(io.BytesIO(qr_bytes))
    qr_size = 38 * mm
    qx = width - 22 * mm - qr_size
    qy = height - 28 * mm - qr_size
    c.setFillColorRGB(1, 1, 1)
    c.rect(qx - 3 * mm, qy - 10 * mm, qr_size + 6 * mm, qr_size + 16 * mm, fill=1, stroke=0)
    c.drawImage(qr_img, qx, qy, width=qr_size, height=qr_size, mask="auto")
    c.setFillColorRGB(0.36, 0.42, 0.39)
    c.setFont("Helvetica", 7)
    c.drawCentredString(qx + qr_size / 2, qy - 6 * mm, "Escanea para validar")

    c.setFont("Helvetica", 7)
    c.drawString(22 * mm, 18 * mm, f"Validar: {verify_url}")
    c.setFont("Helvetica-Oblique", 7)
    c.drawRightString(
        width - 22 * mm,
        18 * mm,
        "Documento firmado digitalmente · no altera el contenido",
    )

    c.showPage()
    c.save()
    return buf.getvalue()
