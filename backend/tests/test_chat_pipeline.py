import time
from io import BytesIO

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.config import settings
from app.embeddings import get_embedder
from app.main import create_app
from app.mongo_client import MongoStore


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def make_pdf() -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 12)
    lines = [
        "DocuMentor is a retrieval augmented generation application.",
        "It chunks PDF text into tokens of about five hundred with overlap.",
        "Each chunk is embedded with all-MiniLM-L6-v2 into 384 dimensions.",
        "Vector search uses cosine similarity against the question embedding.",
        "The selected document scopes retrieval with a document id filter.",
    ]
    y = 780
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.mark.live
def test_full_chat_flow(client):
    res = client.post("/upload", files={"file": ("sample.pdf", make_pdf(), "application/pdf")})
    assert res.status_code == 200, res.text
    doc_id = res.json()["document_id"]

    for _ in range(120):
        docs = client.get("/documents").json()
        doc = next(d for d in docs if d["id"] == doc_id)
        if doc["status"] != "processing":
            break
        time.sleep(1)
    assert doc["status"] == "ready", doc

    store = MongoStore(settings.mongodb_uri, settings.mongodb_db_name)
    question_vector = get_embedder().encode(["What does DocuMentor do?"])[0]
    for _ in range(60):
        if store.vector_search(ObjectId(doc_id), question_vector, 4):
            break
        time.sleep(1)
    else:
        raise AssertionError("chunks not searchable within 60s")

    with client.stream("POST", "/chat", json={"document_id": doc_id, "question": "What does DocuMentor do?"}) as res:
        assert res.status_code == 200
        body = res.read().decode()
    assert '"type": "sources"' in body
    assert "p." in body or '"page_number"' in body
