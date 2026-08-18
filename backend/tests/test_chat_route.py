import json

from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_embedder, get_llm, get_store
from app.routes_chat import router as chat_router


class FakeStore:
    def list_documents(self):
        return [
            {"_id": ObjectId(), "filename": "a.pdf", "status": "ready", "summary": "Test document"},
        ]

    def vector_search(self, document_id, embedding, top_k=4):
        return [
            {"_id": ObjectId(), "document_id": document_id, "page_number": 2, "text": "DocuMentor chunks with overlap."},
            {"_id": ObjectId(), "document_id": document_id, "page_number": 5, "text": "Vector search is cosine."},
        ]


class FakeEmbedder:
    def encode(self, texts, batch_size=32):
        return [[0.1] * 384 for _ in texts]


class FakeLLM:
    async def call(self, model, prompt, system="", temperature=0.2, max_tokens=1024):
        if "plan" in model.lower() or "qwen" in model.lower():
            return json.dumps([{"document_id": str(ObjectId()), "sub_query": "test query"}])
        elif "evaluat" in model.lower() or "gpt-oss-20b" in model.lower():
            return json.dumps({"sufficient": True, "reformulated_query": ""})
        return ""

    async def stream_answer(self, model, prompt, system=""):
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
    with client.stream("POST", "/chat", json={"question": "hi"}) as res:
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/event-stream")
        events = parse_events(res.read().decode())
    types = [e["type"] for e in events]
    assert "token" in types
    assert "trace" in types
    assert types[-1] == "done"
    trace = next(e for e in events if e["type"] == "trace")
    assert len(trace["trace"]) > 0
