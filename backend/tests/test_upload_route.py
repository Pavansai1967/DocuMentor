from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.deps import get_embedder, get_llm, get_store
from app.routes_upload import router as upload_router


def make_pdf() -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 12)
    c.drawString(72, 780, "DocuMentor is a RAG application for PDFs.")
    c.showPage()
    c.save()
    return buf.getvalue()


class FakeStore:
    def insert_document(self, filename):
        from bson import ObjectId

        return ObjectId()

    def insert_chunks(self, rows):
        assert rows
        assert len(rows[0]["embedding"]) == 384

    def mark_document_ready(self, document_id, page_count, summary=None):
        pass

    def mark_document_failed(self, document_id, error):
        raise AssertionError(f"unexpected failure: {error}")


class FakeEmbedder:
    def count_tokens(self, text):
        return len(text.split())

    def encode(self, texts, batch_size=32):
        return [[0.1] * 384 for _ in texts]


class FakeLLM:
    async def call(self, model, prompt, system="", temperature=0.2, max_tokens=1024):
        return "This is a test document summary."


def make_app():
    app = FastAPI()
    app.include_router(upload_router)
    app.dependency_overrides[get_store] = lambda: FakeStore()
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_llm] = lambda: FakeLLM()
    return app


def test_upload_rejects_non_pdf():
    res = TestClient(make_app()).post("/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert res.status_code in (400, 422)


def test_upload_valid_pdf():
    res = TestClient(make_app()).post(
        "/upload", files={"file": ("a.pdf", make_pdf(), "application/pdf")}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "processing"
    assert body["document_id"]
