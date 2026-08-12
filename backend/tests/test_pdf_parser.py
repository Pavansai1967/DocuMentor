from io import BytesIO

from reportlab.pdfgen import canvas

from app.pdf_parser import parse_pdf


def make_pdf(*page_texts: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    for text in page_texts:
        c.setFont("Helvetica", 12)
        y = 780
        for line in text.splitlines():
            c.drawString(72, y, line)
            y -= 16
        c.showPage()
    c.save()
    return buf.getvalue()


def test_parse_pdf_two_pages():
    data = make_pdf("Hello world one", "Second page line")
    pages, count = parse_pdf(data)
    assert count == 2
    assert len(pages) == 2
    assert all(p.strip() for p in pages)
    assert "one" in pages[0]
    assert "Second page" in pages[1]


def test_parse_pdf_scanned_no_text():
    pages, count = parse_pdf(make_pdf(" "))
    assert count == 1
    assert pages == [""]


def test_parse_pdf_invalid_bytes():
    import pytest

    with pytest.raises(ValueError, match="Invalid or empty PDF"):
        parse_pdf(b"not a pdf at all")