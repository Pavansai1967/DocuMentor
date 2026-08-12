import fitz


def parse_pdf(data: bytes) -> tuple[list[str], int]:
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        page_count = doc.page_count
        page_texts = [page.get_text("text").strip() for page in doc]
        doc.close()
    except Exception as exc:
        raise ValueError("Invalid or empty PDF") from exc
    if page_count == 0:
        raise ValueError("Invalid or empty PDF")
    return page_texts, page_count