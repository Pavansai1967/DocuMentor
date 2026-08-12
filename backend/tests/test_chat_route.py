import json

from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_embedder, get_llm, get_store
from app.routes_chat import router as chat_router


class FakeStore:
    def get_document(self, document_id):
        return {"_id": document_id, "status": "ready", "filename": "a.pdf"}

    def vector_search(self, document_id, embedding, top_k=4):
        return [
            {"page_number": 2, "text": "DocuMentor chunks with overlap."},
            {"page_number": 5, "text": "Vector search is cosine."},
        ]


class FakeEmbedder:
    def encode(self, texts, batch_size=32):
        return [[0.1] * 384 for _ in texts]

    def count_tokens(self, text):
        return len(text.split())


class FakeLLM:
    async def stream_answer(self, prompt):
        for tok in ["Hello", " ", "DocuMentor"]:
            yield tok


def make_app(store=None):
    app = FastAPI()
    app.include_router(chat_router)
    app.dependency_overrides[get_store] = lambda: store or FakeStore()
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_llm] = lambda: FakeLLM()
    return app


def parse_events(text: str) -> list[dict]:
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def test_chat_streams_tokens_then_sources_then_done():
    client = TestClient(make_app())
    with client.stream("POST", "/chat", json={"document_id": str(ObjectId()), "question": "hi"}) as res:
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/event-stream")
        events = parse_events(res.read().decode())
    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-2] == "sources"
    assert types[-1] == "done"
    sources = events[-2]["sources"]
    assert sources[0]["page_number"] == 2


def test_chat_missing_document_returns_404():
    class MissingStore(FakeStore):
        def get_document(self, document_id):
            return None

    res = TestClient(make_app(store=MissingStore())).post(
        "/chat", json={"document_id": str(ObjectId()), "question": "hi"}
    )
    assert res.status_code == 404
