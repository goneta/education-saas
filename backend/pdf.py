from textwrap import wrap
from io import BytesIO


def _escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def simple_pdf(title: str, lines: list[str]) -> bytes:
    """Generate a compact single-page PDF using built-in PDF primitives."""
    y = 800
    stream_lines = ["BT", "/F1 18 Tf", f"72 {y} Td", f"({_escape(title)}) Tj"]
    y -= 34
    stream_lines.extend(["/F1 10 Tf"])
    for line in lines:
        for part in wrap(str(line), width=92) or [""]:
            stream_lines.append(f"72 {y} Td")
            stream_lines.append(f"({_escape(part)}) Tj")
            y -= 16
            stream_lines.append(f"-72 {-y} Td")
            if y < 72:
                break
        if y < 72:
            break
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)


def professional_pdf(
    title: str,
    lines: list[str],
    verification_payload: str | None = None,
    subtitle: str | None = None,
    school_header: dict | None = None,
) -> bytes:
    """Generate a branded PDF with a QR image when optional PDF dependencies are installed."""
    try:
        import qrcode
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle
    except Exception:
        fallback = list(lines)
        if verification_payload:
            fallback.append(f"Verification: {verification_payload}")
        return simple_pdf(title, fallback)

    buffer = BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 18 * mm

    page.setFillColor(colors.HexColor("#0F766E"))
    page.rect(0, height - 42 * mm, width, 42 * mm, stroke=0, fill=1)
    text_x = margin
    logo_path = (school_header or {}).get("logo_path")
    if logo_path:
        try:
            page.drawImage(ImageReader(logo_path), margin, height - 35 * mm, 24 * mm, 24 * mm, preserveAspectRatio=True, mask="auto")
            text_x = margin + 30 * mm
        except Exception:
            text_x = margin
    page.setFillColor(colors.white)
    page.setFont("Helvetica-Bold", 11)
    page.drawString(text_x, height - 13 * mm, (school_header or {}).get("name") or "TeducAI")
    page.setFont("Helvetica", 7)
    identity_lines = [
        (school_header or {}).get("address"),
        " | ".join(filter(None, [(school_header or {}).get("phone"), (school_header or {}).get("email")])),
    ]
    identity_y = height - 19 * mm
    for identity in filter(None, identity_lines):
        page.drawString(text_x, identity_y, str(identity)[:105])
        identity_y -= 4 * mm
    page.setFont("Helvetica-Bold", 17)
    page.drawString(text_x, height - 34 * mm, title)
    page.setFont("Helvetica", 8)
    page.drawRightString(width - margin, height - 34 * mm, subtitle or "Document certifie")

    y = height - 54 * mm
    table_data = []
    free_lines = []
    for line in lines:
        if ":" in str(line):
            key, value = str(line).split(":", 1)
            table_data.append([key.strip(), value.strip()])
        else:
            free_lines.append(str(line))

    if table_data:
        table = Table(table_data, colWidths=[46 * mm, 112 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECFDF5")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#065F46")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        table_width, table_height = table.wrapOn(page, width - 2 * margin, y)
        table.drawOn(page, margin, y - table_height)
        y -= table_height + 12 * mm

    page.setFillColor(colors.HexColor("#111827"))
    page.setFont("Helvetica", 10)
    for line in free_lines:
        for part in wrap(line, width=95):
            if y < 42 * mm:
                page.showPage()
                y = height - margin
            page.drawString(margin, y, part)
            y -= 6 * mm

    if verification_payload:
        qr = qrcode.make(verification_payload)
        qr_buffer = BytesIO()
        qr.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        page.drawImage(ImageReader(qr_buffer), width - margin - 32 * mm, 18 * mm, 32 * mm, 32 * mm, mask="auto")
        page.setFont("Helvetica", 7)
        page.setFillColor(colors.HexColor("#475569"))
        page.drawString(margin, 28 * mm, "Verification en ligne via le QR code.")
        page.drawString(margin, 23 * mm, verification_payload[:110])

    page.setStrokeColor(colors.HexColor("#CBD5E1"))
    page.line(margin, 16 * mm, width - margin, 16 * mm)
    page.setFont("Helvetica", 7)
    page.setFillColor(colors.HexColor("#64748B"))
    page.drawString(margin, 10 * mm, "Document genere automatiquement - FCFA/XOF par defaut")
    page.save()
    return buffer.getvalue()
