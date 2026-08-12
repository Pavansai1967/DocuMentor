from datetime import datetime, timezone

from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_store
from app.routes_documents import router as documents_router


class FakeStore:
    def list_documents(self):
        now = datetime.now(timezone.utc)
        return [
            {"_id": ObjectId(), "filename": "a.pdf", "upload_date": now,
             "page_count": 3, "status": "ready", "error": None},
            {"_id": ObjectId(), "filename": "b.pdf", "upload_date": now,
             "page_count": 0, "status": "processing", "error": None},
        ]


def test_list_documents():
    app = FastAPI()
    app.include_router(documents_router)
    app.dependency_overrides[get_store] = lambda: FakeStore()
    res = TestClient(app).get("/documents")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) == 2
    assert docs[0]["filename"] == "a.pdf"
    assert docs[0]["id"]
    assert "upload_date" in docs[0]
