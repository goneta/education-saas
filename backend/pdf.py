from textwrap import wrap


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
